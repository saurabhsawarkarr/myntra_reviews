# 🏛️ Architecture — Myntra Review AI Discovery Engine

> **Purpose of this file:** A detailed technical architecture reference for the entire project. This covers system design, module responsibilities, data flows, schemas, interface contracts, configuration, and key engineering decisions across all 8 phases.

---

## 📐 Architectural Philosophy

This system is designed around **four core principles**:

| Principle | Description |
|---|---|
| **Single Responsibility** | Each module does exactly one thing. Collectors collect. Cleaners clean. The AI only extracts. |
| **Immutability of Raw Data** | Raw source files are never modified. Every stage produces a new output file. |
| **Config-Driven Behavior** | Search queries, subreddits, thresholds — all stored in `config/`, not in code. |
| **LLM-Last Strategy** | AI (Groq) is used only at Phase 4, after all cheap filtering has already been applied. |

---

## 🗂️ Complete Project Directory Layout

```
ai-discovery-engine/
│
├── collectors/                    # Phase 1 — Data collection modules
│   ├── __init__.py
│   ├── base_collector.py          # Abstract base class for all collectors
│   ├── play_store/
│   │   ├── __init__.py
│   │   └── play_store_collector.py
│   ├── app_store/
│   │   ├── __init__.py
│   │   └── app_store_collector.py
│   └── reddit/
│       ├── __init__.py
│       └── reddit_collector.py
│
├── processors/                    # Phase 2 — Cleaning and normalization
│   ├── __init__.py
│   ├── cleaner.py                 # Text cleaning, deduplication, spam removal
│   ├── normalizer.py              # Unified schema transformation
│   └── relevance/                 # Phase 3 — Relevance filtering
│       ├── __init__.py
│       ├── keyword_filter.py      # Rule-based keyword matching
│       └── semantic_filter.py     # Sentence Transformers embedding filter
│
├── ai/                            # Phase 4 — LLM-powered extraction
│   ├── __init__.py
│   ├── extractor.py               # Groq API call manager
│   ├── batch_processor.py         # Batching + rate-limit handling
│   └── prompts/
│       ├── extraction_prompt.txt  # Main structured extraction prompt
│       └── system_prompt.txt      # System role definition
│
├── analysis/                      # Phases 5–7 — Pattern and opportunity discovery
│   ├── __init__.py
│   ├── signal_aggregator.py       # Phase 5 — Aggregate extracted signals
│   ├── pattern_discovery.py       # Phase 5 — Co-occurrence and behavioral chains
│   ├── opportunity_finder.py      # Phase 6 — Convert signals to opportunities
│   └── opportunity_scorer.py      # Phase 7 — Score on 5 dimensions
│
├── reports/                       # Phase 8 — Report generation
│   ├── __init__.py
│   ├── report_generator.py
│   └── output/                    # Generated reports stored here
│
├── data/                          # All data files (auto-created)
│   ├── raw/                       # Phase 1 output — never modified
│   │   ├── play_store_reviews.json
│   │   ├── app_store_reviews.json
│   │   └── reddit_data.json
│   ├── cleaned/                   # Phase 2 intermediate output
│   ├── normalized/                # Phase 2 final output
│   │   └── unified_dataset.json
│   ├── relevant/                  # Phase 3 output
│   │   └── relevant_records.json
│   └── extracted/                 # Phase 4 output
│       └── extracted_signals.json
│
├── config/                        # Configuration files
│   ├── search_queries.json        # Reddit search queries
│   ├── subreddits.json            # Target subreddits
│   ├── keyword_lists.json         # Relevance keyword groups
│   └── settings.json             # Global settings (thresholds, limits)
│
├── utils/                         # Shared utilities
│   ├── __init__.py
│   ├── logger.py                  # Centralized logging
│   ├── file_io.py                 # JSON read/write helpers
│   └── env_loader.py              # .env / environment variable loader
│
├── .env                           # Credentials (git-ignored)
├── .env.example                   # Template for credentials
├── requirements.txt               # Python dependencies
├── main.py                        # Orchestrator — runs all phases in sequence
├── context.md                     # Project context and source of truth
└── Architecture.md                # This file
```

---

## 🔐 Secrets & Environment Variables

All credentials are loaded from environment variables only. They are **never hardcoded**.

```
# .env.example

REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent_string
GROQ_API_KEY=your_groq_api_key
```

Loaded at startup via `utils/env_loader.py` using `python-dotenv`.

---

## 🔄 Full Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PHASE 1: COLLECTION                         │
│                                                                       │
│  ┌─────────────┐   ┌─────────────────┐   ┌────────────────────────┐ │
│  │  Google      │   │  Apple App       │   │  Reddit API            │ │
│  │  Play Store  │   │  Store           │   │  (PRAW)                │ │
│  │  (google-   │   │  (app-store-     │   │                        │ │
│  │   play-     │   │   scraper /      │   │  Posts + Comments      │ │
│  │   scraper)  │   │   RSS feed)      │   │  with thread links     │ │
│  └──────┬──────┘   └────────┬─────────┘   └──────────┬─────────────┘ │
│         │                   │                          │               │
│         ↓                   ↓                          ↓               │
│  play_store_reviews.json  app_store_reviews.json  reddit_data.json    │
│                   [data/raw/ — IMMUTABLE]                             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     PHASE 2: CLEANING & NORMALIZATION                │
│                                                                       │
│  cleaner.py           normalizer.py                                   │
│  ─────────────────    ────────────────────────────────────────────── │
│  - Deduplicate        - Map all sources to canonical schema           │
│  - Remove empty       - Standardize date format (YYYY-MM-DD)         │
│  - Normalize text     - Standardize source names                     │
│  - Remove HTML        - Fill missing fields with null                │
│  - Remove spam        - Assign unique record IDs                     │
│  - Min length check                                                   │
│                                                                       │
│            Output: data/normalized/unified_dataset.json              │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      PHASE 3: RELEVANCE FILTERING                    │
│                                                                       │
│  Layer 1: keyword_filter.py          Layer 2: semantic_filter.py    │
│  ───────────────────────────         ────────────────────────────── │
│  Pattern match on keyword            Sentence Transformers           │
│  groups (wishlist, intent,           (all-MiniLM-L6-v2 or similar)  │
│  uncertainty, fashion signals)                                        │
│                                      Compare record embeddings       │
│  keyword_score: 0.0–1.0              against 7 research concept      │
│                                      embeddings                      │
│                                      semantic_score: 0.0–1.0         │
│                                                                       │
│  final_relevance_score = weighted combination (configurable)         │
│                                                                       │
│  Records below threshold → FILTERED OUT                              │
│  Records above threshold → PASSED TO PHASE 4                        │
│                                                                       │
│            Output: data/relevant/relevant_records.json               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   PHASE 4: AI INFORMATION EXTRACTION                 │
│                                                                       │
│  extractor.py                batch_processor.py                      │
│  ────────────────────────    ─────────────────────────────────────── │
│  Build prompt from record    Batch records (e.g. 10 at a time)      │
│  Call Groq API               Respect rate limits                     │
│  Parse JSON response         Retry on failure                        │
│  Validate schema             Log failures without crashing           │
│                                                                       │
│  LLM: Groq free tier (e.g. llama-3-70b-8192 or mixtral-8x7b)       │
│                                                                       │
│            Output: data/extracted/extracted_signals.json             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 5: SIGNAL AGGREGATION & PATTERNS            │
│                                                                       │
│  signal_aggregator.py         pattern_discovery.py                   │
│  ────────────────────────     ─────────────────────────────────────  │
│  Count signal frequencies     Detect co-occurring signal pairs       │
│  Group by source              Identify behavioral chain sequences    │
│  Cross-source comparison      Compare patterns across data sources   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      PHASE 6: OPPORTUNITY DISCOVERY                  │
│                                                                       │
│  opportunity_finder.py                                               │
│  ─────────────────────────────────────────────────────────────────  │
│  Group related signals into clusters                                 │
│  Generate opportunity statements from signal clusters                │
│  Label each as: evidence-backed hypothesis                           │
│  Link supporting evidence spans                                      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       PHASE 7: QUANTIFY & COMPARE                    │
│                                                                       │
│  opportunity_scorer.py                                               │
│  ─────────────────────────────────────────────────────────────────  │
│  Score each opportunity on 5 dimensions:                             │
│   1. Frequency         (record count / total relevant)               │
│   2. Severity          (1–5 scale from extracted signals)            │
│   3. Workaround Rate   (workaround count / affected count)           │
│   4. Metric Relevance  (strength of link to wishlist drop-off)       │
│   5. Evidence Strength (single → multiple → cross-source)           │
│                                                                       │
│  Rank opportunities by composite score                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 8: DISCOVERY REPORT                     │
│                                                                       │
│  report_generator.py                                                 │
│  ─────────────────────────────────────────────────────────────────  │
│  Generate structured markdown / text report                          │
│  Include: summary, top opportunities, behavioral chains,             │
│  representative quotes, source breakdown, limitations,               │
│  research hypotheses for interviews and surveys                      │
│                                                                       │
│            Output: reports/output/discovery_report.md                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Architecture Details

---

### `collectors/base_collector.py` — Abstract Base Class

All collectors must implement this interface:

```python
class BaseCollector(ABC):

    @abstractmethod
    def collect(self) -> list[dict]:
        """Collect raw records from the source."""
        pass

    @abstractmethod
    def validate(self, record: dict) -> bool:
        """Validate that a record has the minimum required fields."""
        pass

    def save(self, records: list[dict], output_path: str) -> None:
        """Save collected records to a JSON file."""
        pass

    def summarize(self, records: list[dict]) -> dict:
        """Return a collection summary dict."""
        pass
```

This ensures any future collector (e.g., YouTube comments, Quora) can be added without changing the rest of the system.

---

### `collectors/play_store/play_store_collector.py`

| Property | Value |
|---|---|
| **Library** | `google-play-scraper` (Python) |
| **Target App ID** | `com.myntra.android` |
| **Output File** | `data/raw/play_store_reviews.json` |
| **Fields Collected** | review_id, source, platform, rating, text, date, user_name, app_version, thumbs_up_count |
| **Pagination** | Collect as many records as available via `continuation_token` |
| **Deduplication** | Skip records with duplicate `review_id` at collection time |

---

### `collectors/app_store/app_store_collector.py`

| Property | Value |
|---|---|
| **Library** | `app-store-scraper` (Python) or iTunes RSS feed |
| **Target App** | Myntra — India App Store |
| **Output File** | `data/raw/app_store_reviews.json` |
| **Fields Collected** | review_id, source, platform, title, rating, text, date, author, app_version |
| **Limit** | RSS feed is typically capped at ~500 most recent reviews |

---

### `collectors/reddit/reddit_collector.py`

| Property | Value |
|---|---|
| **Library** | `PRAW` (Python Reddit API Wrapper) |
| **Authentication** | Environment variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT |
| **Output File** | `data/raw/reddit_data.json` |
| **Search Source** | `config/search_queries.json` and `config/subreddits.json` |
| **Data Collected** | Posts + nested comments with parent_id linkage |
| **Rate Limiting** | Respect Reddit API limits (60 requests/minute) |

**Reddit Collector Flow:**
```
Load search queries from config
    ↓
For each query → search Reddit API → collect top N posts
    ↓
For each post → collect post metadata + all comments
    ↓
Preserve parent_id on each comment (thread relationship)
    ↓
Deduplicate by post/comment ID
    ↓
Write to data/raw/reddit_data.json
```

---

### `processors/cleaner.py`

**Input:** `data/raw/*.json` (all three raw files)

**Operations:**

| Operation | Description |
|---|---|
| Deduplication | Remove records with identical `id` or identical `text` |
| Empty removal | Drop records where `text` is null or empty |
| Whitespace normalization | Strip leading/trailing whitespace, collapse internal spaces |
| HTML removal | Strip HTML tags using `BeautifulSoup` or `re` |
| Minimum length | Drop records with fewer than `MIN_TEXT_LENGTH` characters (configurable) |
| Spam detection | Rule-based: drop records matching obvious spam patterns |
| Date standardization | Parse all dates to `YYYY-MM-DD` ISO format |

**Output:** `data/cleaned/` (intermediate, one file per source)

---

### `processors/normalizer.py`

**Input:** `data/cleaned/`

**Operation:** Maps each source's specific fields to the unified canonical schema:

```json
{
  "id": "string — unique across all sources",
  "source": "google_play | apple_app_store | reddit",
  "source_type": "app_review | reddit_post | reddit_comment",
  "platform_mentioned": "Myntra",
  "title": "string or null",
  "text": "string — cleaned text",
  "rating": "integer 1-5 or null",
  "date": "YYYY-MM-DD or null",
  "url": "string or null",
  "metadata": {
    "app_version": "string or null",
    "thumbs_up_count": "integer or null",
    "subreddit": "string or null",
    "score": "integer or null",
    "num_comments": "integer or null",
    "parent_id": "string or null"
  }
}
```

**Output:** `data/normalized/unified_dataset.json`

---

### `processors/relevance/keyword_filter.py`

**Input:** `data/normalized/unified_dataset.json`

**Config:** `config/keyword_lists.json`

**Keyword Groups:**

```json
{
  "wishlist_saving": ["wishlist", "wish list", "saved", "save for later", "shortlisted", "shortlist", "kept aside", "bookmarked"],
  "purchase_intent": ["wanted to buy", "planning to buy", "thinking of buying", "buy later", "purchase later"],
  "purchase_delay": ["wait", "waiting", "postpone", "later", "couldn't decide", "not buying yet"],
  "uncertainty": ["confused", "not sure", "uncertain", "doubt", "couldn't decide"],
  "fashion_signals": ["size", "fit", "quality", "material", "colour", "color", "style", "look", "price", "discount", "sale", "review"],
  "external_info": ["youtube", "instagram", "reddit", "asked friends", "other website", "offline store"]
}
```

**Scoring:**
- Each matched keyword group contributes a weighted score
- `keyword_score` is normalized to `0.0–1.0`
- Weights are configurable in `config/settings.json`

---

### `processors/relevance/semantic_filter.py`

**Library:** `sentence-transformers` (local, free, no API key required)

**Recommended model:** `all-MiniLM-L6-v2` (fast and accurate for similarity tasks)

**Research concept anchor sentences:**

```python
RESEARCH_CONCEPTS = [
    "Saving products for later without purchasing immediately",
    "User intends to buy a fashion product but has not yet purchased",
    "Difficulty deciding which fashion product to buy",
    "Uncertainty about size or fit before purchasing",
    "Comparing multiple fashion products before deciding",
    "Searching for information about a product outside the shopping app",
    "Delaying a fashion purchase due to uncertainty or other factors"
]
```

**Scoring:**
- Embed the record text and each concept sentence
- Compute cosine similarity between record and each concept
- `semantic_score` = max similarity across all concepts
- Configurable threshold in `config/settings.json` (e.g., `0.45`)

**Final Relevance Score:**
```
final_relevance_score = (keyword_weight × keyword_score) + (semantic_weight × semantic_score)
```

Default weights (configurable):
```
keyword_weight = 0.4
semantic_weight = 0.6
```

**Output:** `data/relevant/relevant_records.json`

---

### `ai/extractor.py`

**LLM Provider:** Groq API (free tier)

**Recommended Model:** `llama-3-70b-8192` or `mixtral-8x7b-32768`

**Input:** One relevant record at a time (or small batches)

**Prompt Strategy:**
- System prompt defines the role and strict extraction rules
- User prompt includes the record text
- Response must be valid JSON (enforce with `response_format` if supported)

**Extraction Output Schema per record:**

```json
{
  "is_relevant": true,
  "wishlist_behavior": {
    "detected": true,
    "type": "potential_purchase | bookmarking | comparison | waiting_for_sale | unknown",
    "confidence": 0.85
  },
  "motivation": ["liked_design", "good_price", "trending_style"],
  "uncertainties": ["size", "fit", "quality", "material", "color", "style"],
  "purchase_blockers": ["low_fit_confidence", "price_too_high", "conflicting_reviews", "no_discount"],
  "user_actions": ["searched_external_information", "compared_products", "visited_offline_store", "ordered_multiple_sizes"],
  "external_information_sources": ["Instagram", "YouTube", "Reddit", "friend_recommendation"],
  "outcome": "purchased | postponed | abandoned | alternative_purchased | unknown",
  "evidence_spans": ["exact quote from text that supports extraction"]
}
```

**Critical AI Extraction Rules (enforced in system prompt):**
1. Only extract information explicitly stated or strongly implied by the text
2. Use `"unknown"` for any field that cannot be determined
3. Do not invent motivations
4. Do not assume every saved product = purchase intent
5. Do not classify general sentiment unless it directly relates to wishlist-to-purchase behavior

---

### `ai/batch_processor.py`

| Property | Value |
|---|---|
| **Batch Size** | Configurable (default: 10 records per API call) |
| **Rate Limiting** | Sleep between batches to respect Groq free tier limits |
| **Retry Logic** | Exponential backoff on API errors |
| **Failure Handling** | Log failures, skip record, continue — never crash the pipeline |
| **Progress Tracking** | Log processed count every N records |

---

### `analysis/signal_aggregator.py` — Phase 5

**Input:** `data/extracted/extracted_signals.json`

**Operations:**
- Count frequency of each signal type (uncertainties, blockers, actions, sources)
- Group counts by source (Play Store vs App Store vs Reddit)
- Identify signals that appear across multiple sources (cross-source validation)
- Calculate signal co-occurrence matrix

**Example output:**
```json
{
  "signal_frequencies": {
    "size_uncertainty": 342,
    "fit_uncertainty": 289,
    "conflicting_reviews": 178,
    "checked_instagram": 156,
    "purchase_postponed": 201
  },
  "cross_source_signals": {
    "size_uncertainty": ["google_play", "apple_app_store", "reddit"],
    "checked_instagram": ["reddit"]
  },
  "co_occurrences": {
    "size_uncertainty + fit_uncertainty": 198,
    "conflicting_reviews + purchase_postponed": 143
  }
}
```

---

### `analysis/pattern_discovery.py` — Phase 5

**Goal:** Identify recurring behavioral chains across records.

**Behavioral Chain Detection:**
Find sequences in extracted signals such as:

```
Interest → Size/Fit Uncertainty → External Search → Purchase Delay
Interest → Price Too High → Wait for Sale → Purchase/Abandon
Interest → Conflicting Reviews → Cannot Decide → Abandon
```

**Output:** Named behavioral chain patterns with supporting record counts and evidence.

---

### `analysis/opportunity_finder.py` — Phase 6

**Input:** Aggregated signals + behavioral chains

**Goal:** Group related signals into named opportunity areas.

**Opportunity Statement Format:**
```
Opportunity Name: [Short Label]

Signals:
  - Signal A (frequency: N)
  - Signal B (frequency: N)

Potential Underlying Need:
  [1–2 sentence description of the unmet user need]

Representative Quotes:
  - "exact user quote from evidence_spans"
  - "exact user quote from evidence_spans"

Source Distribution:
  Play Store: N% | App Store: N% | Reddit: N%

Classification: evidence-backed hypothesis (requires primary research validation)
```

---

### `analysis/opportunity_scorer.py` — Phase 7

**Scoring Dimensions:**

| Dimension | Calculation |
|---|---|
| **Frequency Score** | Supporting records / Total relevant records |
| **Severity Score** | Derived from outcome field: `purchased=1`, `postponed=3`, `abandoned=5` |
| **Workaround Rate** | Records with `user_actions` ≠ empty / Records experiencing the issue |
| **Metric Relevance** | Heuristic: how directly does the signal chain lead to purchase drop-off? |
| **Evidence Strength** | 1 = single record only, 2 = multiple records, 3 = cross-source |

**Composite Score:** Configurable weighted average of all 5 dimensions.

**Output — Opportunity Comparison Table:**

| Opportunity | Frequency | Severity | Workaround Rate | Metric Relevance | Evidence Strength | Composite |
|---|---|---|---|---|---|---|
| Fit Confidence Gap | High | 4.2 | 68% | High | Cross-source | 0.87 |
| Price Timing Support | High | 3.1 | 42% | High | Cross-source | 0.76 |
| Product Comparison | Medium | 3.8 | 71% | Medium | Multi-record | 0.69 |
| Styling Confidence | Medium | 2.9 | 55% | Medium | Multi-record | 0.61 |

---

### `reports/report_generator.py` — Phase 8

**Output format:** Markdown (`.md`) and optionally JSON

**Report sections:**

```
1. EXECUTIVE SUMMARY
   - Total records collected (by source)
   - Records after cleaning
   - Records after relevance filtering
   - AI-processed records

2. DATA QUALITY NOTES
   - Collection errors
   - Duplicate removal counts
   - Filtering rates

3. TOP OPPORTUNITY AREAS  (ranked by composite score)
   For each opportunity:
   - Opportunity statement
   - Evidence count and sources
   - Severity and workaround rate
   - Key behavioral pattern chain diagram
   - Representative user quotes
   - Confidence level

4. SIGNAL FREQUENCY ANALYSIS
   - Ranked list of all detected signals
   - Cross-source signal validation table

5. BEHAVIORAL PATTERNS
   - Most common behavioral chain sequences
   - Frequency and representative examples

6. SOURCE COMPARISON
   - Differences between Play Store, App Store, Reddit findings

7. RESEARCH HYPOTHESES
   - Prioritized list of hypotheses for surveys and interviews

8. KNOWN LIMITATIONS
   - Data coverage gaps
   - LLM extraction uncertainty
   - Sources not yet included

9. APPENDIX
   - Full opportunity scoring table
   - Config used for this run
```

**Output file:** `reports/output/discovery_report_YYYY-MM-DD.md`

---

### `main.py` — Pipeline Orchestrator

```python
def main():
    # Phase 1: Collection
    run_collector("1.1")       # Play Store collection
    run_collector("1.2")       # App Store collection
    run_collector("1.3")       # Reddit collection

    # Phase 2: Processing
    run_cleaner()              # Clean all raw files
    run_normalizer()           # Unify into one schema

    # Phase 3: Relevance Filtering
    run_keyword_filter()       # Keyword scoring
    run_semantic_filter()      # Embedding-based scoring

    # Phase 4: AI Extraction
    run_ai_extractor()         # Groq API calls

    # Phase 5: Analysis
    run_signal_aggregator()    # Count and group signals
    run_pattern_discovery()    # Identify behavioral chains

    # Phase 6: Opportunities
    run_opportunity_finder()   # Generate opportunity statements

    # Phase 7: Scoring
    run_opportunity_scorer()   # Score and rank opportunities

    # Phase 8: Report
    run_report_generator()     # Generate final discovery report
```

Each phase can also be run independently via CLI flags:
```bash
# Run specific data collectors
python main.py --phase 1.1     # Google Play Store collection
python main.py --phase 1.2     # Apple App Store collection
python main.py --phase 1.3     # Reddit collection

# Run all collections
python main.py --phase 1

# Run other phases
python main.py --phase 3       # Run only relevance filtering
python main.py --from-phase 4  # Run from AI extraction onwards
```

---

## ⚡ Technology Stack

| Layer | Tool | Reason |
|---|---|---|
| **Language** | Python 3.10+ | Core language |
| **Play Store Scraping** | `google-play-scraper` | Free, maintained Python lib |
| **App Store Scraping** | `app-store-scraper` | Free Python lib / iTunes RSS |
| **Reddit API** | `PRAW` | Official Python Reddit API wrapper |
| **Data Processing** | `pandas` | Cleaning and normalization |
| **Text Cleaning** | `beautifulsoup4`, `re` | HTML removal, regex patterns |
| **Semantic Filtering** | `sentence-transformers` | Local free embedding model |
| **Embedding Model** | `all-MiniLM-L6-v2` | Fast, accurate, runs locally |
| **LLM API** | Groq API (free tier) | Structured extraction |
| **LLM Model** | `llama-3-70b-8192` | High quality, free tier available |
| **Config Management** | JSON files in `config/` | Human-readable, version-controllable |
| **Secrets** | `python-dotenv` | Secure credential loading |
| **Storage** | Local JSON files | Zero cost, no external dependencies |
| **Logging** | Python `logging` module | Centralized, configurable |

---

## 🧪 Configuration Reference

### `config/settings.json`

```json
{
  "collection": {
    "play_store_max_reviews": 5000,
    "app_store_max_reviews": 500,
    "reddit_max_posts_per_query": 100,
    "reddit_max_comments_per_post": 50
  },
  "cleaning": {
    "min_text_length": 20,
    "max_text_length": 10000
  },
  "relevance": {
    "keyword_weight": 0.4,
    "semantic_weight": 0.6,
    "relevance_threshold": 0.45,
    "embedding_model": "all-MiniLM-L6-v2"
  },
  "ai_extraction": {
    "groq_model": "llama-3-70b-8192",
    "batch_size": 10,
    "max_retries": 3,
    "retry_delay_seconds": 5
  },
  "scoring": {
    "frequency_weight": 0.25,
    "severity_weight": 0.25,
    "workaround_weight": 0.20,
    "metric_relevance_weight": 0.20,
    "evidence_strength_weight": 0.10
  }
}
```

---

## 🔗 Inter-Phase Interface Contracts

| From → To | File | Format |
|---|---|---|
| Phase 1 → Phase 2 | `data/raw/*.json` | Array of source-specific records |
| Phase 2 → Phase 3 | `data/normalized/unified_dataset.json` | Array of canonical schema records |
| Phase 3 → Phase 4 | `data/relevant/relevant_records.json` | Canonical records + relevance scores |
| Phase 4 → Phase 5 | `data/extracted/extracted_signals.json` | Canonical records + LLM extraction JSON |
| Phase 5 → Phase 6 | In-memory / intermediate JSON | Signal frequency + co-occurrence maps |
| Phase 6 → Phase 7 | In-memory / intermediate JSON | Opportunity statements |
| Phase 7 → Phase 8 | In-memory / intermediate JSON | Scored + ranked opportunities |
| Phase 8 → User | `reports/output/discovery_report_DATE.md` | Human-readable research report |

---

## 🚧 Future Extension Points

The modular architecture supports these extensions **without changing existing code**:

| Extension | Where to add |
|---|---|
| New data source (YouTube, Quora) | New module in `collectors/` implementing `BaseCollector` |
| New keyword group | Add to `config/keyword_lists.json` |
| New embedding model | Change `embedding_model` in `config/settings.json` |
| New LLM provider | New class in `ai/` implementing the extractor interface |
| Dashboard / UI | Read from `data/extracted/` and `reports/output/` |
| Database storage | Replace `utils/file_io.py` JSON operations with DB calls |
| Scheduled pipeline runs | Wrap `main.py` in a cron job or task scheduler |

---

*Last updated: 2026-08-27 | Sources: context.md + Problem_statement.txt*
