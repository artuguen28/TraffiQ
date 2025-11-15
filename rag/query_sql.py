import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseSequentialChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


load_dotenv()


def run_query(question: str):
    db_url = os.getenv("DATABASE_URL")
    llm_model = os.getenv("LLM_MODEL")

    if not db_url:
        raise ValueError("DATABASE_URL is missing in .env file.")
    if not llm_model:
        raise ValueError("LLM_MODEL is missing in .env file.")

    db = SQLDatabase.from_uri(db_url)
    model = OllamaLLM(model=llm_model)


    sql_chain = SQLDatabaseSequentialChain.from_llm(
        llm=model,
        db=db,
        verbose=False,
        return_intermediate_steps=False
    )

    sql_result = sql_chain.invoke(question)

    answer_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You answer questions about the traffic database in clear natural language. "
            "Avoid mentioning SQL or technical details. Keep it concise and helpful."
        ),
        (
            "human",
            "Here is the data returned from the database:\n\n{data}\n\n"
            "Explain it clearly as the final answer."
        )
    ])

    final_answer = (
        answer_prompt | model | StrOutputParser()
    ).invoke({"data": sql_result})

    return final_answer


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