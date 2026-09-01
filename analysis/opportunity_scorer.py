from utils.logger import get_logger

logger = get_logger("opportunity_scorer")

OUTCOME_SEVERITY = {
    "purchased": 1, "postponed": 3,
    "abandoned": 5, "alternative_purchased": 4, "unknown": 2
}

def score_opportunities(opportunities: list[dict], records: list[dict], settings: dict) -> list[dict]:
    total = len(records)
    weights = settings.get("scoring", {})

    for opp in opportunities:
        supporting = opp.get("supporting_record_count", 0)
        sup_records = [r for r in records if r.get("id") in opp.get("supporting_record_ids", [])]

        freq_score = supporting / total if total > 0 else 0

        severities = [OUTCOME_SEVERITY.get(r.get("extracted_signals", {}).get("outcome", "unknown"), 2) for r in sup_records]
        severity_score = sum(severities) / len(severities) if severities else 2

        workaround_count = sum(
            1 for r in sup_records
            if r.get("extracted_signals", {}).get("user_actions", []) not in [[], ["unknown"]]
        )
        workaround_rate = workaround_count / supporting if supporting > 0 else 0

        metric_relevance = "High" if severity_score >= 3.5 else "Medium" if severity_score >= 2.5 else "Low"

        sources = len(set(r.get("source") for r in sup_records))
        evidence_strength = "Cross-source" if sources >= 2 else "Single-source"

        normalized_severity = (severity_score - 1) / 4
        
        # Use defaults if keys are missing from settings
        f_w = weights.get("frequency_weight", 0.25)
        s_w = weights.get("severity_weight", 0.25)
        w_w = weights.get("workaround_weight", 0.20)
        
        composite = (
            f_w * freq_score +
            s_w * normalized_severity +
            w_w * workaround_rate
        )

        opp.update({
            "frequency_score": round(freq_score, 4),
            "severity_avg": round(severity_score, 2),
            "workaround_rate": round(workaround_rate, 4),
            "metric_relevance": metric_relevance,
            "evidence_strength": evidence_strength,
            "composite_score": round(composite, 4)
        })

    return sorted(opportunities, key=lambda x: x["composite_score"], reverse=True)
