from sentence_transformers import SentenceTransformer, util
from utils.file_io import load_config
from utils.logger import get_logger

logger = get_logger("semantic_filter")

RESEARCH_CONCEPTS = [
    "Saving products for later without purchasing immediately",
    "User intends to buy a fashion product but has not yet purchased",
    "Difficulty deciding which fashion product to buy",
    "Uncertainty about size or fit before purchasing",
    "Comparing multiple fashion products before deciding",
    "Searching for information about a product outside the shopping app",
    "Delaying a fashion purchase due to uncertainty or other factors"
]

def compute_semantic_scores(records: list[dict], model: SentenceTransformer) -> list[dict]:
    concept_embeddings = model.encode(RESEARCH_CONCEPTS, convert_to_tensor=True)
    texts = [r.get("text", "") for r in records]
    logger.info(f"Encoding {len(texts)} records...")
    
    # We use show_progress_bar=False to avoid log spam, or True if interactive.
    record_embeddings = model.encode(texts, convert_to_tensor=True, batch_size=64, show_progress_bar=False)

    for i, record in enumerate(records):
        similarities = util.cos_sim(record_embeddings[i], concept_embeddings)
        record["semantic_score"] = round(float(similarities.max()), 4)
        record["best_matching_concept"] = RESEARCH_CONCEPTS[int(similarities.argmax())]
    return records

def compute_final_scores(records: list[dict], settings: dict) -> list[dict]:
    kw_w = settings["relevance"]["keyword_weight"]
    sem_w = settings["relevance"]["semantic_weight"]
    threshold = settings["relevance"]["relevance_threshold"]
    relevant = []
    
    for record in records:
        final = (kw_w * record.get("keyword_score", 0)) + (sem_w * record.get("semantic_score", 0))
        record["final_relevance_score"] = round(final, 4)
        if final >= threshold:
            record["relevance_reason"] = (
                f"keywords={record.get('keyword_matched_groups',[])}; "
                f"concept={record.get('best_matching_concept','')}"
            )
            relevant.append(record)
            
    logger.info(f"Relevant: {len(relevant)} / {len(records)}")
    return relevant
