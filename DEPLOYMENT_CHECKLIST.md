# Pre-Deployment Checklist

## 1. Test Locally First

Open terminal in `C:\Users\Lenovo\Desktop\one` and run:

```bash
# Install/update dependencies
pip install -r requirements.txt

# Start the server
python run.py
```

Server should start at `http://localhost:8000`

## 2. Test with Swagger UI

Open browser: `http://localhost:8000/docs`

- You should see the Swagger UI with your endpoints
- Test the `/honeypot` endpoint with the test_scam.json data
- Verify you get a response back

## 3. Check Your .env File

Make sure `C:\Users\Lenovo\Desktop\one\.env` contains:

```
GROQ_API_KEY=your_groq_key_here
HACKATHON_API_KEY=your_api_key_here
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
LLM_MODEL=llama-3.1-8b-instant
```

Replace `your_groq_key_here` and `your_api_key_here` with actual values.

## 4. Verify Database Works

After testing locally, check that `honeypot.db` file was created in your project directory.

---

Once all these work locally, proceed to deployment.
