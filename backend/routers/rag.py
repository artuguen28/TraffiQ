import os
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

db_url = os.getenv("DATABASE_URL")
model_name = os.getenv("MODEL_NAME", "gpt-4")
openai_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_key)

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
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)


_FORBIDDEN_KEYWORDS = {
    "insert", "update", "delete", "drop", "truncate", "create", "alter",
    "replace", "exec", "execute", "call", "copy", "grant", "revoke",
    "merge", "upsert", "attach", "detach",
}


def validate_sql(sql_query: str) -> None:
    """Raise ValueError if the query is not a plain SELECT statement."""
    # Strip single-line and multi-line comments before analysing
    import re
    cleaned = re.sub(r"--[^\n]*", " ", sql_query)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)

    tokens = cleaned.lower().split()
    if not tokens:
        raise ValueError("Empty SQL query.")

    if tokens[0] != "select":
        raise ValueError(
            f"Only SELECT queries are permitted. Got: '{tokens[0].upper()}'."
        )

    for token in tokens:
        # Strip trailing punctuation that may appear after a keyword (e.g. "drop;")
        word = token.rstrip(";(),")
        if word in _FORBIDDEN_KEYWORDS:
            raise ValueError(
                f"Forbidden SQL keyword detected: '{word.upper()}'. "
                "Only read-only SELECT queries are allowed."
            )


def execute_sql(sql_query: str):
    validate_sql(sql_query)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in results]
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def get_llm_response(question: str):
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
                {"role": "user", "content": question},
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        return json.loads(content)

    except Exception as e:
        raise Exception(f"LLM error: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        llm_response = get_llm_response(request.question)

        if llm_response.get("needs_db"):
            sql_query = llm_response.get("sql")
            data = execute_sql(sql_query)

            followup_prompt = f"""Based on this query result, provide a clear natural language answer to: "{request.question}"

Query: {sql_query}
Results: {json.dumps(data, default=str)}

Provide a concise, helpful answer."""

            final_response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": followup_prompt}],
                temperature=0.3,
            )

            answer = final_response.choices[0].message.content.strip()

            return QueryResponse(answer=answer, sql_query=sql_query, data=data)
        else:
            answer = llm_response.get("answer")
            if isinstance(answer, list):
                answer = "\n".join(str(item) for item in answer)
            return QueryResponse(answer=answer, sql_query=None, data=None)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
