import os
from sentence_transformers import SentenceTransformer
from processors.relevance.keyword_filter import run_keyword_filter
from processors.relevance.semantic_filter import compute_semantic_scores, compute_final_scores
from utils.file_io import load_json, save_json, load_config
from utils.logger import get_logger

logger = get_logger("relevance_pipeline")

def run_relevance_pipeline(input_path: str, output_path: str):
    logger.info("Starting relevance pipeline...")
    settings = load_config("settings.json")
    
    # 1. Load Data
    records = load_json(input_path)
    logger.info(f"Loaded {len(records)} records for filtering.")
    
    # 2. Keyword Filtering
    records = run_keyword_filter(records)
    
    # 3. Semantic Filtering
    model_name = settings["relevance"]["embedding_model"]
    logger.info(f"Loading SentenceTransformer model '{model_name}'...")
    
    # Provide a warning if GPU is not available
    try:
        import torch
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. Semantic embedding will run on CPU and may be slow.")
    except ImportError:
        pass
        
    model = SentenceTransformer(model_name)
    records = compute_semantic_scores(records, model)
    
    # 4. Compute Final Scores & Filter
    relevant_records = compute_final_scores(records, settings)
    
    # 5. Save Output
    save_json(relevant_records, output_path)
    logger.info(f"Saved {len(relevant_records)} relevant records to {output_path}")
    return relevant_records
