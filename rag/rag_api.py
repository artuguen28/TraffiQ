import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Environment variables
db_url = os.getenv("DATABASE_URL")
model_name = os.getenv("MODEL_NAME", "gpt-4")
openai_key = os.getenv("OPENAI_API_KEY")

# Validate environment variables
if not openai_key:
    raise ValueError("OPENAI_API_KEY environment variable must be set")
if not db_url:
    raise ValueError("DATABASE_URL environment variable must be set")

client = OpenAI(api_key=openai_key)

# Database schema for context
DB_SCHEMA = """
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'CAM_01', 'CAM_02'
    video_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    frame_width INTEGER NOT NULL,
    frame_height INTEGER NOT NULL,
    lines JSONB NOT NULL  -- Array of lane line coordinates
);

CREATE TABLE traffic_summary (
    id SERIAL PRIMARY KEY,
    cam_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    lane_counts JSONB NOT NULL,  -- IMPORTANT: This is a JSON ARRAY of integers, e.g., [5, 3, 2] where each element is the vehicle count for a lane
    max_cars_in_frame INTEGER NOT NULL,  -- Peak number of vehicles visible at once
    FOREIGN KEY (cam_id) REFERENCES cameras (cam_id)
);

-- IMPORTANT: To sum all lane counts into total vehicles, use this pattern:
-- SELECT (SELECT SUM(value::int) FROM jsonb_array_elements_text(lane_counts)) AS total_vehicles FROM traffic_summary;

-- Example: Find busiest camera by total vehicles
-- SELECT cam_id, SUM((SELECT SUM(value::int) FROM jsonb_array_elements_text(lane_counts))) AS total_traffic
-- FROM traffic_summary GROUP BY cam_id ORDER BY total_traffic DESC LIMIT 1;
"""

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    data: Optional[List] = None

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def execute_sql(sql_query: str):
    """Execute SQL query and return results"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in results]
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")

def get_llm_response(question: str):
    """Get response from LLM with optional SQL generation"""
    
    system_prompt = f"""You are a helpful assistant for a traffic monitoring system that analyzes camera footage and vehicle counts.

Database Schema:
{DB_SCHEMA}

Instructions:
1. If the question is about traffic data, camera information, or requires database querying:
   - Generate a valid PostgreSQL query
   - Return a JSON object with: {{"needs_db": true, "sql": "YOUR_SQL_QUERY", "explanation": "brief explanation"}}

2. If the question is general (like "who are you?" or "what can you do?"):
   - Answer conversationally without database access
   - Return a JSON object with: {{"needs_db": false, "answer": "YOUR_ANSWER"}}

Examples of database questions:
- "How many cameras are in the system?"
- "What's the traffic count for camera cam_001?"
- "Show me the busiest time periods"

Examples of general questions:
- "What is this application?"
- "How can you help me?"

Always respond with valid JSON only."""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    
    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main endpoint to handle user questions about traffic monitoring system
    """
    try:
        # Get LLM decision
        llm_response = get_llm_response(request.question)
        
        if llm_response.get("needs_db"):
            # Database query needed
            sql_query = llm_response.get("sql")
            data = execute_sql(sql_query)
            
            # Generate natural language answer from data
            followup_prompt = f"""Based on this query result, provide a clear natural language answer to: "{request.question}"

Query: {sql_query}
Results: {json.dumps(data, default=str)}

Provide a concise, helpful answer."""
            
            final_response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": followup_prompt}],
                temperature=0.3
            )
            
            answer = final_response.choices[0].message.content.strip()
            
            return QueryResponse(
                answer=answer,
                sql_query=sql_query,
                data=data
            )
        else:
            # No database needed - direct answer
            return QueryResponse(
                answer=llm_response.get("answer"),
                sql_query=None,
                data=None
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Traffic Monitoring Chatbot API", "endpoint": "/query"}