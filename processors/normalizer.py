from utils.file_io import load_json, save_json, load_config
from utils.logger import get_logger
from processors.cleaner import clean_records

logger = get_logger("normalizer")

def normalize_record(record: dict) -> dict:
    return {
        "id": record.get("id"),
        "source": record.get("source"),
        "source_type": record.get("source_type"),
        "platform_mentioned": record.get("platform", "Myntra"),
        "title": record.get("title"),
        "text": record.get("text"),
        "rating": record.get("rating"),
        "date": record.get("date"),
        "url": record.get("url"),
        "metadata": record.get("metadata", {})
    }

def run_normalization(input_paths: list[str], output_path: str):
    settings = load_config("settings.json")
    all_records = []
    
    for path in input_paths:
        try:
            records = load_json(path)
            all_records.extend(records)
            logger.info(f"Loaded {len(records)} from {path}")
        except Exception as e:
            logger.warning(f"Could not load {path}: {e}")
            
    logger.info(f"Total raw records loaded: {len(all_records)}")
    
    # 1. Clean records
    cleaned_records = clean_records(all_records, settings)
    
    # 2. Normalize schema
    normalized = [normalize_record(r) for r in cleaned_records]
    
    # 3. Save output
    save_json(normalized, output_path)
    logger.info(f"Normalized {len(normalized)} records -> {output_path}")
    return normalized
