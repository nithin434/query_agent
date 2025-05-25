from flask import Flask, render_template, request, jsonify, session
from db_query import query_database
import re
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'penguin_production' 

conversation_history = {}

def extract_logs_and_result(full_response):
    if "> Finished chain." in full_response:
        logs = full_response.split("> Finished chain.")[0].strip()
        result = full_response.split("Result:")[1].strip() if "Result:" in full_response else ""
        return logs, result
    return "", full_response

@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversation_history[session['session_id']] = []
    
    # Get conversation history for this session
    history = conversation_history.get(session['session_id'], [])
    
    return render_template('chat.html', history=history)

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    question = data.get('question', '')
    date_range = data.get('date_range', {})
    
    time_input = None
    if date_range and date_range.get('start') and date_range.get('end'):
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        time_input = f"between {start_date} and {end_date}"
    
    session_id = session.get('session_id', str(uuid.uuid4()))
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append({
        'type': 'user',
        'message': question,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
    
    if time_input:
        conversation_history[session_id].append({
            'type': 'system',
            'message': f"Searching within date range: {time_input}",
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
    
    full_response = query_database(question, time_input)
    logs, result = extract_logs_and_result(full_response)
    
    conversation_history[session_id].append({
        'type': 'assistant',
        'message': result,
        'logs': logs,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })
    
    return jsonify({
        'result': result,
        'logs': logs,
        'history': conversation_history[session_id]
    })

@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('session_id')
    if session_id in conversation_history:
        conversation_history[session_id] = []
    
    return jsonify({'status': 'success'})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
