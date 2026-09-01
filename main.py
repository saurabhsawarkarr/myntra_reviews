import argparse
from utils.logger import get_logger
from utils.file_io import load_json, save_json, load_config
from datetime import date

logger = get_logger("main")

def run_phase(phase: str):
    logger.info(f"===== PHASE {phase} =====")

    if phase == "1":
        run_phase("1.1")
        run_phase("1.2")
        run_phase("1.3")

    elif phase == "1.1":
        from collectors.play_store.play_store_collector import PlayStoreCollector
        PlayStoreCollector().run()

    elif phase == "1.2":
        from collectors.app_store.app_store_collector import AppStoreCollector
        AppStoreCollector().run()

    elif phase == "1.3":
        from collectors.reddit.reddit_collector import RedditCollector
        RedditCollector().run()

    elif phase == "2":
        from processors.cleaner import clean_records
        from processors.normalizer import run_normalization
        settings = load_config("settings.json")
        raw_paths = ["data/raw/play_store_reviews.json", "data/raw/app_store_reviews.json", "data/raw/reddit_data.json", "data/raw/youtube_data.json"]
        for path in raw_paths:
            records = load_json(path)
            if records:
                cleaned = clean_records(records, settings)
                save_json(cleaned, path.replace("raw/", "cleaned/"))
        run_normalization([p.replace("raw/", "cleaned/") for p in raw_paths], "data/normalized/unified_dataset.json")

    elif phase == "3":
        from processors.relevance.keyword_filter import run_keyword_filter
        from processors.relevance.semantic_filter import compute_semantic_scores, compute_final_scores
        from sentence_transformers import SentenceTransformer
        settings = load_config("settings.json")
        records = load_json("data/normalized/unified_dataset.json")
        records = run_keyword_filter(records)
        model = SentenceTransformer(settings["relevance"]["embedding_model"])
        records = compute_semantic_scores(records, model)
        relevant = compute_final_scores(records, settings)
        save_json(relevant, "data/relevant/relevant_records.json")

    elif phase == "4":
        from ai.batch_processor import run_extraction
        run_extraction("data/relevant/relevant_records.json", "data/extracted/extracted_signals.json")

    elif phase == "5":
        from analysis.signal_aggregator import aggregate_signals
        from analysis.pattern_discovery import find_cooccurrences, find_behavioral_chains
        records = load_json("data/extracted/extracted_signals.json")
        aggregated = aggregate_signals(records)
        cooccurrences = find_cooccurrences(records)
        chains = find_behavioral_chains(records)
        save_json({"aggregated": aggregated, "cooccurrences": cooccurrences, "chains": chains}, "data/extracted/patterns.json")

    elif phase == "6":
        from analysis.opportunity_finder import find_opportunities
        records = load_json("data/extracted/extracted_signals.json")
        opportunities = find_opportunities(records)
        save_json(opportunities, "data/extracted/opportunities.json")

    elif phase == "7":
        from analysis.opportunity_scorer import score_opportunities
        records = load_json("data/extracted/extracted_signals.json")
        opportunities = load_json("data/extracted/opportunities.json")
        settings = load_config("settings.json")
        scored = score_opportunities(opportunities, records, settings)
        save_json(scored, "data/extracted/scored_opportunities.json")

    elif phase == "8":
        from reports.report_generator import generate_report
        opportunities = load_json("data/extracted/scored_opportunities.json")
        patterns = load_json("data/extracted/patterns.json")
        output_path = f"reports/output/discovery_report_{date.today().isoformat()}.md"
        generate_report(opportunities, patterns["aggregated"], output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=str)
    parser.add_argument("--from-phase", type=str)
    args = parser.parse_args()

    if args.phase:
        run_phase(args.phase)
    elif args.from_phase:
        # Map string phases to ordered execution list
        order = ["1.1", "1.2", "1.3", "2", "3", "4", "5", "6", "7", "8"]
        try:
            start_idx = order.index(args.from_phase)
            for p in order[start_idx:]:
                run_phase(p)
        except ValueError:
            # Fallback if starting from a whole phase number
            if args.from_phase == "1":
                for p in order:
                    run_phase(p)
            else:
                for p in order:
                    if p >= args.from_phase:
                        run_phase(p)
    else:
        order = ["1.1", "1.2", "1.3", "2", "3", "4", "5", "6", "7", "8"]
        for p in order:
            run_phase(p)
