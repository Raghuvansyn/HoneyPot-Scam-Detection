
import sys
import os
import time

print(f"Starting at {time.time()}")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print("Importing src.models...", flush=True)
from src.models import HoneypotRequest
print("Imported src.models", flush=True)

print("Importing src.utils...", flush=True)
from src.utils import logger
print("Imported src.utils", flush=True)

print("Importing src.workflow.graph...", flush=True)
# This imports detection.py which imports sklearn
from src.workflow.graph import run_honeypot_workflow
print("Imported src.workflow.graph", flush=True)
print("Finished imports")
