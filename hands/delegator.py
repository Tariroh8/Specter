import os
import sys
import subprocess
import threading
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from brain.db import create_task, update_task_status, get_tasks

# A dictionary to store running subprocesses if we need to interact with them in the same session
_running_processes = {}

def _read_output(process, task_id):
    """Reads stdout from a process and waits for it to finish."""
    try:
        for line in iter(process.stdout.readline, b''):
            if line:
                # In the future, we could log the output to a file or DB here.
                pass
        process.stdout.close()
        process.wait()
        
        # When done, update the status
        status = 'completed' if process.returncode == 0 else 'failed'
        update_task_status(task_id, status)
        
        if task_id in _running_processes:
            del _running_processes[task_id]
            
    except Exception as e:
        print(f"[Delegator ERROR] Failed reading output for task {task_id}: {e}")
        update_task_status(task_id, 'failed')

def start_task(name: str, command: str):
    """
    Spawns a new background process for the given command.
    """
    try:
        print(f"[*] Delegating task '{name}': {command}")
        
        # Create a DB entry first to get the ID
        task_id = create_task(name, command)
        if task_id == -1:
            return None
            
        # Start the process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Update the task with the actual PID
        update_task_status(task_id, 'running', pid=process.pid)
        _running_processes[task_id] = process
        
        # Start a background thread to read output and wait for completion
        thread = threading.Thread(target=_read_output, args=(process, task_id), daemon=True)
        thread.start()
        
        print(f"[+] Task '{name}' started with PID {process.pid} (Task ID: {task_id})")
        return task_id
        
    except Exception as e:
        print(f"[-] Failed to start task '{name}': {e}")
        return None

def stop_task(task_id: int):
    """
    Attempts to stop a running task.
    """
    try:
        # Check if we have the process object in memory
        if task_id in _running_processes:
            process = _running_processes[task_id]
            process.terminate()
            update_task_status(task_id, 'stopped')
            del _running_processes[task_id]
            print(f"[+] Task {task_id} terminated.")
            return True
            
        # If not in memory, we might need to kill by PID (if this is a new CLI run)
        tasks = get_tasks()
        task = next((t for t in tasks if t['id'] == task_id), None)
        
        if not task:
            print(f"[-] Task {task_id} not found.")
            return False
            
        if task['status'] != 'running' or not task['pid']:
            print(f"[-] Task {task_id} is not running.")
            return False
            
        # Try to kill it via OS
        if os.name == 'nt':
            os.system(f"taskkill /F /PID {task['pid']}")
        else:
            os.system(f"kill -9 {task['pid']}")
            
        update_task_status(task_id, 'stopped')
        print(f"[+] Task {task_id} (PID {task['pid']}) stopped via OS signal.")
        return True
        
    except Exception as e:
        print(f"[-] Failed to stop task {task_id}: {e}")
        return False

def check_running_tasks():
    """
    A utility to check if tasks marked as running in the DB are actually still running.
    Updates them to completed if they are no longer active.
    """
    tasks = get_tasks(status='running')
    for task in tasks:
        pid = task['pid']
        if not pid:
            continue
            
        is_running = False
        try:
            if os.name == 'nt':
                output = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /NH', shell=True, text=True)
                is_running = str(pid) in output
            else:
                os.kill(pid, 0)
                is_running = True
        except Exception:
            is_running = False
            
        if not is_running:
            update_task_status(task['id'], 'completed')
