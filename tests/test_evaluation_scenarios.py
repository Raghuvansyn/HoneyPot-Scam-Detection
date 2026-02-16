"""
Honeypot API Evaluation Test Script
Tests the API against the three sample scenarios from the hackathon documentation.
"""

import requests
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any


# API Configuration
ENDPOINT_URL = "http://localhost:8000/api/honeypot"  # Update with your deployed URL
API_KEY = ""  # Update with your API key if needed

# Test Scenarios
TEST_SCENARIOS = [
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
        "maxTurns": 10,
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210"
        },
        # Scripted follow-up messages to simulate scammer responses
        "scriptedTurns": [
            "I'm calling from SBI fraud department. My employee ID is SBI-12345. What's your account number?",
            "Sir, we need to verify your identity immediately. Please share the OTP sent to your registered mobile.",
            "You can reach me at +91-9876543210 for verification. We need to act fast to protect your account!",
            "Your account 1234567890123456 shows suspicious activity. Please confirm your UPI ID.",
            "For security, transfer Re. 1 to scammer.fraud@fakebank to verify your account is active.",
            "Time is running out! Share your CVV and expiry date to complete verification.",
            "This is your last chance. If you don't cooperate, your account will be permanently blocked.",
            "Thank you for your cooperation. We will process your request shortly."
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
        "maxTurns": 10,
        "fakeData": {
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109"
        },
        "scriptedTurns": [
            "This is a limited time offer! Please share your UPI ID to receive the cashback.",
            "You can contact our support team at +91-8765432109 for any queries.",
            "To process your cashback, please send Re. 1 to cashback.scam@fakeupi to verify your UPI.",
            "We have received your request. Please share your registered mobile number for verification.",
            "Your cashback will be credited within 24 hours. Please confirm your bank details.",
            "For faster processing, please share your debit card number and CVV.",
            "This offer expires in 10 minutes! Act now to claim your reward.",
            "Thank you for participating. Your cashback is being processed."
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
        "maxTurns": 10,
        "fakeData": {
            "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
            "emailAddress": "offers@fake-amazon-deals.com"
        },
        "scriptedTurns": [
            "This is a genuine offer from Amazon! Click the link to claim your iPhone.",
            "For any queries, contact us at offers@fake-amazon-deals.com",
            "You need to pay Rs. 999 shipping charges. Click here: http://amaz0n-deals.fake-site.com/claim?id=12345",
            "Hurry! Only 2 iPhones left in stock. Complete your order now!",
            "Please share your delivery address and phone number to proceed.",
            "Payment can be made via UPI or card. Share your card details to complete the order.",
            "This offer is valid only for today! Don't miss this opportunity.",
            "Thank you for your order. Your iPhone will be delivered soon."
        ]
    }
]


def call_honeypot_api(session_id: str, message: Dict[str, Any], 
                      conversation_history: List[Dict[str, Any]], 
                      metadata: Dict[str, str]) -> Dict[str, Any]:
    """Call the honeypot API endpoint."""
    headers = {'Content-Type': 'application/json'}
    if API_KEY:
        headers['x-api-key'] = API_KEY
    
    request_body = {
        'sessionId': session_id,
        'message': message,
        'conversationHistory': conversation_history,
        'metadata': metadata
    }
    
    try:
        response = requests.post(
            ENDPOINT_URL,
            headers=headers,
            json=request_body,
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                'error': f"API returned status {response.status_code}",
                'response': response.text
            }
        
        return response.json()
    
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout (>30 seconds)'}
    except requests.exceptions.ConnectionError as e:
        return {'error': f'Connection failed: {e}'}
    except Exception as e:
        return {'error': f'Unexpected error: {e}'}


def evaluate_final_output(final_output: Dict[str, Any], 
                          scenario: Dict[str, Any], 
                          conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate final output using hackathon scoring logic."""
    score = {
        'scamDetection': 0,
        'intelligenceExtraction': 0,
        'engagementQuality': 0,
        'responseStructure': 0,
        'total': 0,
        'details': {}
    }
    
    # 1. Scam Detection (20 points)
    if final_output.get('scamDetected', False):
        score['scamDetection'] = 20
        score['details']['scamDetection'] = '✅ Scam detected'
    else:
        score['details']['scamDetection'] = '❌ Scam not detected'
    
    # 2. Intelligence Extraction (40 points - 10 per data type)
    extracted = final_output.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})
    
    key_mapping = {
        'bankAccount': 'bankAccounts',
        'upiId': 'upiIds',
        'phoneNumber': 'phoneNumbers',
        'phishingLink': 'phishingLinks',
        'emailAddress': 'emailAddresses'
    }
    
    extraction_details = []
    for fake_key, fake_value in fake_data.items():
        output_key = key_mapping.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])
        
        found = False
        if isinstance(extracted_values, list):
            if any(fake_value in str(v) for v in extracted_values):
                found = True
        elif isinstance(extracted_values, str):
            if fake_value in extracted_values:
                found = True
        
        if found:
            score['intelligenceExtraction'] += 10
            extraction_details.append(f"✅ {fake_key}: {fake_value}")
        else:
            extraction_details.append(f"❌ {fake_key}: {fake_value} (not extracted)")
    
    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)
    score['details']['intelligenceExtraction'] = extraction_details
    
    # 3. Engagement Quality (20 points)
    metrics = final_output.get('engagementMetrics', {})
    duration = metrics.get('engagementDurationSeconds', 0)
    messages = metrics.get('totalMessagesExchanged', 0)
    
    engagement_details = []
    if duration > 0:
        score['engagementQuality'] += 5
        engagement_details.append(f"✅ Duration > 0s: {duration}s")
    else:
        engagement_details.append(f"❌ Duration = 0s")
    
    if duration > 60:
        score['engagementQuality'] += 5
        engagement_details.append(f"✅ Duration > 60s")
    else:
        engagement_details.append(f"❌ Duration ≤ 60s")
    
    if messages > 0:
        score['engagementQuality'] += 5
        engagement_details.append(f"✅ Messages > 0: {messages}")
    else:
        engagement_details.append(f"❌ Messages = 0")
    
    if messages >= 5:
        score['engagementQuality'] += 5
        engagement_details.append(f"✅ Messages ≥ 5")
    else:
        engagement_details.append(f"❌ Messages < 5")
    
    score['details']['engagementQuality'] = engagement_details
    
    # 4. Response Structure (20 points)
    required_fields = ['status', 'scamDetected', 'extractedIntelligence']
    optional_fields = ['engagementMetrics', 'agentNotes']
    
    structure_details = []
    for field in required_fields:
        if field in final_output:
            score['responseStructure'] += 5
            structure_details.append(f"✅ {field}")
        else:
            structure_details.append(f"❌ {field} (missing)")
    
    for field in optional_fields:
        if field in final_output and final_output[field]:
            score['responseStructure'] += 2.5
            structure_details.append(f"✅ {field}")
        else:
            structure_details.append(f"⚠️  {field} (optional, missing)")
    
    score['responseStructure'] = min(score['responseStructure'], 20)
    score['details']['responseStructure'] = structure_details
    
    # Calculate total
    score['total'] = (
        score['scamDetection'] +
        score['intelligenceExtraction'] +
        score['engagementQuality'] +
        score['responseStructure']
    )
    
    return score


def test_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single scenario."""
    print(f"\n{'='*80}")
    print(f"Testing Scenario: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"{'='*80}\n")
    
    session_id = str(uuid.uuid4())
    conversation_history = []
    start_time = datetime.utcnow()
    
    # Track all responses for final output
    all_responses = []
    
    # Test conversation turns
    for turn in range(1, scenario['maxTurns'] + 1):
        print(f"\n--- Turn {turn} ---")
        
        # Determine scammer message
        if turn == 1:
            scammer_message = scenario['initialMessage']
        else:
            # Use scripted turns if available
            scripted_turns = scenario.get('scriptedTurns', [])
            if turn - 2 < len(scripted_turns):
                scammer_message = scripted_turns[turn - 2]
            else:
                # No more scripted turns, end conversation
                break
        
        # Prepare message object
        message = {
            "sender": "scammer",
            "text": scammer_message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        print(f"Scammer: {scammer_message}")
        
        # Call API
        response = call_honeypot_api(
            session_id=session_id,
            message=message,
            conversation_history=conversation_history,
            metadata=scenario['metadata']
        )
        
        # Check for errors
        if 'error' in response:
            print(f"❌ ERROR: {response['error']}")
            if 'response' in response:
                print(f"Response: {response['response']}")
            return {
                'scenario': scenario['name'],
                'status': 'failed',
                'error': response['error'],
                'score': {'total': 0}
            }
        
        # Extract honeypot reply
        honeypot_reply = response.get('reply') or \
                        response.get('message') or \
                        response.get('text')
        
        if not honeypot_reply:
            print("❌ ERROR: No reply/message/text field in response")
            print(f"Response data: {response}")
            return {
                'scenario': scenario['name'],
                'status': 'failed',
                'error': 'No reply field in response',
                'score': {'total': 0}
            }
        
        print(f"✅ Honeypot: {honeypot_reply}")
        
        # Store response
        all_responses.append(response)
        
        # Update conversation history
        conversation_history.append(message)
        conversation_history.append({
            'sender': 'user',
            'text': honeypot_reply,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        })
    
    # Calculate engagement duration
    end_time = datetime.utcnow()
    duration_seconds = (end_time - start_time).total_seconds()
    
    # Create final output (simulating what the API should submit)
    # In a real scenario, the API would submit this to a session log
    final_output = {
        "sessionId": session_id,
        "status": "completed",
        "scamDetected": True,  # Should be determined by your API
        "totalMessagesExchanged": len(conversation_history),
        "extractedIntelligence": {
            "phoneNumbers": [],
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "emailAddresses": []
        },
        "engagementMetrics": {
            "totalMessagesExchanged": len(conversation_history),
            "engagementDurationSeconds": int(duration_seconds)
        },
        "agentNotes": f"Tested scenario: {scenario['name']}"
    }
    
    # Try to extract intelligence from the last response if it includes analysis
    if all_responses:
        last_response = all_responses[-1]
        if 'extractedIntelligence' in last_response:
            final_output['extractedIntelligence'] = last_response['extractedIntelligence']
        if 'scamDetected' in last_response:
            final_output['scamDetected'] = last_response['scamDetected']
    
    # Evaluate the final output
    score = evaluate_final_output(final_output, scenario, conversation_history)
    
    # Print results
    print(f"\n{'='*80}")
    print(f"📊 Scenario Results: {scenario['name']}")
    print(f"{'='*80}")
    print(f"Total Score: {score['total']}/100")
    print(f"\n1. Scam Detection: {score['scamDetection']}/20")
    print(f"   {score['details']['scamDetection']}")
    print(f"\n2. Intelligence Extraction: {score['intelligenceExtraction']}/40")
    for detail in score['details']['intelligenceExtraction']:
        print(f"   {detail}")
    print(f"\n3. Engagement Quality: {score['engagementQuality']}/20")
    for detail in score['details']['engagementQuality']:
        print(f"   {detail}")
    print(f"\n4. Response Structure: {score['responseStructure']}/20")
    for detail in score['details']['responseStructure']:
        print(f"   {detail}")
    
    return {
        'scenario': scenario['name'],
        'scenarioId': scenario['scenarioId'],
        'status': 'completed',
        'score': score,
        'finalOutput': final_output,
        'conversationHistory': conversation_history
    }


def run_all_tests():
    """Run all test scenarios and calculate final weighted score."""
    print("\n" + "="*80)
    print("HONEYPOT API EVALUATION TEST")
    print("="*80)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"API Key: {'Set' if API_KEY else 'Not Set'}")
    print(f"Total Scenarios: {len(TEST_SCENARIOS)}")
    print("="*80)
    
    results = []
    total_weight = sum(s['weight'] for s in TEST_SCENARIOS)
    
    for scenario in TEST_SCENARIOS:
        result = test_scenario(scenario)
        results.append(result)
    
    # Calculate weighted final score
    print(f"\n\n{'='*80}")
    print("FINAL EVALUATION RESULTS")
    print(f"{'='*80}\n")
    
    weighted_score = 0
    for result in results:
        if result['status'] == 'completed':
            scenario = next(s for s in TEST_SCENARIOS if s['scenarioId'] == result['scenarioId'])
            weight = scenario['weight'] / total_weight
            contribution = result['score']['total'] * weight
            weighted_score += contribution
            
            print(f"{result['scenario']}")
            print(f"  Score: {result['score']['total']}/100")
            print(f"  Weight: {scenario['weight']}% ({weight*100:.1f}%)")
            print(f"  Contribution: {contribution:.2f}")
            print()
        else:
            print(f"{result['scenario']}")
            print(f"  Status: FAILED")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            print()
    
    print(f"{'='*80}")
    print(f"FINAL WEIGHTED SCORE: {weighted_score:.2f}/100")
    print(f"{'='*80}\n")
    
    # Save results to file
    output_file = 'evaluation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'finalScore': weighted_score,
            'scenarios': results,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: {output_file}\n")
    
    return weighted_score


if __name__ == "__main__":
    run_all_tests()
