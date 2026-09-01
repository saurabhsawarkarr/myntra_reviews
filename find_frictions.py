import json
import re
import os

def load_data():
    records = []
    base_dir = "data/raw"
    files = ["play_store_reviews.json", "app_store_reviews.json", "reddit_data.json", "youtube_data.json"]
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    for item in data:
                        text = item.get("content") or item.get("text") or item.get("review")
                        if text and len(text.split()) > 10:  # only substantial reviews
                            records.append({
                                "id": item.get("reviewId", item.get("id", "unknown")),
                                "text": text.replace("\n", " "),
                                "source": f.split("_")[0]
                            })
                except Exception as e:
                    pass
    return records

frictions = {
    "Quality & Material Confidence": {
        "includes": ["poor material", "fabric", "durability", "quality mismatch", "expected better quality", "cheap material"],
        "excludes": ["delivery", "login", "refund", "customer service"]
    },
    "Fit & Size Confidence": {
        "includes": ["size selection", "measurements", "inconsistent sizing", "model size", "tight fit", "loose fit", "not sure what size", "size chart is wrong", "ordered m but"],
        "excludes": ["delivery", "refund"]
    },
    "Price & Purchase Timing": {
        "includes": ["waiting for discount", "wait for sale", "saving until price drops", "postpone purchase", "compare price", "waiting for offer"],
        "excludes": ["good offer", "nice discount"]
    },
    "Product Comparison & Decision Confidence": {
        "includes": ["comparing products", "shortlisting", "deciding between", "difficulty choosing", "can't decide which", "too many options to choose"],
        "excludes": ["good recommendation"]
    },
    "Trust, Authenticity & Information Confidence": {
        "includes": ["fake product", "duplicate", "authenticity", "misleading photo", "unreliable review", "insufficient info", "looks different from picture"],
        "excludes": ["scam app", "delivery", "customer service"]
    }
}

records = load_data()
results = {k: [] for k in frictions}

for r in records:
    text = r["text"].lower()
    for name, rules in frictions.items():
        if any(exc in text for exc in rules["excludes"]):
            continue
        
        match_count = sum(1 for inc in rules["includes"] if inc in text)
        if match_count > 0:
            results[name].append((match_count, len(text), r))

with open("friction_results.txt", "w", encoding="utf-8") as out:
    for name in frictions:
        out.write(f"--- {name} ---\n")
        # Sort by match count then length
        sorted_res = sorted(results[name], key=lambda x: (x[0], x[1]), reverse=True)
        count = len(sorted_res)
        out.write(f"Found {count} reviews.\n")
        for res in sorted_res[:10]: # top 10
            r = res[2]
            out.write(f"ID: {r['id']} | Source: {r['source']}\nText: {r['text']}\n\n")
