# 🏥 MediBot — AI Medical Health Companion

An intelligent medical chatbot built with RAG (Retrieval-Augmented Generation) 
architecture that provides accurate health information to the general public.

## ✨ Features

- 💬 **AI Chat** — Ask any health question powered by Groq LLaMA
- 💊 **Medicine Analyzer** — Upload tablet photo for instant drug info
- 🩺 **Report Analyzer** — Upload blood/urine test PDF for analysis  
- 🗺️ **Hospital Finder** — Find nearby hospitals using live map
- 🎙️ **Voice Input** — Speak your questions hands-free
- 🔊 **Text to Speech** — Listen to responses read aloud
- 📄 **PDF Export** — Download your chat as a report
- 🚨 **Emergency Detection** — Auto-detects emergencies with helpline numbers
- 🌍 **Multilingual** — Responds in user's language

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM (Text) | Groq LLaMA 3.1 |
| LLM (Vision) | Groq LLaMA 4 Scout |
| LLM (Reports) | Google Gemini 1.5 Flash |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector DB | Pinecone |
| Framework | Flask |
| Maps | OpenStreetMap + Leaflet.js |
| Drug Info | OpenFDA API |

## 🚀 Setup

1. Clone this repository
2. Create virtual environment: `python -m venv medbot`
3. Activate: `medbot\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with your API keys:
```
GROQ_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=medbot
GEMINI_API_KEY=your_key
```
6. Build vector index: `python store_index.py`
7. Run: `python app.py`

## ⚠️ Disclaimer

MediBot provides general health information only.
Always consult a qualified doctor for medical advice.

## 👨‍💻 Author
Pavan Reddy

## Step 4 — Update .gitignore

Open `.gitignore` and replace everything with:
```
# Environment
.env

# Virtual environment
medbot/

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.eggs/

# Data (too large for GitHub)
data/

# Logs
*.log