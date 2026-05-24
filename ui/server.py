import os
import sys
from flask import Flask, render_template, jsonify, request

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain.synthesis import get_recent_context, search_events, analyze_today_stats, get_ai_chats
from brain.config import load_config, save_config
from brain.db import log_event, get_tasks
from hands.delegator import check_running_tasks, stop_task
from hands.skills import get_all_skills_metadata, get_skill

app = Flask(__name__)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events', methods=['GET'])
def api_events():
    limit = request.args.get('limit', default=50, type=int)
    events = get_recent_context(limit=limit)
    return jsonify(events)

@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', default='', type=str)
    limit = request.args.get('limit', default=50, type=int)
    if query:
        events = search_events(query, limit=limit)
    else:
        events = get_recent_context(limit=limit)
    return jsonify(events)

@app.route('/api/stats', methods=['GET'])
def api_stats():
    stats = analyze_today_stats()
    return jsonify(stats)

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.json
        if data is not None:
            current_config = load_config()
            current_config.update(data)
            save_config(current_config)
            return jsonify({"status": "success", "config": current_config})
        return jsonify({"status": "error", "message": "Invalid data"}), 400
    else:
        return jsonify(load_config())

@app.route('/api/extension/chat', methods=['POST', 'OPTIONS'])
def api_extension_chat():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    data = request.json
    if not data or 'source' not in data or 'content' not in data:
        return jsonify({"status": "error", "message": "Missing source or content"}), 400
    
    source = data['source']
    content = data['content']
    
    # Log the full chat content
    log_event("AI_CHAT_CONTENT", source, content)
    return jsonify({"status": "success"}), 200

@app.route('/api/tasks', methods=['GET'])
def api_tasks():
    check_running_tasks()
    tasks = get_tasks()
    return jsonify(tasks)

@app.route('/api/chats', methods=['GET'])
def api_chats():
    chats = get_ai_chats()
    return jsonify(chats)

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
def api_stop_task(task_id):
    success = stop_task(task_id)
    if success:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Failed to stop task"}), 400

@app.route('/api/skills', methods=['GET'])
def api_skills():
    return jsonify(get_all_skills_metadata())

@app.route('/api/skills/<skill_name>/run', methods=['POST'])
def api_run_skill(skill_name):
    skill_class = get_skill(skill_name)
    if not skill_class:
        return jsonify({"success": False, "message": "Skill not found"}), 404
    
    data = request.json or {}
    try:
        skill_instance = skill_class()
        result = skill_instance.execute(**data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    print("=== SPECTER DASHBOARD ===")
    print("[*] Starting local server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
