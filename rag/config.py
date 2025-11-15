from dotenv import load_dotenv
import os

load_dotenv()

DB_CONN = os.getenv("DB_CONN")
LLM_MODEL = os.getenv("LLM_MODEL")