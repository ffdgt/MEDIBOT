from flask import Flask, render_template, request, jsonify, send_file
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from src.helper import get_embedding_model
from src.emergency import check_emergency
from src.medication import get_medication_info, format_medication_card, extract_drug_name
from src.prompt import system_prompt
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from src.vision import analyze_medicine_image, analyze_medical_report, get_mime_type, is_medical_report
from src.hospitals import find_nearby_hospitals
import os
import io
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ── Load embedding model & vector store ──────────────────────────────────────
print("🤖 Loading embedding model...")
embeddings = get_embedding_model()

print("🌲 Connecting to Pinecone...")
docsearch = PineconeVectorStore.from_existing_index(
    index_name=os.environ.get("PINECONE_INDEX_NAME", "medbot"),
    embedding=embeddings
)
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# ── Load Groq LLM ─────────────────────────────────────────────────────────────
print("⚡ Loading Groq LLM...")
llm = ChatGroq(
    groq_api_key=os.environ.get("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant",
    temperature=0.4,
    max_tokens=1024
)

# ── Build RAG chain ───────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Please answer in English only. Question: {input}"),
])

document_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, document_chain)

# ── In-memory chat history (per session) ─────────────────────────────────────
chat_histories = {}


def get_chat_history(session_id):
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    return chat_histories[session_id]


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    history = get_chat_history(session_id)

    # ── 1. Emergency check ────────────────────────────────────────────────────
    is_emergency, emergency_response = check_emergency(user_message)
    if is_emergency:
        history.append({"role": "user", "content": user_message})
        history.append({"role": "bot", "content": emergency_response})
        return jsonify({
            "response": emergency_response,
            "type": "emergency",
            "sources": []
        })

    # ── 2. Medication card check ──────────────────────────────────────────────
    drug_name = extract_drug_name(user_message)
    med_card = None
    if drug_name:
        med_info = get_medication_info(drug_name)
        med_card = format_medication_card(med_info)

    # ── 3. Build context-aware prompt with history ────────────────────────────
    history_text = ""
    for msg in history[-6:]:  # last 3 exchanges
        role = "Patient" if msg["role"] == "user" else "MediBot"
        history_text += f"{role}: {msg['content']}\n"

    enhanced_input = user_message
    if history_text:
        enhanced_input = f"Previous conversation:\n{history_text}\nCurrent question: {user_message}"

    # ── 4. RAG chain call ─────────────────────────────────────────────────────
    response = rag_chain.invoke({"input": enhanced_input})
    bot_answer = response["answer"]

    # ── 5. Extract sources ────────────────────────────────────────────────────
    sources = []
    for doc in response.get("context", []):
        page = doc.metadata.get("page", "N/A")
        source = doc.metadata.get("source", "Medical Encyclopedia")
        source_entry = f"📖 Page {page} — {os.path.basename(str(source))}"
        if source_entry not in sources:
            sources.append(source_entry)

    # ── 6. Append medication card to response if found ────────────────────────
    if med_card:
        bot_answer = bot_answer + "\n\n" + med_card

    # ── 7. Save to history ────────────────────────────────────────────────────
    history.append({"role": "user", "content": user_message})
    history.append({"role": "bot", "content": bot_answer})

    return jsonify({
        "response": bot_answer,
        "type": "normal",
        "sources": sources
    })


@app.route("/export_pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    history = get_chat_history(session_id)

    if not history:
        return jsonify({"error": "No chat history to export"}), 400

    # ── Build PDF ─────────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        textColor=HexColor("#1a73e8"), fontSize=18, spaceAfter=10
    )
    user_style = ParagraphStyle(
        "User", parent=styles["Normal"],
        textColor=HexColor("#1a73e8"), fontSize=11,
        spaceAfter=4, fontName="Helvetica-Bold"
    )
    bot_style = ParagraphStyle(
        "Bot", parent=styles["Normal"],
        textColor=HexColor("#333333"), fontSize=11,
        spaceAfter=10, leftIndent=10
    )
    date_style = ParagraphStyle(
        "Date", parent=styles["Normal"],
        textColor=HexColor("#888888"), fontSize=9, spaceAfter=20
    )

    story = []
    story.append(Paragraph("🏥 MediBot — Chat Report", title_style))
    story.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        date_style
    ))
    story.append(Spacer(1, 10))

    for msg in history:
        if msg["role"] == "user":
            story.append(Paragraph(f"You: {msg['content']}", user_style))
        else:
            clean = msg["content"].replace("**", "").replace("*", "")
            story.append(Paragraph(f"MediBot: {clean}", bot_style))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"medibot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mimetype="application/pdf"
    )


@app.route("/clear", methods=["POST"])
def clear_chat():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    if session_id in chat_histories:
        chat_histories[session_id] = []
    return jsonify({"status": "cleared"})

@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file_bytes = file.read()
    mime_type  = get_mime_type(file.filename)

    if is_medical_report(file.filename):
        # PDF report → Gemini
        result = analyze_medical_report(file_bytes, mime_type)
        return jsonify({
            "response": result,
            "type": "report"
        })
    else:
        # Image → Groq LLaMA 4 Vision
        result = analyze_medicine_image(file_bytes, mime_type)
        return jsonify({
            "response": result,
            "type": "medicine"
        })


@app.route("/hospitals", methods=["POST"])
def hospitals():
    data = request.get_json()
    lat  = data.get("lat")
    lon  = data.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Location not provided"}), 400

    hospitals_list = find_nearby_hospitals(lat, lon)

    if not hospitals_list:
        return jsonify({
            "hospitals": [],
            "message": "No hospitals found nearby. Try increasing search radius."
        })

    return jsonify({
        "hospitals": hospitals_list,
        "count": len(hospitals_list)
    })


if __name__ == "__main__":
    print("🚀 MediBot is starting...")
    app.run(host="0.0.0.0", port=5000, debug=True)