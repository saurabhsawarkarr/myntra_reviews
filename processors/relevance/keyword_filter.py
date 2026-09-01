from utils.file_io import load_config
from utils.logger import get_logger

logger = get_logger("keyword_filter")

def compute_keyword_score(text: str, keyword_groups: dict) -> tuple[float, list[str]]:
    if not text:
        return 0.0, []
    text_lower = text.lower()
    matched_groups = [g for g, kws in keyword_groups.items() if any(kw in text_lower for kw in kws)]
    score = len(matched_groups) / len(keyword_groups)
    return round(score, 4), matched_groups

def run_keyword_filter(records: list[dict]) -> list[dict]:
    keyword_groups = load_config("keyword_lists.json")
    for record in records:
        score, matched = compute_keyword_score(record.get("text", ""), keyword_groups)
        record["keyword_score"] = score
        record["keyword_matched_groups"] = matched
    return records
