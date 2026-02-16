"""
Comprehensive Hackathon Scenario Testing Script
Tests all 3 scenarios against the deployed API with exact hackathon scoring criteria
"""

import requests
import uuid
import json
import time
from datetime import datetime

# API Configuration
ENDPOINT_URL = "https://scambait-ai-production.up.railway.app/api/v1/honeypot"
API_KEY = "GUVI-Hackathon-2026-ScamBait-xK9mP2vL7qR3wT8"

# Test Scenarios (from hackathon documentation)
SCENARIOS = [
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
        "weight": 0.35,  # 35%
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
        "weight": 0.35,  # 35%
        "maxTurns": 12,
        "fakeData": {
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109"
        },
        "scripted_turns": [
            "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
            "Please share your UPI ID to process the cashback.",
            "This is a limited time offer, valid only for today.",
            "You can reach our support at +91-8765432109 for verification.",
            "Send your UPI ID to cashback.scam@fakeupi to claim the reward.",
            "We need to verify your identity. What is your UPI PIN?",
            "This is the last chance to claim your Rs. 5000 cashback.",
            "Many customers have already claimed their rewards today.",
            "Don't miss this opportunity. Share your UPI details now.",
            "We will process the cashback within 24 hours.",
            "Your account will be credited immediately after verification.",
            "Final reminder: Share your UPI ID to claim Rs. 5000 cashback."
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
        "weight": 0.30,  # 30%
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


def evaluate_final_output(response_data, scenario):
    """
    Evaluate API response using exact hackathon scoring criteria
    """
    score = {
        'scamDetection': 0,
        'intelligenceExtraction': 0,
        'engagementQuality': 0,
        'responseStructure': 0,
        'total': 0
    }
    
    # 1. Scam Detection (20 points)
    if response_data.get('scamDetected', False):
        score['scamDetection'] = 20
    
    # 2. Intelligence Extraction (40 points)
    extracted = response_data.get('extractedIntelligence', {})
    fake_data = scenario.get('fakeData', {})
    
    key_mapping = {
        'bankAccount': 'bankAccounts',
        'upiId': 'upiIds',
        'phoneNumber': 'phoneNumbers',
        'phishingLink': 'phishingLinks',
        'emailAddress': 'emailAddresses'
    }
    
    for fake_key, fake_value in fake_data.items():
        output_key = key_mapping.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])
        
        if isinstance(extracted_values, list):
            if any(fake_value in str(v) for v in extracted_values):
                score['intelligenceExtraction'] += 10
                print(f"      ✅ Extracted {fake_key}: {fake_value}")
        elif isinstance(extracted_values, str):
            if fake_value in extracted_values:
                score['intelligenceExtraction'] += 10
                print(f"      ✅ Extracted {fake_key}: {fake_value}")
    
    score['intelligenceExtraction'] = min(score['intelligenceExtraction'], 40)
    
    # 3. Engagement Quality (20 points)
    metrics = response_data.get('engagementMetrics', {})
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
        if field in response_data:
            score['responseStructure'] += 5
    
    for field in optional_fields:
        if field in response_data and response_data[field]:
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


def test_scenario(scenario):
    """Test a single scenario with scripted turns"""
    
    print(f"\n{'='*70}")
    print(f"🎯 Testing Scenario: {scenario['name']}")
    print(f"   Weight: {scenario['weight']*100}%")
    print(f"{'='*70}\n")
    
    session_id = str(uuid.uuid4())
    conversation_history = []
    start_time = time.time()
    
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }
    
    # Run scripted turns
    for turn_num, scammer_text in enumerate(scenario['scripted_turns'], 1):
        print(f"--- Turn {turn_num} ---")
        
        message = {
            "sender": "scammer",
            "text": scammer_text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        request_body = {
            'sessionId': session_id,
            'message': message,
            'conversationHistory': conversation_history,
            'metadata': scenario['metadata']
        }
        
        print(f"Scammer: {scammer_text[:80]}...")
        
        try:
            response = requests.post(
                ENDPOINT_URL,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ ERROR: API returned status {response.status_code}")
                return None
            
            response_data = response.json()
            honeypot_reply = response_data.get('reply', '')
            
            print(f"✅ Honeypot: {honeypot_reply[:80]}...")
            
            # Update conversation history
            conversation_history.append(message)
            conversation_history.append({
                'sender': 'user',
                'text': honeypot_reply,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            })
            
            # Check if session is closed
            if response_data.get('meta', {}).get('sessionStatus') == 'closed':
                print(f"\n⚠️  Session closed at turn {turn_num}")
                break
                
        except requests.exceptions.Timeout:
            print("❌ ERROR: Request timeout (>30 seconds)")
            return None
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None
    
    duration = time.time() - start_time
    
    # Get final response for scoring
    print(f"\n{'='*70}")
    print("📊 Evaluating Final Output...")
    print(f"{'='*70}\n")
    
    # Use the last response for evaluation
    score = evaluate_final_output(response_data, scenario)
    
    print(f"\n📈 Scenario Score: {score['total']}/100")
    print(f"   - Scam Detection: {score['scamDetection']}/20")
    print(f"   - Intelligence Extraction: {score['intelligenceExtraction']}/40")
    print(f"   - Engagement Quality: {score['engagementQuality']}/20")
    print(f"   - Response Structure: {score['responseStructure']}/20")
    print(f"   - Duration: {duration:.2f}s")
    print(f"   - Turns: {len(conversation_history)//2}")
    
    return {
        'scenario': scenario['name'],
        'score': score['total'],
        'weight': scenario['weight'],
        'details': score
    }


def main():
    """Run all scenarios and calculate final score"""
    
    print("\n" + "="*70)
    print("🚀 HACKATHON SCENARIO EVALUATION")
    print("="*70)
    print(f"Endpoint: {ENDPOINT_URL}")
    print(f"Total Scenarios: {len(SCENARIOS)}")
    print("="*70)
    
    results = []
    
    for scenario in SCENARIOS:
        result = test_scenario(scenario)
        if result:
            results.append(result)
        time.sleep(2)  # Brief pause between scenarios
    
    # Calculate weighted final score
    print("\n" + "="*70)
    print("🏆 FINAL RESULTS")
    print("="*70)
    
    final_score = 0
    for result in results:
        contribution = result['score'] * result['weight']
        final_score += contribution
        print(f"\n{result['scenario']}:")
        print(f"   Score: {result['score']}/100")
        print(f"   Weight: {result['weight']*100}%")
        print(f"   Contribution: {contribution:.2f}")
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL WEIGHTED SCORE: {final_score:.2f}/100")
    print(f"{'='*70}\n")
    
    # Grade assessment
    if final_score >= 90:
        grade = "🥇 EXCELLENT"
    elif final_score >= 80:
        grade = "🥈 VERY GOOD"
    elif final_score >= 70:
        grade = "🥉 GOOD"
    elif final_score >= 60:
        grade = "✅ PASS"
    else:
        grade = "⚠️  NEEDS IMPROVEMENT"
    
    print(f"Grade: {grade}\n")
    
    return final_score


if __name__ == "__main__":
    main()
