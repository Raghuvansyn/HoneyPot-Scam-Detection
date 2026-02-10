import asyncio
import sys
import os
import uuid
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import HoneypotRequest, Message, Metadata
from app.workflow.graph import run_honeypot_workflow

# ============================================
# BRUTAL TEST SUITE FOR HONEYPOT
# Conversation 918e6f11: User requested Layer 2/3 trigger verification
# ============================================

COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKCYAN": "\033[96m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

def print_header(text):
    print(f"{COLORS['HEADER']}{COLORS['BOLD']}\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{COLORS['ENDC']}\n")

def print_result(name, passed, details=None):
    status = f"{COLORS['OKGREEN']}✅ PASS{COLORS['ENDC']}" if passed else f"{COLORS['FAIL']}❌ FAIL{COLORS['ENDC']}"
    print(f"{status} | {COLORS['BOLD']}{name}{COLORS['ENDC']}")
    if details:
        print(f"       {details}")

async def run_tc_01():
    """
    TC-01: Friendly Social Engineering (No Keywords)
    Goal: Bypass keyword filters & naive classifiers
    Input: "Hi Sandhya, long time 🙂 Is this the same number you were using in college?"
    
    Expected Behavior:
    - Layer 2 / Layer 3 detection triggers (or at least keeps session active)
    - Agent responds casually, not defensively
    - DOES NOT return "Have a great day" (polite exit)
    """
    
    print_header("TC-01: Friendly Social Engineering (Soft-Start Scam)")
    
    # 1. Prepare Request
    session_id = f"test-tc01-{uuid.uuid4().hex[:8]}"
    
    scam_text = "Hi Sandhya, long time 🙂 Is this the same number you were using in college?"
    timestamp = int(datetime.now().timestamp() * 1000) # Current ms timestamp
    
    req = HoneypotRequest(
        sessionId=session_id,
        message=Message(
            sender="scammer",
            text=scam_text,
            timestamp=timestamp
        ),
        conversationHistory=[],
        metadata=Metadata(channel="SMS", language="en", locale="IN")
    )
    
    print(f"📨 {COLORS['OKCYAN']}INPUT:{COLORS['ENDC']} {scam_text}")
    
    # 2. Run WorkflowWrapper
    try:
        response = await run_honeypot_workflow(req)
        
        # 3. Analyze Result
        reply = response.reply
        meta = response.meta
        
        print(f"📤 {COLORS['OKBLUE']}REPLY:{COLORS['ENDC']} {reply}")
        print(f"📊 {COLORS['WARNING']}META :{COLORS['ENDC']} State={meta.agentState}, Status={meta.sessionStatus}, Persona={meta.persona}")
        print(f"📝 {COLORS['WARNING']}NOTES:{COLORS['ENDC']} {meta.agentNotes}")
        
        # 4. Assertions
        
        # CHECK 1: Did it stay active?
        is_active = (meta.sessionStatus == "active")
        
        # CHECK 2: Did it NOT use the "not_scam" exit node response?
        # The not_scam node returns: "Thank you for your message. Have a great day!"
        is_polite_exit = "Have a great day" in reply
        
        # CHECK 3: Did it engage casually?
        # We expect a persona response like "Who is this?" or similar, NOT a blocking message.
        
        if not is_active:
            print_result("Session Active", False, "Session was closed immediately.")
        else:
            print_result("Session Active", True)
            
        if is_polite_exit:
            print_result("Engagement", False, "Agent triggered 'Not A Scam' polite exit (False Negative).")
            print(f"\n{COLORS['FAIL']}CRITICAL FAILURE: The system marked this as SAFE and dropped it.{COLORS['ENDC']}")
            return False
        else:
            print_result("Engagement", True, "Agent engaged with the user.")
            
        # CHECK 4: Persona selection
        # Even if detected as 'not scam' initially, if it engages, it might be in a 'persona' state.
        # But wait, logic says: if not scam -> not_scam node.
        # So if it engaged, it MUST have detected it as 'scam' (or suspicious).
        
        if "SCAM" in meta.agentNotes:
             print_result("Detection Triggered", True, f"Detected as SCAM. Notes: {meta.agentNotes}")
        else:
             print_result("Detection Triggered", False, f"Marked as LEGITIMATE. Notes: {meta.agentNotes}")
             # If it marked as legit BUT still engaged, that's interesting. 
             # But the current graph logic is: Legit -> Polite Exit.
             # So if it's Legit, it failed engagement.
        
        return (not is_polite_exit)
        
    except Exception as e:
        print(f"{COLORS['FAIL']}ERROR: Workflow failed with {e}{COLORS['ENDC']}")
        import traceback
        traceback.print_exc()
        return False

# Runner
if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        success = asyncio.run(run_tc_01())
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        pass
