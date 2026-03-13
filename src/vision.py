import google.genai as genai
import base64
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Groq setup ────────────────────────────────────────────────────────────────
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── Tablet / Medicine Image Analysis (Groq LLaMA 4 Vision) ───────────────────
def analyze_medicine_image(image_bytes, mime_type="image/jpeg"):
    try:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are a medical assistant. Analyze this medicine/tablet image and provide:

1. 💊 **Medicine Name** — Identify the medicine name
2. 🎯 **Purpose / Uses** — What condition is it used for?
3. 📋 **Dosage Information** — Typical dosage
4. ⚠️ **Side Effects** — Common and serious side effects
5. 🚫 **Warnings** — Who should NOT take this
6. 🔄 **Drug Interactions** — What to avoid
7. 💡 **General Advice** — Important tips

Always end with: 'Please consult your doctor or pharmacist before taking any medication.'
Respond in English only."""
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Could not analyze the medicine image. Error: {str(e)}"


# ── Medical Report Analysis (Gemini) ─────────────────────────────────────────
def analyze_medical_report(file_bytes, mime_type="application/pdf"):
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

        prompt = """You are an expert medical report analyst. Analyze this medical report and provide:

1. 📋 **Report Type** — What type of report is this?
2. 📊 **Key Values Found** — List all test values:
   Format: Test Name | Your Value | Normal Range | Status (✅ Normal / ⚠️ Borderline / 🔴 Abnormal)
3. 🔴 **Abnormal Findings** — Values outside normal range and what they indicate
4. 🟡 **Borderline Values** — Values that need monitoring
5. ✅ **Normal Values** — What looks healthy
6. 🩺 **Possible Health Implications** — What abnormal values suggest
7. 💡 **Recommendations** — Lifestyle or follow-up suggestions
8. ⚠️ **Important Notice** — This is for informational purposes only

Use simple language a general patient can understand. Respond in English only."""

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(file_bytes).decode("utf-8")
                            }
                        },
                        {"text": prompt}
                    ]
                }
            ]
        )
        return response.text

    except Exception as e:
        return f"⚠️ Could not analyze the medical report. Error: {str(e)}"


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_mime_type(filename):
    filename = filename.lower()
    if filename.endswith(".pdf"):   return "application/pdf"
    elif filename.endswith(".png"): return "image/png"
    elif filename.endswith(".webp"):return "image/webp"
    else:                           return "image/jpeg"

def is_medical_report(filename):
    return filename.lower().endswith(".pdf")