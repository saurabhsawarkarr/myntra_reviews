from datetime import date
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("report_generator")

def generate_report(opportunities: list[dict], aggregated: dict, output_path: str):
    import json
    try:
        with open("data/normalized/unified_dataset.json", "r", encoding="utf-8") as f:
            total_analyzed = len(json.load(f))
    except Exception:
        total_analyzed = "Unknown"

    today = date.today().isoformat()
    lines = [
        f"# AI Discovery Engine Report — Myntra",
        f"**Generated:** {today}\n",
        "---\n",
        "## 📊 Dataset Summary\n",
        f"- Total records analyzed: {aggregated.get('total_records', 'N/A')}",
        f"- Uncertainty signals found: {sum(aggregated.get('uncertainty_frequencies', {}).values())}",
        f"- Purchase blocker signals found: {sum(aggregated.get('blocker_frequencies', {}).values())}",
        "",
        "## 🔝 Top Opportunity Areas\n"
    ]

    for i, opp in enumerate(opportunities, 1):
        lines += [
            f"### {i}. {opp['name']}",
            f"> {opp['opportunity_statement']}\n",
            "| Metric | Value |",
            "|---|---|",
            f"| Supporting Records | {opp['supporting_record_count']} |",
            f"| Frequency Score | {opp.get('frequency_score', 0):.1%} |",
            f"| Severity (avg) | {opp.get('severity_avg', 0)} / 5 |",
            f"| Workaround Rate | {opp.get('workaround_rate', 0):.1%} |",
            f"| Metric Relevance | {opp.get('metric_relevance', 'N/A')} |",
            f"| Evidence Strength | {opp.get('evidence_strength', 'N/A')} |",
            f"| Composite Score | {opp.get('composite_score', 0):.3f} |",
            "",
        ]
        if opp.get("representative_quotes"):
            lines.append("**Representative User Quotes:**")
            for q in opp["representative_quotes"][:3]:
                lines.append(f'> "{q}"')
        lines += [f"\n**Classification:** {opp['classification']}", "---\n"]

    lines += [
        "## ⚠️ Known Limitations",
        "- Data from public reviews only; may not represent all user segments",
        "- LLM extraction may miss implicit behavioral signals",
        "- YouTube, Quora, and fashion community sources not yet included",
        "- All opportunity areas are hypotheses requiring primary research validation\n",
        "## 🔬 Research Hypotheses for Interviews & Surveys\n"
    ]
    for i, opp in enumerate(opportunities, 1):
        lines.append(f"{i}. **{opp['name']}** — Validate whether this is a primary driver of wishlist abandonment")

    lines += [
        "\n---",
        f"**Total reviews analyzed:** {total_analyzed}",
        f"**Reviews used for AI Discovery:** {aggregated.get('total_records', 'N/A')}\n"
    ]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Report saved: {output_path}")
