import time
import os
from ai.extractor import extract_signals
from groq import Groq
from utils.env_loader import get_env
from utils.file_io import load_config, load_json, save_json
from utils.logger import get_logger

logger = get_logger("batch_processor")

def run_extraction(input_path: str, output_path: str):
    records = load_json(input_path)
    settings = load_config("settings.json")
    model = settings["ai_extraction"]["groq_model"]
    batch_size = settings["ai_extraction"]["batch_size"]
    max_retries = settings["ai_extraction"]["max_retries"]
    retry_delay = settings["ai_extraction"]["retry_delay_seconds"]

    # We need to make sure the key is present
    api_key = get_env("GROQ_API_KEY", required=False)
    if not api_key:
        logger.error("GROQ_API_KEY is not set in .env. Phase 4 requires it.")
        return

    client = Groq(api_key=api_key)
    results, failed = [], []

    for i, record in enumerate(records):
        logger.info(f"Processing {i+1}/{len(records)}: {record.get('id')}")
        signals = {}
        for attempt in range(max_retries):
            signals = extract_signals(record, client, model)
            if "error" not in signals: 
                break
            logger.warning(f"Retry {attempt+1}/{max_retries}")
            time.sleep(retry_delay * (attempt + 1))

        if "error" in signals:
            failed.append(record.get("id"))
        else:
            results.append({**record, "extracted_signals": signals})

        # STRICT RATE LIMITING: 
        # Groq limits for qwen/qwen3.8-27b are 30 RPM (requests per minute).
        # We sleep 2.5 seconds per request to guarantee max 24 requests/min.
        time.sleep(2.5)

    save_json(results, output_path)
    logger.info(f"Done. Success: {len(results)}, Failed: {len(failed)}")
    if failed: 
        logger.warning(f"Failed IDs: {failed}")
