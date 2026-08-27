# 🛡️ Edge Cases & Handling Strategy — Myntra Review AI Discovery Engine

> **Purpose of this file:** A comprehensive catalog of potential edge cases, anomalies, and failure modes across all 8 phases of the AI Discovery Engine, along with their designed mitigation strategies.

---

## 📡 PHASE 1: Data Collection

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **API Rate Limiting (Reddit)** | PRAW hitting Reddit's 60 requests/min limit, resulting in HTTP 429. | PRAW automatically handles basic rate limits. We enforce `max_posts_per_query` and `max_comments_per_post` in `settings.json` to cap aggressive fetching. |
| **Pagination Failures (Play Store)** | Continuation tokens expiring or breaking mid-fetch. | `while continuation_token and len(all_reviews) < max_reviews` loop safely terminates if the token becomes invalid (None). |
| **Deleted/Removed Content** | Reddit posts or comments deleted by users/mods missing text or author fields. | `_normalize` functions safely use `.get()` with defaults. `validate()` ensures records without core `text` or `id` are dropped before saving. |
| **Network Timeouts** | Transient network failures during collection. | Try-except blocks in Reddit subreddit iterators (`except Exception as e`). Failures are logged, and the collector moves to the next query/subreddit without crashing. |
| **Empty Search Results** | A specific subreddit or query yields 0 results. | The loops simply yield an empty list and append nothing. The process continues to the next query. |

---

## 🧹 PHASE 2: Cleaning & Normalization

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Spam / Bot Reviews** | Repeated characters ("niceeeeeee") or non-alphabetic spam ("👍👍👍"). | `is_spam()` uses regex (`r'(.)\1{10,}'`, `r'^[^a-zA-Z]*$'`) to detect and drop these records. |
| **Extremely Short Text** | "ok", "good app", "bad" — useless for behavioral analysis. | `min_text_length` setting (default 20 chars) filters out non-descriptive reviews. |
| **Extremely Long Text** | Essays that might crash downstream embedding or LLM models. | Text is truncated to `max_text_length` (default 10,000 chars) in `clean_records()`. |
| **Corrupted Encoding** | Null bytes (`\x00`) or weird HTML artifacts in the text. | `BeautifulSoup` strips HTML, and `.replace('\x00', '')` sanitizes null bytes. |
| **Cross-Platform Duplicates** | The same user posting the exact same review on App Store and Play Store. | `clean_records()` maintains a `seen_texts` set across all combined files to deduplicate based on exact text match, regardless of source. |

---

## 🔍 PHASE 3: Relevance Filtering

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Contextual Ambiguity (Keywords)** | The word "size" used for "app size is too big", not clothing size. | Layer 2 Semantic Filtering using Sentence Transformers acts as a safeguard. Keyword score is only a partial weight (0.4). |
| **Sarcasm or Literal Matches** | "I wish Myntra had this feature" triggering the "wishlist" keyword. | Semantic embeddings compare against behavioral concepts ("Saving products for later without purchasing"). Sarcasm usually scores low on semantic similarity. |
| **Overly Aggressive Filtering** | Threshold set too high, resulting in 0 relevant records. | Threshold is configurable in `settings.json`. Logs output `Relevant: X / Y`. If X is too low, the operator can manually lower `relevance_threshold`. |
| **OOM (Out of Memory) on Embeddings** | Large datasets causing RAM/VRAM exhaustion during encoding. | `model.encode()` uses `batch_size=64` to process in chunks rather than loading all embeddings into memory at once. |

---

## 🤖 PHASE 4: AI Extraction

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Groq API Rate Limits** | Hitting Free Tier tokens/min or requests/min limits. | `batch_processor.py` pauses for 2 seconds every `batch_size` (10 records). Implements exponential backoff (`time.sleep(retry_delay * (attempt + 1))`) up to `max_retries`. |
| **Malformed JSON Response** | The LLM outputs conversational text along with JSON, or broken JSON syntax. | `json.loads()` wrapped in try-except. System prompt strictly commands "Return ONLY valid JSON". Failed records are logged and skipped, preventing pipeline crashes. |
| **LLM Hallucinations** | The LLM invents a motivation not present in the text to "be helpful". | Strict system prompt rules: "Never invent motivations", "Only extract what is explicitly stated". Fallback to `"unknown"`. |
| **Context Window Overflow** | Record text exceeds `llama-3-70b-8192` context limit. | Addressed in Phase 2 via `max_text_length` truncation (10,000 chars is well within 8k tokens). |
| **Unrelated Extractions** | The LLM extracting non-fashion complaints (e.g., delivery delays) into purchase blockers. | System prompt scope is explicitly limited to "wishlist-to-purchase behavior". |

---

## 📊 PHASE 5 & 6: Signal Aggregation & Opportunity Discovery

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Zero Co-occurrences** | No signals appear together frequently enough. | `itertools.combinations` handles empty or single-item lists safely. Will just return an empty dict. |
| **Source Skew** | Reddit data dominates 90% of the signals, burying Play Store insights. | `signal_aggregator.py` groups counts by source (`signal_by_source`) allowing cross-source comparison and preventing one source from silently skewing the whole dataset. |
| **Unmatched Opportunities** | Extracted signals don't trigger any of the predefined `OPPORTUNITY_TEMPLATES`. | The system only creates opportunity hypotheses if `supporting_ids` is > 0. If none match, it gracefully returns an empty list (requires analyst to update templates). |

---

## 📏 PHASE 7: Quantify & Compare

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Division by Zero** | Calculating frequency or workaround rates when `total_relevant` or `supporting_record_count` is 0. | Ternary operators safeguard calculations: `... / total if total > 0 else 0`. |
| **Missing Outcome Fields** | LLM could not determine if user purchased or abandoned. | Default fallback to `"unknown"` which maps to a neutral severity score of `2`. |
| **Tied Composite Scores** | Multiple opportunities scoring exactly the same. | Python's `sorted(..., reverse=True)` handles ties gracefully based on original insertion order. |

---

## 📝 PHASE 8: Report Generation

| Edge Case | Description | Mitigation Strategy (Implemented/Planned) |
|---|---|---|
| **Empty Report** | No opportunities passed the threshold or matched templates. | The generator loops over `opportunities`. If empty, the Top Opportunity Areas section is naturally empty, but the Dataset Summary still prints correctly to show where data dropped off. |
| **Missing Representative Quotes** | An opportunity matched via signals but has no `evidence_spans`. | Conditional formatting: `if opp.get("representative_quotes"):` prevents printing an empty quotes block. |

---

*Last updated: 2026-08-28 | Derived from Implementation.md & Architecture.md*
