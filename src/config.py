import os
from dotenv import load_dotenv

load_dotenv()

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
API_KEY = os.getenv("API_KEY", "temp-key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "temp-key")
DATABASE_PATH = os.getenv("DATABASE_PATH", "honeypot.db")

LLM_PROVIDER = "cerebras"
LLM_MODEL = "llama3.1-8b"
FALLBACK_PROVIDER = "groq"
FALLBACK_MODEL = "llama-3.1-8b-instant"

MODE = os.getenv("MODE", "prod")
