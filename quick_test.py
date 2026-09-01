import json
from ai.extractor import extract_signals
from groq import Groq
from utils.env_loader import get_env
from utils.file_io import load_config, load_json, save_json
from utils.logger import get_logger
import time
from main import run_phase
import subprocess
import os

logger = get_logger("quick_test")

def run_quick_test():
    logger.info("Running quick test on 10 records...")
    
    # 1. Load relevant records
    records = load_json("data/relevant/relevant_records.json")
    if not records:
        logger.error("No relevant records found.")
        return
        
    # Just take 4 records to keep it fast, and append one guaranteed implicit record
    sample_records = records[:4]
    sample_records.append({
        "id": "mock_strong_inference_1",
        "text": "I really like the styling of this dress but I'm keeping it in my saved items until the wedding season starts to see if they offer a discount.",
        "source": "mock_data",
        "rating": 4,
        "is_relevant": True
    })
    
    settings = load_config("settings.json")
    model = settings["ai_extraction"]["groq_model"]
    api_key = get_env("GROQ_API_KEY", required=True)
    client = Groq(api_key=api_key)
    
    results = []
    
    # 2. Extract signals (Phase 4 mock)
    for i, record in enumerate(sample_records):
        logger.info(f"Extracting {i+1}/10...")
        signals = extract_signals(record, client, model)
        results.append({**record, "extracted_signals": signals})
        time.sleep(2.5) # rate limit
        
    # Save the sample extraction so phase 5 and 6 can pick it up
    save_json(results, "data/extracted/extracted_signals.json")
    
    # 3. Run downstream phases
    logger.info("Running Phase 5 (Patterns)...")
    run_phase("5")
    
    logger.info("Running Phase 6 (Opportunities)...")
    run_phase("6")
    
    logger.info("Running Phase 7 (Scoring)...")
    run_phase("7")
    
    # 4. Rebuild dashboard analytics
    logger.info("Rebuilding Dashboard Analytics...")
    subprocess.run(["py", "dashboard/build_analytics.py"], check=True)
    
    logger.info("Quick test complete! Dashboard should now be updated.")

if __name__ == "__main__":
    run_quick_test()
