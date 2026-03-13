import requests


def get_medication_info(drug_name):
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}&limit=1"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            result = data["results"][0]

            info = {
                "name": drug_name.capitalize(),
                "purpose": result.get("purpose", ["Not available"])[0][:300]
                if result.get("purpose") else "Not available",
                "warnings": result.get("warnings", ["Not available"])[0][:300]
                if result.get("warnings") else "Not available",
                "dosage": result.get("dosage_and_administration", ["Not available"])[0][:300]
                if result.get("dosage_and_administration") else "Not available",
                "side_effects": result.get("adverse_reactions", ["Not available"])[0][:300]
                if result.get("adverse_reactions") else "Not available",
            }
            return info
        else:
            return None
    except Exception:
        return None


def format_medication_card(info):
    if not info:
        return None
    card = f"""
💊 **Medication Info: {info['name']}**

📌 **Purpose:** {info['purpose']}

⚠️ **Warnings:** {info['warnings']}

📋 **Dosage:** {info['dosage']}

🔴 **Side Effects:** {info['side_effects']}

*Always consult your doctor or pharmacist before taking any medication.*
"""
    return card


MEDICATION_TRIGGER_WORDS = [
    "tablet", "medicine", "medication", "drug", "pill", "capsule",
    "dose", "dosage", "prescription", "paracetamol", "ibuprofen",
    "aspirin", "amoxicillin", "metformin", "omeprazole", "cetirizine"
]


def extract_drug_name(message):
    common_drugs = [
        "paracetamol", "ibuprofen", "aspirin", "amoxicillin",
        "metformin", "omeprazole", "cetirizine", "atorvastatin",
        "lisinopril", "metoprolol", "amlodipine", "azithromycin"
    ]
    message_lower = message.lower()
    for drug in common_drugs:
        if drug in message_lower:
            return drug
    return None