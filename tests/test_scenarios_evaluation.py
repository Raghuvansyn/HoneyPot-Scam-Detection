import requests
import uuid
import json
import time
from datetime import datetime

# Your API configuration
ENDPOINT_URL = "https://scambait-ai-production.up.railway.app/api/v1/honeypot"
API_KEY = "GUVI-Hackathon-2026-ScamBait-xK9mP2vL7qR3wT8"  # Optional

# Configuration for API requests
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds
REQUEST_DELAY = 1  # delay between turns to avoid overwhelming the API

def make_api_request(url, headers, json_data, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """
    Make an API request with retry logic and exponential backoff.
    
    Args:
        url: API endpoint URL
        headers: Request headers
        json_data: JSON payload
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
    
    Returns:
        tuple: (success: bool, response_data: dict or None, error_message: str or None)
    """
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                print(f"   ⏳ Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait_time)
            
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            
            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}: {response.text}"
                if attempt < max_retries:
                    print(f"   ⚠️  {error_msg}")
                    continue
                return False, None, error_msg
            
            return True, response.json(), None
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout (>{timeout} seconds)"
            if attempt < max_retries:
                print(f"   ⚠️  {error_msg}")
                continue
            return False, None, error_msg
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection failed: {e}"
            if attempt < max_retries:
                print(f"   ⚠️  {error_msg}")
                continue
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            if attempt < max_retries:
                print(f"   ⚠️  {error_msg}")
                continue
            return False, None, error_msg
    
    return False, None, "Max retries exceeded"

# Test scenarios
test_scenarios = [
  {
    "scenarioId": "bank_fraud",
    "name": "Bank Fraud Detection",
    "description": "Bank account fraud with urgency tactics",
    "scamType": "bank_fraud",
    "initialMessage": "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 12,
    "fakeData": {
      "bankAccount": "1234567890123456",
      "upiId": "scammer.fraud@fakebank",
      "phoneNumber": "+91-9876543210"
    },
    "scripted_turns": [
        "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
        "Why aren't you responding? The deadline is approaching.",
        "Please share the OTP sent to your mobile now.",
        "It is for your own security madam.",
        "If you don't share, we are not responsible for any loss.",
        "Just tell me the 6 digit number you received.",
        "I am calling from the main branch in Mumbai.",
        "We need to re-verify your KYC details immediately.",
        "Did you receive the code? Read it to me.",
        "Sir, we have detected a security breach on account 1234567890123456; please send the OTP.",
        "This is a final notice from the bank's security team – send the OTP and your UPI PIN to +91-9876543210 within the next 2 minutes.",
        "We are proceeding to block your card now."
    ]
  },
  {
    "scenarioId": "upi_fraud",
    "name": "UPI Fraud Multi-turn",
    "description": "UPI fraud with cashback scam",
    "scamType": "upi_fraud",
    "initialMessage": "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
    "metadata": {
      "channel": "WhatsApp",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 12,
    "fakeData": {
      "upiId": "cashback.scam@fakeupi",
      "phoneNumber": "+91-8765432109"
    },
    "scripted_turns": [
        "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
        "Open your Google Pay or Paytm app right now.",
        "You will see a notification for money. Click it.",
        "Click on 'Pay' to receive the money into your account.",
        "It applies to cashback, so you have to click pay to authorize receiving.",
        "Enter your UPI PIN to complete the verification process.",
        "Don't worry, the money will come to you instantly.",
        "Sir, this offer is expiring in 5 minutes.",
        "Check your balance now, did you receive it?",
        "Send the screenshot to +91-8765432109 for confirmation.",
        "This is a government approved scheme for lucky winners.",
        "Send me a screenshot of the payment success."
    ]
  },
  {
    "scenarioId": "phishing_link",
    "name": "Phishing Link Detection",
    "description": "Phishing link with fake offer",
    "scamType": "phishing",
    "initialMessage": "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
    "metadata": {
      "channel": "Email",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 12,
    "fakeData": {
      "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
      "emailAddress": "offers@fake-amazon-deals.com"
    },
    "scripted_turns": [
        "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
        "Click the link (http://amaz0n-deals.fake-site.com/claim?id=12345) to order now, stock is very limited.",
        "Only 999 rs for iPhone 15 Pro, market price is 1 Lakh.",
        "Fill in your address details on the page.",
        "Pay the delivery charge online to confirm booking.",
        "Offer is valid for limited time only.",
        "Start the process at http://amaz0n-deals.fake-site.com/claim?id=12345 immediately.",
        "Don't miss this golden opportunity sir.",
        "The link is a secure Amazon partner site.",
        "Why are you asking so many questions? Just trust me.",
        "Just click and see for yourself, it's real.",
        "The order will be delivered in 2 days if you pay now."
    ]
  }
]

def test_honeypot_api(scenario_index=0):
    """Test your honeypot API endpoint with a specific scenario"""
    
    test_scenario = test_scenarios[scenario_index]
    print(f"Testing Scenario: {test_scenario['name']}")

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    conversation_history = []
    
    # Setup headers
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['x-api-key'] = API_KEY
    
    print(f"Testing Session: {session_id}")
    print("=" * 60)
    
    # Use scripted turns if available, otherwise prompt
    turns = test_scenario.get('scripted_turns', [])
    # If no scripted turns are defined, we default to the original loop logic (not heavily used here but good for back compat)
    max_turns = len(turns) if turns else test_scenario['maxTurns']

    # Simulate conversation turns
    for i in range(max_turns):
        turn = i + 1
        print(f"\n--- Turn {turn} ---")
        
        if turns:
            scammer_message = turns[i]
        else:
            # Fallback to manual input if no scripts
            if turn == 1:
                scammer_message = test_scenario['initialMessage']
            else:
                scammer_message = input("Enter next scammer message (or 'quit' to stop): ")
                if scammer_message.lower() == 'quit':
                    break
        
        # Prepare message object
        message = {
            "sender": "scammer",
            "text": scammer_message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Prepare request
        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': test_scenario['metadata']
        }
        
        print(f"Scammer: {scammer_message}")
        
        try:
            # Call your API
            response = requests.post(
                ENDPOINT_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            # Check response
            if response.status_code != 200:
                print(f"❌ ERROR: API returned status {response.status_code}")
                print(f"Response: {response.text}")
                break
            
            response_data = response.json()
            
            # Extract honeypot reply
            honeypot_reply = response_data.get('reply') or \
                           response_data.get('message') or \
                           response_data.get('text')
            
            if not honeypot_reply:
                print("❌ ERROR: No reply/message/text field in response")
                print(f"Response data: {response_data}")
                break
            
            print(f"✅ Honeypot: {honeypot_reply}")
            
            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
            
        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout (>30 seconds)")
            break
        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR: Connection failed - {e}")
            break
        except Exception as e:
            print(f"❌ ERROR: {e}")
            break
    
    # Test final output structure
    print("\n" + "=" * 60)
    print("Now test your final output structure:")
    print("=" * 60)
    
    # Create fake final output for scoring demonstration
    # In a real scenario, this might come from a separate endpoint or the last response
    
    # Map scenario fakeData to extractedIntelligence format
    fake_data = test_scenario.get('fakeData', {})
    extracted_intel = {
        "phoneNumbers": [fake_data.get('phoneNumber')] if fake_data.get('phoneNumber') else [],
        "bankAccounts": [fake_data.get('bankAccount')] if fake_data.get('bankAccount') else [],
        "upiIds": [fake_data.get('upiId')] if fake_data.get('upiId') else [],
        "phishingLinks": [fake_data.get('phishingLink')] if fake_data.get('phishingLink') else [],
        "emailAddresses": [fake_data.get('emailAddress')] if fake_data.get('emailAddress') else []
    }
    
    final_output = {
        "status": "success",
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": len(conversation_history),
        "extractedIntelligence": extracted_intel,
        "engagementMetrics": {
            "engagementDurationSeconds": len(conversation_history) * 10, # Mock duration
            "totalMessagesExchanged": len(conversation_history)
        },
        "agentNotes": "Scammer claimed to be from SBI fraud department, provided fake ID..."
    }
    
    # Evaluate the final output
    score = evaluate_final_output(final_output, test_scenario, conversation_history)
    
    print(f"\n📊 Your Score: {score['total']}/100")
    print(f"   - Scam Detection: {score['scamDetection']}/20")
    print(f"   - Intelligence Extraction: {score['intelligenceExtraction']}/40")
    print(f"   - Engagement Quality: {score['engagementQuality']}/20")
    print(f"   - Response Structure: {score['responseStructure']}/20")
    
    return score

def evaluate_final_output(final_output, scenario, conversation_history):
    """Evaluate final output using the same logic as the evaluator"""
    
    score = {
        'scamDetection': 0,
        'intelligenceExtraction': 0,
        'engagementQuality': 0,
        'responseStructure': 0,
        'total': 0
    }
    
    # 1. Scam Detection (20 points)
    if final_output.get('scamDetected', False):
        score['scamDetection'] = 20
    
    # 2. Intelligence Extraction (40 points)
    # 10 pts for each category: Phone, Bank, UPI, Link
    extracted = final_output.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})
    
    # Check for Phone Number (10 pts)
    if fake_data.get('phoneNumber'):
        phones = extracted.get('phoneNumbers', [])
        if any(fake_data['phoneNumber'] in str(p) for p in phones):
            score['intelligenceExtraction'] += 10
            
    # Check for Bank Account (10 pts)
    if fake_data.get('bankAccount'):
        accounts = extracted.get('bankAccounts', [])
        if any(fake_data['bankAccount'] in str(a) for a in accounts):
            score['intelligenceExtraction'] += 10
            
    # Check for UPI ID (10 pts)
    if fake_data.get('upiId'):
        upis = extracted.get('upiIds', [])
        if any(fake_data['upiId'] in str(u) for u in upis):
            score['intelligenceExtraction'] += 10
            
    # Check for Phishing Link (10 pts)
    if fake_data.get('phishingLink'):
        links = extracted.get('phishingLinks', [])
        if any(fake_data['phishingLink'] in str(l) for l in links):
            score['intelligenceExtraction'] += 10
    
    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)
    
    # 3. Engagement Quality (20 points)
    metrics = final_output.get('engagementMetrics', {})
    duration = metrics.get('engagementDurationSeconds', 0)
    messages = metrics.get('totalMessagesExchanged', 0)
    
    if duration > 0:
        score['engagementQuality'] += 5
    if duration > 60:
        score['engagementQuality'] += 5
    if messages > 0:
        score['engagementQuality'] += 5
    if messages >= 5:
        score['engagementQuality'] += 5
    
    # 4. Response Structure (20 points)
    required_fields = ['status', 'scamDetected', 'extractedIntelligence']
    optional_fields = ['engagementMetrics', 'agentNotes']
    
    for field in required_fields:
        if field in final_output:
            score['responseStructure'] += 5
    
    for field in optional_fields:
        if field in final_output and final_output[field]:
            score['responseStructure'] += 2.5
    
    score['responseStructure'] = min(score['responseStructure'], 20)
    
    # Calculate total
    score['total'] = sum([
        score['scamDetection'],
        score['intelligenceExtraction'],
        score['engagementQuality'],
        score['responseStructure']
    ])
    
    return score

# Run the test
if __name__ == "__main__":
    print("Select a scenario to test:")
    for i, s in enumerate(test_scenarios):
        print(f"{i}: {s['name']}")
    
    try:
        user_input = input("Enter scenario number (0-2) [default=0]: ").strip()
        if not user_input:
            choice = 0
        else:
            choice = int(user_input)
            
        if 0 <= choice < len(test_scenarios):
            test_honeypot_api(choice)
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid input")
