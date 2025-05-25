from flask import Flask, render_template, request, jsonify
from db_query import query_database
import re

app = Flask(__name__)

def extract_logs_and_result(full_response):
    if "> Finished chain." in full_response:
        logs = full_response.split("> Finished chain.")[0].strip()
        result = full_response.split("Result:")[1].strip() if "Result:" in full_response else ""
        return logs, result
    return "", full_response

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    logs = None
    
    if request.method == 'POST':
        question = request.form.get('question', '')
        time_input = request.form.get('time_input', '')
        
        if not time_input:
            time_input = None
            
        full_response = query_database(question, time_input)
        logs, result = extract_logs_and_result(full_response)
        
    return render_template('index.html', result=result, logs=logs)

@app.route('/api/query', methods=['POST'])
def api_query():
    data = request.json
    question = data.get('question', '')
    time_input = data.get('time_input')
    
    full_response = query_database(question, time_input)
    logs, result = extract_logs_and_result(full_response)
    
    return jsonify({
        'result': result,
        'logs': logs
    })

if __name__ == '__main__':
    app.run(debug=True)

