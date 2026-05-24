import os
import sys
import argparse

# Add project root to path so we can import 'brain' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from brain.synthesis import get_recent_context, detect_friction, search_events, analyze_today_stats
from brain.config import set_setting

def mock_ai_analysis(context, friction_report):
    """
    Mocks an AI response based on the provided context.
    """
    print("\n" + "="*50)
    print("🤖 SPECTER AI ANALYSIS (MOCK VERSION)")
    print("="*50)
    
    if friction_report.get("friction_detected"):
        print(f"\n[!] FRICTION DETECTED: {friction_report['reason']}")
        print("-> MOCK ADVICE: It looks like this command keeps failing or you are retrying it. Have you checked if you are in the correct directory, or if you need to install a missing dependency?")
    else:
        print("\n[+] No obvious friction detected in recent actions.")
        print("-> MOCK ADVICE: You seem to be making steady progress. Let me know if you need help with a specific bug!")
        
    print("\n[Recent Context Provided to AI]")
    for idx, event in enumerate(context[-5:]): # Just show last 5 for brevity
        content = event['content'] or event['source']
        print(f"  {idx+1}. [{event['event_type']}] {content}")
    print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Specter Agent CLI - The 'Hands'")
    parser.add_argument("--status", action="store_true", help="Get a summary of your current context")
    parser.add_argument("--debug", action="store_true", help="Analyze recent history for friction/errors using AI")
    parser.add_argument("--set-api-key", type=str, help="Save your AI provider API key")
    parser.add_argument("--set-model", type=str, help="Set your AI model preference (e.g. gemini, ollama)")
    parser.add_argument("--tag", type=str, help="Add a manual bookmark/tag to your timeline")
    parser.add_argument("--search", type=str, help="Search the Specter timeline")
    parser.add_argument("--summary", action="store_true", help="Print today's summary statistics")
    
    # Delegation Engine Arguments
    parser.add_argument("--delegate", nargs=2, metavar=('NAME', 'COMMAND'), help="Delegate a background task to Specter")
    parser.add_argument("--tasks", action="store_true", help="List all delegated tasks and their status")
    parser.add_argument("--stop", type=int, metavar='TASK_ID', help="Stop a running delegated task")
    
    # Action Engine / Skills Arguments
    parser.add_argument("--list-skills", action="store_true", help="List all available skills")
    parser.add_argument("--run-skill", type=str, metavar='SKILL_NAME', help="Run a specific skill by name")
    parser.add_argument("--args", type=str, help="Comma-separated key=value arguments for the skill (e.g. type=python,name=my_app)")
    
    args = parser.parse_args()
    
    if args.set_api_key is not None:
        set_setting("api_key", args.set_api_key)
        print(f"[+] API Key saved to Specter config.")
        return

    if args.set_model is not None:
        set_setting("model_provider", args.set_model)
        print(f"[+] Model provider set to: {args.set_model}")
        return
        
    if args.tag is not None:
        from brain.db import log_event
        log_event(event_type="USER_TAG", source="agent_cli", content=args.tag)
        print(f"[+] Tag added to Specter Memory: {args.tag}")
        return
        
    if args.summary:
        print("\n=== TODAY'S SPECTER SUMMARY ===")
        stats = analyze_today_stats()
        print(f"Total Events Logged: {stats.get('total_events', 0)}")
        print(f"Times Gone Idle: {stats.get('idle_count', 0)}")
        print("\nTop Apps Used:")
        for app, count in stats.get('top_apps', {}).items():
            print(f"  - {app}: {count} interactions")
        print("\nTop Files Touched:")
        for file, count in stats.get('top_files', {}).items():
            print(f"  - {file}: {count} events")
        return

    if args.search:
        print(f"[*] Searching memory for: '{args.search}'")
        results = search_events(args.search)
        if not results:
            print("[-] No results found.")
            return
        print(f"[+] Found {len(results)} results:")
        for event in results:
            time_str = event['timestamp'].split('.')[0].replace('T', ' ')
            content = event['content'] or event['source']
            print(f" - [{time_str}] {event['event_type']}: {content}")
        return

    if args.delegate:
        name, command = args.delegate
        from hands.delegator import start_task
        start_task(name, command)
        return
        
    if args.tasks:
        from hands.delegator import check_running_tasks
        check_running_tasks()
        
        from brain.db import get_tasks
        tasks = get_tasks()
        if not tasks:
            print("[-] No tasks found.")
            return
        print("\n=== DELEGATED TASKS ===")
        for t in tasks:
            pid_str = f"(PID: {t['pid']})" if t['pid'] else ""
            print(f"[{t['id']}] {t['name']} - Status: {t['status']} {pid_str}")
            print(f"    Command: {t['command']}")
            if t['completed_at']:
                print(f"    Completed: {t['completed_at']}")
        print("=======================\n")
        return
        
    if args.stop is not None:
        from hands.delegator import stop_task
        stop_task(args.stop)
        return

    if args.list_skills:
        from hands.skills import get_all_skills_metadata
        skills = get_all_skills_metadata()
        print("\n=== AVAILABLE SKILLS ===")
        for name, meta in skills.items():
            print(f"[*] {name}: {meta['description']}")
            if meta['parameters']:
                print("    Parameters:")
                for param, desc in meta['parameters'].items():
                    print(f"      - {param}: {desc}")
        print("========================\n")
        return

    if args.run_skill:
        from hands.skills import get_skill
        skill_class = get_skill(args.run_skill)
        if not skill_class:
            print(f"[-] Skill '{args.run_skill}' not found.")
            return
            
        kwargs = {}
        if args.args:
            try:
                pairs = args.args.split(',')
                for pair in pairs:
                    k, v = pair.split('=', 1)
                    kwargs[k.strip()] = v.strip()
            except ValueError:
                print("[-] Invalid --args format. Use key=value,key2=value2")
                return
                
        print(f"[*] Executing skill '{args.run_skill}' with args: {kwargs}")
        skill_instance = skill_class()
        result = skill_instance.execute(**kwargs)
        
        if result.get("success"):
            print(f"[+] Success: {result.get('message')}")
        else:
            print(f"[-] Failed: {result.get('message')}")
        return

    if not (args.status or args.debug):
        parser.print_help()
        return

    print("[*] Fetching recent memory from the Brain...")
    context = get_recent_context(limit=20)
    
    if not context:
        print("[-] No recent context found. Is the Observer running?")
        return
        
    if args.status:
        print("\n=== SPECTER STATUS ===")
        print(f"Total events analyzed: {len(context)}")
        print("Your last 3 actions:")
        for event in context[-3:]:
            # Clean up timestamp for readability
            time_str = event['timestamp'].split('.')[0].replace('T', ' ')
            content = event['content'] or event['source']
            print(f" - [{time_str}] {event['event_type']}: {content}")
            
    if args.debug:
        friction_report = detect_friction(context)
        mock_ai_analysis(context, friction_report)

if __name__ == "__main__":
    main()
