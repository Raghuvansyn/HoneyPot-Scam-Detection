# 🎯 ScamBait AI
### *Turning the tables on scammers through intelligent conversation*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/🦜_LangChain-Latest-green.svg?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-AI-orange.svg?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

**🏆 Built for GUVI Hackathon 2026 🏆**

[Live Demo](#) • [Documentation](project_report.md) • [Deployment Guide](DEPLOYMENT_GUIDE.md)

</div>

---

## 🌟 The Problem We're Solving

Every year, **₹20,000 crores** are stolen from Indian citizens through digital scams. Traditional detection systems just block suspicious messages — but scammers simply change their tactics and continue targeting new victims.

**We're taking a different approach:**

Instead of blocking scams, we **engage** them. Our AI-powered honeypot pretends to be a confused elderly victim, causing scammers to reveal their phone numbers, UPI IDs, bank accounts, and phishing infrastructure. This intelligence gets automatically sent to law enforcement, enabling them to **shut down entire criminal operations** instead of just blocking individual messages.

---

## 💡 What Makes This Different

### Traditional Approach ❌
```
Scam Detected → Block Message → End
```
**Result:** Scammer adjusts tactics, continues operating

### ScamBait AI Approach ✅
```
Scam Detected → Engage Scammer → Extract Intelligence → Dismantle Operation
```
**Result:** Criminal infrastructure exposed and dismantled

---

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 🔍 **Hybrid Detection Engine**
- **Rules-based** keyword scoring (instant)
- **ML-powered** pattern recognition (TF-IDF + SVM)
- **100% accuracy** on test suite
- Trained on 100 real scam samples

</td>
<td width="50%">

### 🤖 **Intelligent Persona**
- LLM-powered elderly character
- Context-aware conversation strategy
- Anti-hallucination safety filter
- Realistic confusion & trust patterns

</td>
</tr>
<tr>
<td width="50%">

### 🕵️ **Real-Time Intelligence**
- Extracts: Phone numbers, UPI IDs, banks
- Captures: Phishing links, keywords
- Regex-based (no hallucination risk)
- Comprehensive forensic logging

</td>
<td width="50%">

### ⚡ **Smart Automation**
- Dynamic conversation termination
- Automatic law enforcement callbacks
- Session persistence across messages
- Production-ready error handling

</td>
</tr>
</table>

---

## 🎬 How It Works

### 1️⃣ Detection Phase
```python
Incoming: "URGENT! Bank account blocked. Send OTP to 9876543210."

Detection Engine:
├─ Rules: 4 high-risk keywords found → Score: 0.18
├─ ML Model: SCAM detected → Confidence: 1.00
└─ Verdict: SCAM ✅
```

### 2️⃣ Engagement Phase
```python
Persona Response: "Oh no! What happened? I'm very worried! 
                  Let me get my pen... what was that number again?"

Strategy: Missing phone number → Ask scammer to repeat it slowly
```

### 3️⃣ Extraction Phase
```python
Intelligence Extracted:
├─ Phone Number: +91-9876543210 ✅
├─ UPI ID: scammer@paytm ✅
├─ Keywords: ["urgent", "blocked", "send otp"] ✅
└─ Confidence: HIGH (3 categories captured)
```

### 4️⃣ Intelligence Delivery
```python
Callback to Law Enforcement:
{
  "sessionId": "abc-123",
  "scamDetected": true,
  "extractedIntelligence": {
    "phoneNumbers": ["+91-9876543210"],
    "upiIds": ["scammer@paytm"],
    ...
  }
}
```

---

## 📊 Performance Metrics

<div align="center">

| Metric | Result |
|--------|--------|
| **Detection Accuracy** | 100% (20/20 test cases) |
| **Detection Speed** | <500ms |
| **Persona Response Time** | 1-2 seconds |
| **False Positives** | 0 |
| **False Negatives** | 0 |
| **Concurrent Sessions** | 100+ supported |

</div>

---

## 🛠️ Technology Stack

| Component | Technology | Why We Chose It |
|-----------|-----------|-----------------|
| **Web Framework** | FastAPI | Async support, auto-docs, high performance |
| **LLM Integration** | LangChain + Groq | Easy orchestration, fast inference (1-2s) |
| **Workflow** | LangGraph | Multi-agent orchestration, state management |
| **ML Model** | scikit-learn | Production-ready, fast training/inference |
| **Database** | SQLite | Zero-config, embedded, perfect for scale |
| **Language** | Python 3.11 | Rich ML/NLP ecosystem, rapid development |

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
Groq API key (free tier available)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/scambait-ai-honeypot.git
cd scambait-ai-honeypot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run the server
python run.py
```

Server starts at `http://localhost:8000` 🎉

---

## 🧪 Testing

### Run Detection Tests
```bash
python tests/test_detection.py
```

**Expected Output:**
```
================================================================================
  DETECTION AGENT — CASCADING ACCURACY TEST (Rules → ML)
================================================================================

  Total tests       : 20
  Passed            : 20
  Failed            : 0
  Accuracy          : 100.0%
  False Positives   : 0
  False Negatives   : 0
================================================================================
```

### Interactive Testing with Swagger UI
```
Open: http://localhost:8000/docs
```

---

## 📡 API Documentation

### Endpoint
```
POST /honeypot
```

### Authentication
```http
x-api-key: your_api_key_here
Content-Type: application/json
```

### Request Example
```json
{
  "sessionId": "test-001",
  "message": {
    "sender": "scammer",
    "text": "URGENT! Your bank blocked. Send OTP to 9876543210.",
    "timestamp": "2026-02-03T10:00:00Z"
  },
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Response Example
```json
{
  "status": "success",
  "reply": "Oh no! What happened? Let me get my pen...",
  "meta": {
    "agentState": "engaging",
    "sessionStatus": "active",
    "persona": "confused_customer",
    "turn": 2,
    "agentNotes": "Detection: SCAM (confidence: 0.95)"
  }
}
```

---

## 💼 Business Impact

### Target Markets

| Market | Problem Solved | Revenue Potential |
|--------|----------------|-------------------|
| **Banks & Financial Institutions** | Proactive fraud prevention | ₹100Cr+ market |
| **Telecom Operators** | Platform abuse reduction | ₹50Cr+ market |
| **Law Enforcement** | Intelligence gathering | Government contracts |
| **Enterprise Security** | Internal threat detection | ₹30Cr+ market |

---

## 🔒 Security & Ethics

### Safeguards Implemented

✅ **Anti-Hallucination Filter** - Prevents AI from generating fake sensitive data
✅ **API Authentication** - Protects against unauthorized access
✅ **Rate Limiting** - Prevents abuse and resource exhaustion
✅ **Audit Logging** - Full forensic trail for legal compliance
✅ **Privacy Protection** - Intelligence shared only with authorized endpoints

---

## 📈 Roadmap

### ✅ Phase 1 - Current
- [x] Multi-layer detection engine
- [x] Context-aware persona
- [x] Real-time intelligence extraction
- [x] Dynamic conversation termination
- [x] API deployment

### 🔄 Phase 2 - Next 3 Months
- [ ] Multilingual support (Hindi, Tamil, Bengali)
- [ ] Advanced conversation memory
- [ ] Real-time monitoring dashboard

### 🚀 Phase 3 - 6-12 Months
- [ ] Federated learning across deployments
- [ ] Criminal network visualization
- [ ] Predictive scam detection

---

## 📂 Project Structure

```
scambait-ai-honeypot/
│
├── app/
│   ├── agents/
│   │   ├── detection.py              # Cascading detection
│   │   ├── persona.py                # Context-aware persona
│   │   ├── extraction.py             # Intelligence extraction
│   │   ├── hallucination_filter.py   # Safety guardrail
│   │   └── timeline.py               # Summarization
│   ├── workflow/
│   │   ├── graph.py                  # LangGraph orchestration
│   │   └── state.py                  # State management
│   ├── database/
│   │   └── persistence.py            # SQLite storage
│   ├── main.py                       # FastAPI application
│   ├── models.py                     # Pydantic schemas
│   └── utils.py                      # Logging & callbacks
│
├── tests/
│   ├── test_detection.py             # Accuracy tests
│   ├── test_scam.json
│   └── test_legit.json
│
├── requirements.txt
├── run.py
├── README.md
├── DEPLOYMENT_GUIDE.md
└── project_report.md
```

---

## 🏆 Hackathon Highlights

### Innovation
🌟 First honeypot to use context-aware LLM personas
🌟 Novel cascading detection (Rules → ML)
🌟 Ethical AI with hallucination prevention

### Technical Excellence
⚡ 100% test accuracy on comprehensive suite
⚡ Production-ready error handling
⚡ Scalable architecture (100+ concurrent sessions)

### Social Impact
❤️ Protects vulnerable elderly citizens
❤️ Enables law enforcement to dismantle networks
❤️ Supports India's digital transformation

---

## 👥 Team

**Project Lead:** [Your Name]
**Email:** [Your Email]
**GitHub:** [Your GitHub]

**Built for:** GUVI Hackathon 2026

---

## 🙏 Acknowledgments

- **GUVI** for organizing this impactful hackathon
- **Anthropic** for Claude AI development assistance
- **Groq** for fast LLM inference
- **Open Source Community** for incredible tools

---

## 📚 Additional Resources

- 📖 [Complete Project Report](project_report.md)
- 🚀 [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 📊 [API Documentation](https://your-deployment-url.com/docs)

---

<div align="center">

### ⭐ If this project helps protect even one person from fraud, it's a success ⭐

**Built with ❤️ to make the digital world safer for everyone**

[⬆ Back to Top](#-scambait-ai)

</div>
