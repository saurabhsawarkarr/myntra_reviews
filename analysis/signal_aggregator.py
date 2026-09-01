from collections import Counter, defaultdict
from utils.file_io import load_json, save_json
from utils.logger import get_logger

logger = get_logger("signal_aggregator")

def aggregate_signals(records: list[dict]) -> dict:
    uncertainty_counts, blocker_counts = Counter(), Counter()
    action_counts, source_counts, outcome_counts = Counter(), Counter(), Counter()
    source_signal_map = defaultdict(Counter)

    def extract_val(item, key):
        if isinstance(item, dict): return item.get(key, "unknown")
        return item

    for record in records:
        signals = record.get("extracted_signals", {})
        source = record.get("source", "unknown")

        for u in signals.get("pre_purchase_uncertainties", []):
            val = extract_val(u, "theme")
            if val != "unknown":
                uncertainty_counts[val] += 1
                source_signal_map[source][f"uncertainty:{val}"] += 1

        for b in signals.get("purchase_blockers", []):
            val = extract_val(b, "blocker")
            if val != "unknown": blocker_counts[val] += 1

        for a in signals.get("user_workarounds", []):
            val = extract_val(a, "action")
            if val != "unknown": action_counts[val] += 1

        outcome = signals.get("outcome", "unknown")
        if outcome != "unknown": outcome_counts[outcome] += 1

    return {
        "total_records": len(records),
        "uncertainty_frequencies": dict(uncertainty_counts.most_common()),
        "blocker_frequencies": dict(blocker_counts.most_common()),
        "user_action_frequencies": dict(action_counts.most_common()),
        "external_source_frequencies": dict(source_counts.most_common()),
        "outcome_distribution": dict(outcome_counts),
        "signal_by_source": {k: dict(v) for k, v in source_signal_map.items()}
    }
