# 📈 Evaluation Framework — Myntra Review AI Discovery Engine

> **Purpose of this file:** Defines the metrics, strategies, and methodologies for evaluating the performance, accuracy, and reliability of the AI Discovery Engine across all phases.

---

## 🏗️ 1. System-Level Evaluation

### 1.1 Performance & Latency
- **End-to-End Execution Time:** Time taken from Phase 1 to Phase 8 per 1,000 records.
- **Phase-wise Latency:** Time spent in bottleneck phases (e.g., Sentence Transformers encoding in Phase 3, Groq API in Phase 4).
- **Cost Efficiency:** Since Groq free tier is used initially, measure token usage to forecast scaling costs for production deployment.

### 1.2 Data Funnel Integrity
- **Drop-off Rates:** Monitor percentage of data filtered at each step. 
  - *Healthy Funnel Example:* 10,000 raw → 8,000 cleaned (80%) → 1,500 relevant (15%) → 1,450 extracted successfully (96%).
- **Error Rates:** Number of records failing schema validation, triggering try-except blocks, or failing API calls.

---

## 📊 2. Phase-Level Evaluation

### Phase 1: Data Collection
- **Coverage Metric:** Percentage of actual available reviews fetched vs. `max_reviews` target.
- **Source Distribution:** Ratio of data across Play Store, App Store, and Reddit to ensure no single source completely skews the dataset.
- **Metadata Completeness:** Percentage of records with fully populated non-mandatory fields (e.g., `app_version`, `thumbs_up_count`).

### Phase 2: Cleaning & Normalization
- **Spam Detection Accuracy:** Manual spot-check of 100 discarded records to evaluate the False Positive Rate (FPR) of the `is_spam()` function.
- **Deduplication Rate:** Percentage of records dropped due to exact text overlap (identifies bot attacks or cross-platform duplicate posting).

### Phase 3: Relevance Filtering (Crucial)
Evaluated via **Human-in-the-Loop (HITL) Annotation** on a sample set (e.g., 200 records).
- **Precision:** Of the records marked `final_relevance_score >= threshold`, how many are actually relevant to wishlist/purchase behavior?
- **Recall:** Of the records scoring below the threshold, how many were actually relevant but missed?
- **Weight Calibration:** A/B testing `keyword_weight` vs `semantic_weight` (default 0.4/0.6) to optimize the F1-Score.

### Phase 4: AI Information Extraction (Crucial)
- **JSON Success Rate:** Percentage of LLM responses successfully parsed by `json.loads()` without syntax errors.
- **Hallucination Rate:** Spot-check of `evidence_spans` against original text to ensure the LLM isn't inventing motivations (0% tolerance).
- **Extraction Precision/Recall:** Manual evaluation of whether the LLM correctly identified the specific `purchase_blocker` or `uncertainty` present in the text.
- **Default Fallback Rate:** Percentage of fields returning `"unknown"`. A very high rate (>40%) indicates the prompt needs refinement or the data is too ambiguous.

### Phase 5-7: Analysis & Opportunity Scoring
- **Signal Robustness (Cross-Source Validation):** An opportunity is considered "High Confidence" if it appears independently in at least 2 out of 3 sources (e.g., Play Store + Reddit).
- **Scoring Distribution:** Ensure the composite scores range smoothly between 0.0 and 1.0. If all opportunities score >0.9 or <0.2, the dimension weights in `settings.json` need recalibration.

---

## 🛡️ 3. Edge Case Mitigation Evaluation

Based on `edgecase.md`, we evaluate system resilience against known anomalies:
- **Rate Limit Recovery:** Does the system successfully resume extraction after hitting Groq's HTTP 429 status? *(Metric: Successful retries vs. hard failures).*
- **OOM Prevention:** Can the pipeline process 50,000 records on standard hardware without crashing the Semantic Filter? *(Metric: Peak RAM/VRAM usage).*
- **Corrupt Data Handling:** Injection of synthetically corrupted records (null bytes, malformed JSON, emojis) to verify the cleaner catches 100% without crashing the pipeline.

---

## 🔄 4. Continuous Improvement Loop

1. **Weekly Funnel Review:** Check pipeline drop-off percentages.
2. **Monthly Annotation:** Manually label 100 random records to track Phase 3 (Filtering) & Phase 4 (Extraction) Precision/Recall over time.
3. **Prompt Iteration:** If the Phase 4 "unknown" fallback rate rises, adjust `extraction_prompt.txt` using failed examples as few-shot demonstrations.

---
*Last updated: 2026-08-28 | Derived from Architecture.md, Implementation.md & edgecase.md*
