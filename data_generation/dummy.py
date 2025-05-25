import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker


fake = Faker()


db_path = "transcripts.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


cursor.execute("DROP TABLE IF EXISTS call_metrics;")
cursor.execute("DROP TABLE IF EXISTS calls;")


cursor.execute("""
CREATE TABLE calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    customer_name TEXT,
    agent_name TEXT,
    issue TEXT NOT NULL,
    request_type TEXT NOT NULL,
    transcription TEXT NOT NULL,
    outcome TEXT NOT NULL
);
""")


cursor.execute("""
CREATE TABLE call_metrics (
    call_id INTEGER PRIMARY KEY,
    duration_seconds INTEGER NOT NULL,
    was_forwarded BOOLEAN NOT NULL,
    wait_time_seconds INTEGER NOT NULL,
    issue_resolved BOOLEAN NOT NULL,
    customer_sentiment TEXT,
    agent_efficiency_rating INTEGER,
    escalation_level TEXT,
    agent_politeness_score INTEGER,
    FOREIGN KEY(call_id) REFERENCES calls(id)
);
""")


transcripts = [
    "Customer: Hi, I'm calling because my credit card payment failed even though I have enough balance. "
    "Agent: I understand. Let me check your account. It seems like there was a system error. I've fixed it now. "
    "Customer: Thank you so much. "
    "Agent: You're welcome. Is there anything else I can help with? "
    "Customer: No, that's all.",

    "Customer: Hello, I was double charged for a transaction yesterday. "
    "Agent: I'm sorry to hear that. Let me check your transaction history. Yes, I see the duplicate. I'll initiate a refund. "
    "Customer: Great, how long will it take? "
    "Agent: Usually 3-5 business days. "
    "Customer: Okay, thank you.",

    "Customer: Hi, I can’t log into my mobile banking app. "
    "Agent: Let’s reset your password. I’ll guide you through it. "
    "Customer: Alright, I'm on the login screen now. "
    "Agent: Please click on 'Forgot Password' and follow the prompts. "
    "Customer: Done. It worked! Thanks. "
    "Agent: Glad to help!",

    "Customer: I made a payment but it hasn’t reflected in my account. "
    "Agent: I apologize. Let me verify. Yes, the payment is delayed due to a backend process. "
    "Customer: Will it be posted today? "
    "Agent: It should reflect within the next few hours. "
    "Customer: Okay, thanks for the update.",

    "Customer: Hello, I want to cancel a transaction I just made. "
    "Agent: May I know the transaction ID? "
    "Customer: It's 893745. "
    "Agent: Unfortunately, it's already processed. I recommend contacting the merchant. "
    "Customer: Alright, thanks for the help anyway."
]

issues = ["Payment Issue", "Technical Issue", "Credit Card Issue", "Account Access", "Billing Error"]
request_types = ["Complaint", "Inquiry", "Request"]
outcomes = ["Success", "Fail", "Escalated", "Dropped"]

start_date = datetime.now() - timedelta(days=60)
num_calls = 240

for _ in range(num_calls):
    call_time = start_date + timedelta(
        days=random.randint(0, 59),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    customer_name = fake.name()
    agent_name = fake.name()
    issue = random.choice(issues)
    request_type = random.choice(request_types)
    transcription = random.choice(transcripts)
    outcome = random.choice(outcomes)

    cursor.execute("""
    INSERT INTO calls (timestamp, customer_name, agent_name, issue, request_type, transcription, outcome)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (call_time.strftime("%Y-%m-%d %H:%M:%S"), customer_name, agent_name, issue, request_type, transcription, outcome))

conn.commit()
conn.close()

db_path

