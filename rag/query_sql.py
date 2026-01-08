import os
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseChain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# ---------------------------- SQL Cleaner ----------------------------
def clean_sql(text: str) -> str:
    return (
        text.replace("```sql", "")
            .replace("```", "")
            .strip()
    )


# ---------------------------- Main Logic ----------------------------
def run_query(question: str):
    db_url = os.getenv("DATABASE_URL")
    model_name = os.getenv("MODEL_NAME")

    if not db_url:
        raise ValueError("DATABASE_URL is missing in .env file.")
    if not model_name:
        raise ValueError("MODEL_NAME is missing in .env file.")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing in .env file.")

    db = SQLDatabase.from_uri(db_url)

    sql_prompt = ChatPromptTemplate.from_messages([
        ("system", "You ONLY write SQL queries. Don't explain."),
        ("human", "{input}")
    ])

    sql_llm = ChatOpenAI(model=model_name, temperature=0)

    sql_chain = SQLDatabaseChain.from_llm(
        llm=sql_llm,
        db=db,
        prompt=sql_prompt,
        verbose=True
    )

    # Generate SQL
    raw_sql = sql_chain.invoke(question)
    sql_query = clean_sql(str(raw_sql))

    print(sql_query)

    # Execute SQL manually
    sql_result = db.run(sql_query)


# ------------------ CLI Loop ------------------
if __name__ == "__main__":
    while True:
        q = input("\nAsk (or 'exit'): ")
        if q.lower().strip() == "exit":
            break

        print("\nThinking...\n")
        try:
            response = run_query(q)
            print(response)
        except Exception as e:
            print("\n[Error]")
            print(str(e))
