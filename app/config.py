

import os
from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv("API_KEY", "temp-key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "temp-key")


DATABASE_PATH = os.getenv("DATABASE_PATH", "honeypot.db")



LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

MODE=os.getenv("MODE", "dev")
if MODE == "dev":
    print("Running in DEV mode - callbacks disabled")
else:
    print("Running in PROD mode - callbacks enabled")
print("Configuration loaded successfully")