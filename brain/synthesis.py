import sqlite3
from typing import List, Dict
from brain.db import DB_PATH

def get_recent_context(limit: int = 20) -> List[Dict]:
    """
    Fetches the most recent events from the Specter memory.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, event_type, source, content, project_dir 
            FROM events 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert sqlite3.Row to dictionaries and reverse so it reads chronologically
        events = [dict(row) for row in rows]
        events.reverse()
        return events
    except Exception as e:
        print(f"[SYNTHESIS ERROR] Failed to fetch context: {e}")
        return []

def detect_friction(events: List[Dict]) -> Dict:
    """
    A basic rule-based engine to detect user friction from recent events.
    """
    friction_report = {
        "friction_detected": False,
        "reason": None,
        "relevant_events": []
    }
    
    if not events:
        return friction_report
        
    # Rule 1: Repeated identical commands (e.g. running 'npm install' multiple times)
    commands = [e for e in events if e['event_type'] == 'CMD_EXECUTED']
    if len(commands) >= 3:
        last_three = commands[-3:]
        # Check if the content of the last 3 commands is identical
        if last_three[0]['content'] == last_three[1]['content'] == last_three[2]['content']:
            friction_report["friction_detected"] = True
            friction_report["reason"] = f"User has repeatedly executed '{last_three[0]['content']}' 3 times."
            friction_report["relevant_events"] = last_three
            return friction_report

    # Future Rules: Detect 'error' string in stderr (once implemented), etc.
    
    return friction_report

def search_events(query: str, limit: int = 50) -> List[Dict]:
    """
    Searches the database for events matching the query.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT timestamp, event_type, source, content, project_dir 
            FROM events 
            WHERE source LIKE ? OR content LIKE ?
            ORDER BY id DESC 
            LIMIT ?
        ''', (search_term, search_term, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = [dict(row) for row in rows]
        return events
    except Exception as e:
        print(f"[SYNTHESIS ERROR] Failed to search events: {e}")
        return []

def analyze_today_stats() -> Dict:
    """
    Analyzes today's events to provide statistics.
    """
    from datetime import datetime, timezone, timedelta
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get today's start in UTC (since we log in UTC)
        today_date = datetime.utcnow().date().isoformat()
        
        cursor.execute('''
            SELECT timestamp, event_type, source, content 
            FROM events 
            WHERE timestamp LIKE ?
            ORDER BY timestamp ASC
        ''', (f"{today_date}%",))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {
            "total_events": len(rows),
            "idle_count": 0,
            "top_apps": {},
            "top_files": {}
        }
        
        for row in rows:
            etype = row['event_type']
            source = row['source']
            
            if etype == 'IDLE_START':
                stats['idle_count'] += 1
            elif etype == 'WINDOW_ACTIVE':
                stats['top_apps'][source] = stats['top_apps'].get(source, 0) + 1
            elif etype in ('FILE_MODIFIED', 'FILE_CREATED'):
                stats['top_files'][source] = stats['top_files'].get(source, 0) + 1
                
        # Sort apps and files
        stats['top_apps'] = dict(sorted(stats['top_apps'].items(), key=lambda item: item[1], reverse=True)[:5])
        stats['top_files'] = dict(sorted(stats['top_files'].items(), key=lambda item: item[1], reverse=True)[:5])
        
        return stats
    except Exception as e:
        print(f"[SYNTHESIS ERROR] Failed to analyze stats: {e}")
        return {}

def get_ai_chats() -> List[Dict]:
    """
    Groups AI_CHAT_CONTENT events into discrete conversations.
    """
    from datetime import datetime
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Order by timestamp ASC to reconstruct the session
        cursor.execute('''
            SELECT id, timestamp, source, content 
            FROM events 
            WHERE event_type = 'AI_CHAT_CONTENT'
            ORDER BY timestamp ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        chats = []
        if not rows:
            return chats
            
        current_chat = None
        
        for row in rows:
            timestamp_str = row['timestamp']
            source = row['source']
            content = row['content']
            
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            try:
                dt = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue
                
            if current_chat is None:
                current_chat = {
                    "id": row['id'],
                    "source": source,
                    "content": content,
                    "start_time": dt,
                    "last_time": dt,
                    "topic": "New Conversation"
                }
            else:
                # Check if it belongs to the same chat
                time_diff = (dt - current_chat['last_time']).total_seconds()
                
                if source == current_chat['source'] and time_diff <= 1800: # 30 mins
                    # Update with the newest content and time
                    current_chat['content'] = content
                    current_chat['last_time'] = dt
                else:
                    # Save the current chat and start a new one
                    chats.append(current_chat)
                    current_chat = {
                        "id": row['id'],
                        "source": source,
                        "content": content,
                        "start_time": dt,
                        "last_time": dt,
                        "topic": "New Conversation"
                    }
                    
        if current_chat:
            chats.append(current_chat)
            
        # Post-process to extract topics and format times
        for chat in chats:
            lines = chat['content'].split('\n')
            topic = "AI Conversation"
            for i, line in enumerate(lines):
                if line.strip() == "[USER]" and i + 1 < len(lines):
                    for j in range(i+1, len(lines)):
                        potential_topic = lines[j].strip()
                        if potential_topic and not potential_topic.startswith('['):
                            topic = (potential_topic[:50] + '...') if len(potential_topic) > 50 else potential_topic
                            break
                    break
            
            chat['topic'] = topic
            chat['start_time'] = chat['start_time'].isoformat() + "Z"
            chat['last_time'] = chat['last_time'].isoformat() + "Z"
            
        # Reverse to show newest chats first
        chats.reverse()
        return chats
        
    except Exception as e:
        print(f"[SYNTHESIS ERROR] Failed to fetch AI chats: {e}")
        return []
