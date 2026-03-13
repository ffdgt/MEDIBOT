EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe",
    "difficulty breathing", "stroke", "unconscious", "not breathing",
    "severe bleeding", "overdose", "poisoning", "suicidal", "kill myself",
    "want to die", "seizure", "choking", "anaphylaxis", "allergic reaction",
    "severe headache", "paralysis", "loss of consciousness", "fainting",
    "severe burn", "drowning", "electric shock", "high fever"
]

EMERGENCY_RESPONSE = """
🚨 **EMERGENCY ALERT**

This sounds like a medical emergency. Please take immediate action:

📞 **Call Emergency Services NOW:**
- India: **112** or **108** (Ambulance)

⚡ **While waiting for help:**
- Stay calm and stay with the person
- Do NOT give food or water
- Keep them still and comfortable
- Follow dispatcher instructions

⚠️ *Do not rely on this chatbot in emergencies — call for help immediately.*
"""


def check_emergency(user_message):
    message_lower = user_message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message_lower:
            return True, EMERGENCY_RESPONSE
    return False, None