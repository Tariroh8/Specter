import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Define the user-specific data directory for Specter
APP_DATA_DIR = Path(os.path.expandvars(r"%APPDATA%\Specter"))
DB_PATH = APP_DATA_DIR / "specter.db"

def init_db():
    """Initializes the database and creates the necessary tables if they don't exist."""
    # Ensure the directory exists
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT,
            project_dir TEXT
        )
    ''')
    
    # Create the tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            command TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            pid INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

def log_event(event_type: str, source: str, content: str = "", project_dir: str = ""):
    """
    Logs an event to the database.
    
    :param event_type: e.g., 'CMD_EXECUTED', 'FILE_MODIFIED', 'FILE_CREATED'
    :param source: The file path or the terminal name
    :param content: The command string or any file diff/content
    :param project_dir: The root directory of the active project
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Use UTC for standard logging
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO events (timestamp, event_type, source, content, project_dir)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, event_type, source, content, project_dir))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Failed to log event: {e}")

# Initialize the DB when this module is imported
init_db()

def create_task(name: str, command: str, pid: int = None) -> int:
    """Creates a new task in the database and returns its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (name, command, status, pid)
            VALUES (?, ?, ?, ?)
        ''', (name, command, 'running' if pid else 'pending', pid))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    except Exception as e:
        print(f"[DB ERROR] Failed to create task: {e}")
        return -1

def update_task_status(task_id: int, status: str, pid: int = None):
    """Updates the status (and optionally PID) of an existing task."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if status in ('completed', 'failed', 'stopped'):
            completed_at = datetime.utcnow().isoformat()
            if pid is not None:
                cursor.execute('''
                    UPDATE tasks SET status = ?, pid = ?, completed_at = ? WHERE id = ?
                ''', (status, pid, completed_at, task_id))
            else:
                cursor.execute('''
                    UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
                ''', (status, completed_at, task_id))
        else:
            if pid is not None:
                cursor.execute('UPDATE tasks SET status = ?, pid = ? WHERE id = ?', (status, pid, task_id))
            else:
                cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Failed to update task: {e}")

def get_tasks(status: str = None):
    """Retrieves tasks from the database, optionally filtered by status."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
            
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    except Exception as e:
        print(f"[DB ERROR] Failed to get tasks: {e}")
        return []
