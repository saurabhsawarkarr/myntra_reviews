from collections import Counter
from itertools import combinations
from utils.logger import get_logger

logger = get_logger("pattern_discovery")

def find_cooccurrences(records: list[dict]) -> dict:
    pair_counts = Counter()
    for record in records:
        signals = record.get("extracted_signals", {})
        all_signals = (
            [f"uncertainty:{u}" for u in signals.get("uncertainties", []) if u != "unknown"] +
            [f"blocker:{b}" for b in signals.get("purchase_blockers", []) if b != "unknown"] +
            [f"action:{a}" for a in signals.get("user_actions", []) if a != "unknown"]
        )
        for pair in combinations(sorted(set(all_signals)), 2):
            pair_counts[pair] += 1
    return {" + ".join(k): v for k, v in pair_counts.most_common(20)}

def find_behavioral_chains(records: list[dict]) -> list[dict]:
    chains = []
    for record in records:
        signals = record.get("extracted_signals", {})
        wishlist = signals.get("wishlist_behavior", {}).get("detected", False)
        uncertainties = [u for u in signals.get("uncertainties", []) if u != "unknown"]
        actions = signals.get("user_actions", [])
        outcome = signals.get("outcome", "unknown")
        
        if wishlist and uncertainties:
            chains.append({
                "record_id": record.get("id"),
                "chain": {
                    "interest": True,
                    "uncertainties": uncertainties,
                    "external_search": "searched_external_information" in actions,
                    "outcome": outcome
                }
            })
    return chains
