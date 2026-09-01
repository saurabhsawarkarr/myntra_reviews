import json
import os
from groq import Groq
from pathlib import Path
from utils.env_loader import get_env
from utils.logger import get_logger
from utils.file_io import load_config

logger = get_logger("opportunity_finder")

def load_prompt(filename: str) -> str:
    return (Path("ai/prompts") / filename).read_text(encoding="utf-8")

def find_opportunities(records: list[dict]) -> list[dict]:
    api_key = get_env("GROQ_API_KEY", required=False)
    if not api_key:
        logger.error("GROQ_API_KEY is not set. Cannot run LLM for opportunity discovery.")
        return []

    settings = load_config("settings.json")
    model = settings.get("ai_extraction", {}).get("groq_model", "qwen/qwen3.8-27b")

    # Filter and minimize records to save context window
    minimal_records = []
    for r in records:
        sig = r.get("extracted_signals", {})
        if not sig or not sig.get("is_relevant"):
            continue
            
        # Try to support both old schema (flat array) and new schema (objects)
        uncertainties = sig.get("pre_purchase_uncertainties", sig.get("uncertainties", []))
        blockers = sig.get("purchase_blockers", [])
        actions = sig.get("user_workarounds", sig.get("user_actions", []))
        
        def extract_val(item, key):
            if isinstance(item, dict): return item.get(key, "unknown")
            return item

        u_vals = [extract_val(u, "theme") for u in uncertainties]
        b_vals = [extract_val(b, "blocker") for b in blockers]
        a_vals = [extract_val(a, "action") for a in actions]
        
        # Only include records that have meaningful signals (not all unknown)
        has_signal = any(
            val != "unknown" for val_list in [u_vals, b_vals, a_vals] for val in val_list
        )
        
        if has_signal:
            minimal_records.append({
                "id": r.get("id"),
                "text": r.get("text"),
                "signals": sig
            })
            
    # Fallback: if no records had explicit signals, just grab the top 20 relevant ones
    if not minimal_records:
        for r in records:
            if r.get("extracted_signals", {}).get("is_relevant"):
                minimal_records.append({
                    "id": r.get("id"),
                    "text": r.get("text"),
                    "signals": r.get("extracted_signals")
                })
                if len(minimal_records) >= 20:
                    break

    # Hard limit to prevent blowing up the context window
    minimal_records = minimal_records[:10]

    if not minimal_records:
        logger.warning("No relevant records with signals found for opportunity discovery.")
        return []

    logger.info(f"Sending {len(minimal_records)} records to LLM for opportunity discovery...")
    
    prompt_text = load_prompt("opportunity_discovery_prompt.txt")
    prompt_text = prompt_text.replace("{data}", json.dumps(minimal_records, indent=2))

    client = Groq(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.2,
            max_tokens=2048
        )
        
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
            
        opportunities = json.loads(raw)
        
        # Ensure supporting count is added for the scorer
        for opp in opportunities:
            opp["supporting_record_count"] = len(opp.get("supporting_record_ids", []))
            
        logger.info(f"LLM discovered {len(opportunities)} opportunities.")
        return opportunities
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM opportunity response: {e}")
        return []
    except Exception as e:
        logger.error(f"LLM API error during opportunity discovery: {e}")
        return []
