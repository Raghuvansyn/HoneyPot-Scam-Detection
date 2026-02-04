

import os
from dotenv import load_dotenv


load_dotenv()

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

API_KEY = os.getenv("API_KEY", "temp-key")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "temp-key")


DATABASE_PATH = os.getenv("DATABASE_PATH", "honeypot.db")

#Primary LLM
LLM_PROVIDER = "cerebras"  # Primary
LLM_MODEL = "llama3.1-8b"

# Fallback
FALLBACK_PROVIDER = "groq"
FALLBACK_MODEL = "llama-3.1-8b-instant"


MODE=os.getenv("MODE", "prod")
if MODE == "dev":
    print("Running in DEV mode - callbacks disabled")
else:
    print("Running in PROD mode - callbacks enabled")
print("Configuration loaded successfully")