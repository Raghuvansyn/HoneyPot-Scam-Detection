
import asyncio
import os
import sys
import uuid
import time
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set unique DB for test
os.environ["DATABASE_PATH"] = f"test_honeypot_{int(time.time())}.db"
print(f"Using DB: {os.environ['DATABASE_PATH']}")

from src.models import HoneypotRequest, Message, Metadata

async def mock_llm_fallback_check(text):
    print(f"[MOCK] LLM check for '{text}'")
    if "scam" in text.lower() or "urgent" in text.lower():
        return True, 0.88
    return False, 0.12

async def mock_generate_persona_response(*args, **kwargs):
    print("[MOCK] Persona response generation")
    return "I am confused, please explain slowly."

def mock_get_ml_model():
    print("[MOCK] Getting ML model")
    mock_model = MagicMock()
    # mock predict -> returns [1] (scam) or [0] (safe)
    # mock decision_function -> returns [val]
    # But wait, ml_classify uses global _ML_MODEL.
    # And ml_classify logic:
    # prediction = model.predict([text])[0]
    # confidence = min(round(abs(model.decision_function([text])[0]), 2), 1.0)
    
    # Let's patch ml_classify instead of get_ml_model
    return mock_model

def mock_ml_classify(text):
    print(f"[MOCK] ML classify '{text}'")
    # Simulate ML
    is_scam = "scam" in text.lower() or "urgent" in text.lower()
    confidence = 0.92 if is_scam else 0.85 # High confidence safe/scam for test
    return {"is_scam": is_scam, "confidence": confidence}

# Patching
print("Starting patches...")
with patch('src.agents.detection.llm_fallback_check', side_effect=mock_llm_fallback_check) as p1, \
     patch('src.agents.persona.generate_persona_response', side_effect=mock_generate_persona_response) as p2, \
     patch('src.agents.detection.ml_classify', side_effect=mock_ml_classify) as p3:
     
    print("Imports inside patch...")
    from src.workflow.graph import run_honeypot_workflow
    from src.utils import logger
    
    # Disable logging? Maybe enable to see progress
    # logger.disabled = True 
    # Actually keep logs visible to debug hang

    async def run_test(scenario_name, message_text, expected_scam):
        print(f"\n--- Testing Scenario: {scenario_name} ---")
        print(f"Input: '{message_text}'")
        
        session_id = str(uuid.uuid4())
        request = HoneypotRequest(
            sessionId=session_id,
            message=Message(
                sender="tester",
                text=message_text,
                timestamp=datetime.now().isoformat()
            ),
            metadata=Metadata(channel="console")
        )
        
        start = time.time()
        try:
            print("Invoking workflow...")
            response = await asyncio.wait_for(run_honeypot_workflow(request), timeout=20.0)
            elapsed = time.time() - start
            print(f"Workflow finished in {elapsed:.2f}s")
            
            print(f"Response: {response.reply}")
            print(f"Meta: {response.meta}")
            
            confidence = response.meta.confidence
            scam_detected = "SCAM" in response.meta.agentNotes
            
            print(f"Result: ScamDetected={scam_detected}, Confidence={confidence}")
            
            if expected_scam:
                if not scam_detected:
                    print("❌ FAILED: Expected SCAM detection")
                elif confidence is None:
                    print("❌ FAILED: Confidence is None")
                elif confidence < 0.5:
                     print(f"⚠️ WARNING: Confidence low ({confidence}) for scam")
                else:
                    print(f"✅ PASSED: Detected as SCAM with confidence {confidence}")
            else:
                if scam_detected:
                    print(f"❌ FAILED: False Positive (Confidence {confidence})")
                elif confidence is None:
                     print("❌ FAILED: Confidence is None")
                elif confidence > 0.5:
                     print(f"⚠️ WARNING: High confidence ({confidence}) for safe message")
                else:
                     print(f"✅ PASSED: Detected as SAFE with confidence {confidence}")
                     
            return response
            
        except asyncio.TimeoutError:
            print("❌ ERROR: Workflow TIMEOUT")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def main():
        # Test 1: Safe Message
        await run_test("Safe Greeting", "Hi, are you free for coffee later?", False)
        
        # Test 2: Scam Message (Rule based)
        await run_test("Bank Scam (Rule)", "URGENT: Your SBI account is blocked. Click bit.ly/123 to verify KYC immediately.", True)
        
        # Test 3: Scam Message (ML/LLM Mock)
        await run_test("Generic Scam (LLM Mock)", "I have a scam for you.", True)

    if __name__ == "__main__":
        asyncio.run(main())
