import re, pandas as pd
from bs4 import BeautifulSoup
from utils.file_io import load_json, save_json, load_config
from utils.logger import get_logger

logger = get_logger("cleaner")

def clean_text(text: str) -> str:
    if not text: return ""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace('\x00', '')

def is_spam(text: str) -> bool:
    patterns = [r'(.)\1{10,}', r'^[^a-zA-Z]*$']
    return any(re.search(p, text) for p in patterns)

def clean_records(records: list[dict], settings: dict) -> list[dict]:
    min_len = settings["cleaning"]["min_text_length"]
    max_len = settings["cleaning"]["max_text_length"]
    cleaned, seen_texts, seen_ids = [], set(), set()
    stats = {"duplicates": 0, "empty": 0, "spam": 0, "too_short": 0, "kept": 0}

    for record in records:
        rid = record.get("id")
        text = clean_text(record.get("text", ""))
        if rid in seen_ids: stats["duplicates"] += 1; continue
        if not text: stats["empty"] += 1; continue
        if text in seen_texts: stats["duplicates"] += 1; continue
        if len(text) < min_len: stats["too_short"] += 1; continue
        if is_spam(text): stats["spam"] += 1; continue
        seen_ids.add(rid); seen_texts.add(text)
        record["text"] = text[:max_len]
        cleaned.append(record); stats["kept"] += 1

    logger.info(f"Cleaning stats: {stats}")
    return cleaned
