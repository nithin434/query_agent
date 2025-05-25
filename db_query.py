import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.sql_database import SQLDatabase
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
import io
import sys
from contextlib import redirect_stdout

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

def connect_to_database(db_path: str = "transcripts.db") -> SQLDatabase:
    db_uri = f"sqlite:///{db_path}"
    return SQLDatabase.from_uri(db_uri)

def create_llm():
    return GoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.1,
        verbose=True,
        max_tokens=4096,
    )

class CleanedQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    def _run(self, query: str) -> str:
        if query.startswith("```sql"):
            query = query.replace("```sql", "", 1)
            if query.endswith("```"):
                query = query[:-3]
        elif query.startswith("```"):
            query = query.replace("```", "", 1)
            if query.endswith("```"):
                query = query[:-3]
        
        query = query.strip()
        
        try:
            return self.db.run(query)
        except Exception as e:
            return f"Error: {str(e)}"
        
class CleanedSQLDatabaseToolkit(SQLDatabaseToolkit):
    def get_tools(self):
        tools = super().get_tools()
        for i, tool in enumerate(tools):
            if isinstance(tool, QuerySQLDatabaseTool):
                tools[i] = CleanedQuerySQLDatabaseTool(db=self.db, llm=self.llm)
        return tools

def create_agent(db: SQLDatabase, llm):
    toolkit = CleanedSQLDatabaseToolkit(db=db, llm=llm)

    custom_prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct SQL query to run, execute it, and return the results.
You have access to tools for interacting with the database.
DO NOT include markdown formatting in your SQL queries.
DO NOT include backticks in your SQL queries.
DO NOT write any explanations, only return the query and query results.

The database has the following tables:
- calls: Contains information about phone calls including timestamp, customer_name, agent_name, issue, etc.
- call_metrics: Contains metrics about calls like sentiment_score, silence_percentage, etc.
- sales: Contains information about sales made during calls including product_type, sale_success, etc.

Here are some example queries:
1. To get total successful sales by product: SELECT product_type, COUNT(*) FROM sales WHERE sale_success = 1 GROUP BY product_type;
2. To get average call duration: SELECT AVG(duration) FROM calls;

"""
    
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        prefix=custom_prefix
    )

def parse_time_constraints(time_input: str) -> Dict[str, Any]:

    time_constraints = {}
    
    try:
        if "last" in time_input.lower() and "days" in time_input.lower():
            days = int(time_input.lower().split("last")[1].split("days")[0].strip())
            time_constraints["type"] = "last_n_days"
            time_constraints["days"] = days
        elif "between" in time_input.lower() and "and" in time_input.lower():
            parts = time_input.lower().split("between")[1].split("and")
            start_date_str = parts[0].strip()
            end_date_str = parts[1].strip()

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            time_constraints["type"] = "date_range"
            time_constraints["start_date"] = start_date
            time_constraints["end_date"] = end_date
        else:

            time_constraints["type"] = "raw"
            time_constraints["raw_input"] = time_input
            
    except Exception as e:
        print(f"Error parsing time constraints: {e}")
        time_constraints["type"] = "raw"
        time_constraints["raw_input"] = time_input
        
    return time_constraints

def format_query_with_time(question: str, time_constraints: Dict[str, Any]) -> str:

    context = """
    Database schema:
    - calls: id, customer_id, timestamp, duration, call_type, agent_id
    - call_metrics: id, call_id, sentiment_score, silence_percentage, customer_talk_time, agent_talk_time, interruptions
    - sales: call_id, product_type, product_subtype, sale_success, payment_method, convinced_with_rep, verification_done, knows_autopay_requirement
    """
    
    if time_constraints["type"] == "last_n_days":
        context += f"\nPlease limit your search to calls within the last {time_constraints['days']} days."
    elif time_constraints["type"] == "date_range":
        start_date = time_constraints["start_date"].strftime("%Y-%m-%d")
        end_date = time_constraints["end_date"].strftime("%Y-%m-%d")
        context += f"\nPlease limit your search to calls between {start_date} and {end_date}."
    elif time_constraints["type"] == "raw":
        context += f"\nTime constraint: {time_constraints['raw_input']}"
    

    formatted_query = f"{context}\n\nUser question: {question}"
    return formatted_query

def query_database(question: str, time_input: Optional[str] = None) -> str:

    db = connect_to_database()
    llm = create_llm()
    agent = create_agent(db, llm)
    time_constraints = parse_time_constraints(time_input) if time_input else {"type": "none"}
    formatted_query = format_query_with_time(question, time_constraints)
    
    # Capture stdout to get the agent's thought process
    captured_output = io.StringIO()
    try:
        with redirect_stdout(captured_output):
            response = agent.invoke({"input": formatted_query})
            result = response['output']
            
        # Format the captured output and result
        logs = captured_output.getvalue()
        full_response = f"{logs}\n\n> Finished chain.\n\nResult:\n{result}"
        return full_response
    except Exception as e:
        error_msg = f"Error querying database: {str(e)}"
        return f"{captured_output.getvalue()}\n\nError: {error_msg}"



'''
Examples for time
    - "last 7 days"
    - "between 2023-01-01 and 2023-01-31"
    - "after 3pm on 2023-01-15"
  
    "What are the top 5 products sold successfully?"
    "What's the average call duration for successful sales?"
    "How many calls resulted in sales of DirecTV Satellite?"
    "What percentage of calls with high sentiment scores resulted in a sale?
    
   question: The natural language question to ask
        time_input: Optional time constraint (e.g., "last 7 days", "between 2023-01-01 and 2023-01-31")
'''
