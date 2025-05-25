import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_call_transcript(call_id):
    conn = sqlite3.connect("transcripts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, transcription FROM calls WHERE id = ?", (call_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

def get_call_ids(start_id=None, end_id=None):
    conn = sqlite3.connect("transcripts.db")
    cursor = conn.cursor()
    
    if start_id and end_id:
        cursor.execute("SELECT id FROM calls WHERE id BETWEEN ? AND ?", (start_id, end_id))
    else:
        cursor.execute("SELECT id FROM calls")
    
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

def analyze_transcript_with_gemini(transcript):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Analyze the following customer service call transcript and extract these metrics:
    1. Call duration in seconds (estimate based on conversation length)
    2. Whether the call was forwarded (true/false)
    3. Wait time in seconds (estimate if mentioned)
    4. Whether the issue was resolved (true/false)
    5. Customer sentiment (positive, neutral, negative)
    6. Agent efficiency rating (1-10)
    7. Escalation level (none, supervisor, manager)
    8. Agent politeness score (1-10)
    
    Return only a JSON object with these fields:
    {{
        "duration_seconds": int,
        "was_forwarded": bool,
        "wait_time_seconds": int,
        "issue_resolved": bool,
        "customer_sentiment": str,
        "agent_efficiency_rating": int,
        "escalation_level": str,
        "agent_politeness_score": int
    }}
    
    Transcript:
    {transcript}
    """
    
    response = model.generate_content(prompt)
    
    try:
        response_text = response.text
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()
        
        import json
        metrics = json.loads(json_str)
        return metrics
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        return {
            "duration_seconds": 120,
            "was_forwarded": False,
            "wait_time_seconds": 30,
            "issue_resolved": True,
            "customer_sentiment": "neutral",
            "agent_efficiency_rating": 5,
            "escalation_level": "none",
            "agent_politeness_score": 5
        }

def update_call_metrics(call_id, metrics):
    conn = sqlite3.connect("transcripts.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT call_id FROM call_metrics WHERE call_id = ?", (call_id,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("""
        UPDATE call_metrics SET 
            duration_seconds = ?,
            was_forwarded = ?,
            wait_time_seconds = ?,
            issue_resolved = ?,
            customer_sentiment = ?,
            agent_efficiency_rating = ?,
            escalation_level = ?,
            agent_politeness_score = ?
        WHERE call_id = ?
        """, (
            metrics["duration_seconds"],
            metrics["was_forwarded"],
            metrics["wait_time_seconds"],
            metrics["issue_resolved"],
            metrics["customer_sentiment"],
            metrics["agent_efficiency_rating"],
            metrics["escalation_level"],
            metrics["agent_politeness_score"],
            call_id
        ))
    else:
        cursor.execute("""
        INSERT INTO call_metrics (
            call_id,
            duration_seconds,
            was_forwarded,
            wait_time_seconds,
            issue_resolved,
            customer_sentiment,
            agent_efficiency_rating,
            escalation_level,
            agent_politeness_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            metrics["duration_seconds"],
            metrics["was_forwarded"],
            metrics["wait_time_seconds"],
            metrics["issue_resolved"],
            metrics["customer_sentiment"],
            metrics["agent_efficiency_rating"],
            metrics["escalation_level"],
            metrics["agent_politeness_score"]
        ))
    
    conn.commit()
    conn.close()

def process_calls(start_id=None, end_id=None, single_id=None):
    if single_id:
        call_ids = [single_id]
    else:
        call_ids = get_call_ids(start_id, end_id)
    
    print(f"Processing {len(call_ids)} call(s)...")
    
    for call_id in call_ids:
        call_id, transcript = get_call_transcript(call_id)
        if not transcript:
            print(f"No transcript found for call ID {call_id}")
            continue
            
        print(f"Analyzing call ID {call_id}...")
        metrics = analyze_transcript_with_gemini(transcript)
        update_call_metrics(call_id, metrics)
        print(f"Call ID {call_id} processed successfully.")
    
    print("Processing complete!")

if __name__ == "__main__":

        # process_calls(single_id=2)

        process_calls(start_id=30, end_id=50)

        #process_calls()

