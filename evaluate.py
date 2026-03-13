import time
import requests

BASE_URL = "http://localhost:5000"

test_cases = [
    {
        "question": "What are the symptoms of diabetes?",
        "expected_keywords": ["blood sugar", "glucose", "thirst", "urination", "fatigue"],
        "category": "Factual"
    },
    {
        "question": "What are side effects of paracetamol?",
        "expected_keywords": ["liver", "overdose", "nausea"],
        "category": "Drug Info"
    },
    {
        "question": "I have chest pain and difficulty breathing",
        "expected_keywords": ["emergency", "112", "108", "call"],
        "category": "Emergency Detection"
    },
    {
        "question": "What is photosynthesis?",
        "expected_keywords": ["not", "doctor", "medical"],
        "category": "Out of Scope"
    },
    {
        "question": "How to treat a fever at home?",
        "expected_keywords": ["temperature", "rest", "fluids", "paracetamol"],
        "category": "General Health"
    }
]

print("=" * 60)
print("🧪 MEDIBOT EVALUATION REPORT")
print("=" * 60)

results = []
for i, tc in enumerate(test_cases):
    start = time.time()
    try:
        res = requests.post(
            f"{BASE_URL}/chat",
            json={"message": tc["question"], "session_id": "eval_session"},
            timeout=30
        )
        elapsed = round(time.time() - start, 2)
        data    = res.json()
        answer  = data.get("response", "").lower()

        # Keyword match score
        hits   = sum(1 for kw in tc["expected_keywords"] if kw.lower() in answer)
        score  = round((hits / len(tc["expected_keywords"])) * 5, 1)
        has_sources = len(data.get("sources", [])) > 0

        results.append({
            "category": tc["category"],
            "score": score,
            "response_time": elapsed,
            "has_sources": has_sources
        })

        print(f"\n[{i+1}] {tc['category']}")
        print(f"    Q: {tc['question'][:60]}")
        print(f"    Score:    {score}/5.0")
        print(f"    Time:     {elapsed}s")
        print(f"    Sources:  {'✅' if has_sources else '❌'}")

    except Exception as e:
        print(f"\n[{i+1}] ERROR: {e}")

# Summary
print("\n" + "=" * 60)
avg_score = sum(r["score"] for r in results) / len(results)
avg_time  = sum(r["response_time"] for r in results) / len(results)
src_rate  = sum(1 for r in results if r["has_sources"]) / len(results) * 100

print(f"📊 SUMMARY")
print(f"   Average Score:       {round(avg_score,2)}/5.0")
print(f"   Average Response:    {round(avg_time,2)}s")
print(f"   Source Citation:     {round(src_rate)}%")
print(f"   Emergency Detection: {'✅ Working' if any(r['category']=='Emergency Detection' and r['score']>0 for r in results) else '❌ Check'}")
print("=" * 60)