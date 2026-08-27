# 🚀 Implementation Plan — Myntra Review AI Discovery Engine

> **Purpose of this file:** Phase-wise, step-by-step implementation guide. Each phase covers: objective, prerequisites, files to create, exact code structure, expected outputs, and validation checks.

---

## 📋 Pre-Implementation Checklist

- [ ] Python 3.10+ installed
- [ ] Reddit Developer account created at https://www.reddit.com/prefs/apps
- [ ] Groq API account created at https://console.groq.com (free tier)
- [ ] Git initialized in the project folder
- [ ] `.gitignore` includes `.env` and `data/`

---

## 🔐 Environment Setup

### Step 1 — Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
```

### Step 2 — Create `.env` file (never commit this)

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MyResearchBot/1.0 by YourUsername
GROQ_API_KEY=your_groq_api_key_here
```

### Step 3 — Create `.env.example` (safe to commit)

```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
GROQ_API_KEY=
```

### Step 4 — Create `.gitignore`

```gitignore
.env
venv/
data/raw/
data/cleaned/
data/normalized/
data/relevant/
data/extracted/
__pycache__/
*.pyc
reports/output/
```

---

## 📦 PHASE 0 — Project Setup & Architecture

### Objective
Create the full project skeleton with all folders, config files, and shared utilities before writing any phase-specific logic.

### Install base dependencies

```bash
pip install python-dotenv requests
```

---

### Files to Create

#### `utils/env_loader.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, required: bool = True) -> str:
    value = os.getenv(key)
    if required and not value:
        raise EnvironmentError(f"Missing required environment variable: {key}")
    return value
```

#### `utils/logger.py`
```python
import logging, sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

#### `utils/file_io.py`
```python
import json
from pathlib import Path

def load_json(path: str) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: list | dict, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_config(filename: str) -> dict:
    import os
    return load_json(os.path.join("config", filename))
```

#### `collectors/base_collector.py`
```python
from abc import ABC, abstractmethod
from utils.file_io import save_json
from utils.logger import get_logger

class BaseCollector(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def collect(self) -> list[dict]:
        pass

    @abstractmethod
    def validate(self, record: dict) -> bool:
        pass

    def save(self, records: list[dict], output_path: str) -> None:
        save_json(records, output_path)
        self.logger.info(f"Saved {len(records)} records to {output_path}")

    def summarize(self, records: list[dict]) -> dict:
        return {
            "total_collected": len(records),
            "valid_records": sum(1 for r in records if self.validate(r)),
        }
```

---

#### `config/settings.json`
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

#### `config/search_queries.json`
```json
[
  "Myntra", "Myntra wishlist", "Myntra saved items", "Myntra shopping experience",
  "Myntra size", "Myntra fit", "Myntra quality", "Myntra reviews",
  "Myntra alternatives", "Myntra discount", "online fashion shopping India",
  "buying clothes online India", "fashion shopping size issue", "online shopping fit problem"
]
```

#### `config/subreddits.json`
```json
["india", "indianfashion", "IndiaShopping", "AskIndia", "TwoXIndia", "FashionAdvice", "femalefashionadvice", "onlineshopping"]
```

#### `config/keyword_lists.json`
```json
{
  "wishlist_saving": ["wishlist", "wish list", "saved", "save for later", "shortlisted", "shortlist", "kept aside", "bookmarked", "saved items"],
  "purchase_intent": ["wanted to buy", "planning to buy", "thinking of buying", "buy later", "purchase later"],
  "purchase_delay": ["wait", "waiting", "postpone", "later", "couldn't decide", "not buying yet", "holding off"],
  "uncertainty": ["confused", "not sure", "uncertain", "doubt", "couldn't decide", "can't decide", "unsure"],
  "fashion_signals": ["size", "fit", "quality", "material", "colour", "color", "style", "look", "price", "discount", "sale", "review", "fabric"],
  "external_info": ["youtube", "instagram", "reddit", "asked friends", "other website", "offline store", "checked online"]
}
```

### Phase 0 Validation
- [ ] All folders and config files created
- [ ] `utils/` modules import without errors
- [ ] `python main.py --phase 1` runs without import errors


---

## 📡 PHASE 1 — Multi-Source Data Collection

### Objective
Collect raw public feedback from Google Play Store, Apple App Store, and Reddit. **No AI analysis in this phase.**

### Flow
```
CONNECT → COLLECT → VALIDATE BASIC FIELDS → STORE RAW DATA
```

### Install dependencies

```bash
pip install google-play-scraper app-store-scraper praw
```

Add to `requirements.txt`:
```
google-play-scraper>=1.2.4
app-store-scraper>=0.3.5
praw>=7.7.1
```

---

### Sub-Phase 1.1 — Google Play Store Collector

**File:** `collectors/play_store/play_store_collector.py`

```python
from google_play_scraper import reviews, Sort
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
import uuid, time

class PlayStoreCollector(BaseCollector):
    APP_ID = "com.myntra.android"
    OUTPUT_PATH = "data/raw/play_store_reviews.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        max_reviews = settings["collection"]["play_store_max_reviews"]
        result, continuation_token = reviews(
            self.APP_ID, lang="en", country="in",
            sort=Sort.NEWEST, count=200
        )
        all_reviews = list(result)
        while continuation_token and len(all_reviews) < max_reviews:
            result, continuation_token = reviews(
                self.APP_ID, continuation_token=continuation_token, count=200
            )
            all_reviews.extend(result)
            time.sleep(1)
        return [self._normalize(r) for r in all_reviews[:max_reviews]]

    def _normalize(self, raw: dict) -> dict:
        return {
            "id": f"play_{raw.get('reviewId', uuid.uuid4().hex)}",
            "source": "google_play",
            "source_type": "app_review",
            "platform": "Myntra",
            "title": None,
            "text": raw.get("content"),
            "rating": raw.get("score"),
            "date": str(raw.get("at", ""))[:10],
            "url": None,
            "metadata": {
                "app_version": raw.get("appVersion"),
                "thumbs_up_count": raw.get("thumbsUpCount", 0),
                "user_name": raw.get("userName")
            }
        }

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Google Play Store collection...")
        records = self.collect()
        self.save(records, self.OUTPUT_PATH)
        return self.summarize(records)
```

---

### Sub-Phase 1.2 — Apple App Store Collector

**File:** `collectors/app_store/app_store_collector.py`

```python
from app_store_scraper import AppStore
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
import uuid

class AppStoreCollector(BaseCollector):
    APP_NAME = "myntra"
    APP_ID = "1038311274"
    COUNTRY = "in"
    OUTPUT_PATH = "data/raw/app_store_reviews.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        max_reviews = settings["collection"]["app_store_max_reviews"]
        app = AppStore(country=self.COUNTRY, app_name=self.APP_NAME, app_id=self.APP_ID)
        app.review(how_many=max_reviews)
        return [self._normalize(r) for r in app.reviews]

    def _normalize(self, raw: dict) -> dict:
        return {
            "id": f"app_{raw.get('id', uuid.uuid4().hex)}",
            "source": "apple_app_store",
            "source_type": "app_review",
            "platform": "Myntra",
            "title": raw.get("title"),
            "text": raw.get("review"),
            "rating": raw.get("rating"),
            "date": str(raw.get("date", ""))[:10],
            "url": None,
            "metadata": {
                "app_version": raw.get("version"),
                "user_name": raw.get("userName")
            }
        }

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Apple App Store collection...")
        records = self.collect()
        self.save(records, self.OUTPUT_PATH)
        return self.summarize(records)
```

---

### Sub-Phase 1.3 — Reddit Collector

**File:** `collectors/reddit/reddit_collector.py`

```python
import praw, uuid
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
from utils.env_loader import get_env

class RedditCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/reddit_data.json"

    def _get_client(self):
        return praw.Reddit(
            client_id=get_env("REDDIT_CLIENT_ID"),
            client_secret=get_env("REDDIT_CLIENT_SECRET"),
            user_agent=get_env("REDDIT_USER_AGENT")
        )

    def collect(self) -> list[dict]:
        reddit = self._get_client()
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        subreddits = load_config("subreddits.json")
        max_posts = settings["collection"]["reddit_max_posts_per_query"]
        max_comments = settings["collection"]["reddit_max_comments_per_post"]

        records, seen_ids = [], set()

        for query in queries:
            self.logger.info(f"Searching: {query}")
            for post in reddit.subreddit("all").search(query, limit=max_posts):
                if post.id in seen_ids: continue
                seen_ids.add(post.id)
                records.append(self._normalize_post(post))
                records.extend(self._get_comments(post, max_comments, seen_ids))

        for sub in subreddits:
            try:
                for post in reddit.subreddit(sub).new(limit=max_posts):
                    if post.id in seen_ids: continue
                    seen_ids.add(post.id)
                    records.append(self._normalize_post(post))
                    records.extend(self._get_comments(post, max_comments, seen_ids))
            except Exception as e:
                self.logger.warning(f"Could not access r/{sub}: {e}")

        return records

    def _normalize_post(self, post) -> dict:
        return {
            "id": f"reddit_post_{post.id}",
            "source": "reddit",
            "source_type": "reddit_post",
            "platform": "Myntra",
            "title": post.title,
            "text": post.selftext or post.title,
            "rating": None,
            "date": str(post.created_utc)[:10],
            "url": f"https://reddit.com{post.permalink}",
            "metadata": {"subreddit": str(post.subreddit), "score": post.score, "num_comments": post.num_comments}
        }

    def _get_comments(self, post, max_comments, seen_ids) -> list[dict]:
        comments = []
        try:
            post.comments.replace_more(limit=0)
            for c in post.comments.list()[:max_comments]:
                if c.id in seen_ids: continue
                seen_ids.add(c.id)
                comments.append({
                    "id": f"reddit_comment_{c.id}",
                    "source": "reddit",
                    "source_type": "reddit_comment",
                    "platform": "Myntra",
                    "title": None,
                    "text": c.body,
                    "rating": None,
                    "date": str(c.created_utc)[:10],
                    "url": f"https://reddit.com{c.permalink}",
                    "metadata": {"subreddit": str(c.subreddit), "score": c.score, "parent_id": f"reddit_post_{post.id}"}
                })
        except Exception as e:
            self.logger.warning(f"Comment error on post {post.id}: {e}")
        return comments

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Reddit collection...")
        records = self.collect()
        self.save(records, self.OUTPUT_PATH)
        return self.summarize(records)
```

### Phase 1 — Expected Output

```
data/raw/
  play_store_reviews.json   ← raw Play Store records
  app_store_reviews.json    ← raw App Store records
  reddit_data.json          ← raw posts + comments with parent_id
```

**Collection summary to log:**
```
Google Play reviews collected: X
Apple App Store reviews collected: X
Reddit posts collected: X
Reddit comments collected: X
Errors: X | Duplicates skipped: X
```

### Phase 1 Validation
- [ ] All three raw files exist and contain records
- [ ] Reddit comments have `parent_id` in metadata
- [ ] All records have `id`, `source`, `text` populated
- [ ] No credentials hardcoded in any source file


---

## 🧹 PHASE 2 — Cleaning & Normalization

### Objective
Convert raw multi-source data into a clean, consistent unified dataset. **No LLM required.**

### Install dependencies

```bash
pip install pandas beautifulsoup4
```

---

### `processors/cleaner.py`

```python
import re, pandas as pd
from bs4 import BeautifulSoup
from utils.file_io import load_json, save_json, load_config
from utils.logger import get_logger

logger = get_logger("cleaner")

def clean_text(text: str) -> str:
    if not text: return ""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    return text.replace('\x00', '')

def is_spam(text: str) -> bool:
    patterns = [r'(.)\1{10,}', r'^[^a-zA-Z]*$']
    return any(re.search(p, text) for p in patterns)

def clean_records(records: list[dict], settings: dict) -> list[dict]:
    min_len = settings["cleaning"]["min_text_length"]
    max_len = settings["cleaning"]["max_text_length"]
    cleaned, seen_texts, seen_ids = [], set(), set()
    stats = {"duplicates": 0, "empty": 0, "spam": 0, "too_short": 0, "kept": 0}

    for record in records:
        rid = record.get("id")
        text = clean_text(record.get("text", ""))
        if rid in seen_ids: stats["duplicates"] += 1; continue
        if not text: stats["empty"] += 1; continue
        if text in seen_texts: stats["duplicates"] += 1; continue
        if len(text) < min_len: stats["too_short"] += 1; continue
        if is_spam(text): stats["spam"] += 1; continue
        seen_ids.add(rid); seen_texts.add(text)
        record["text"] = text[:max_len]
        cleaned.append(record); stats["kept"] += 1

    logger.info(f"Cleaning stats: {stats}")
    return cleaned
```

---

### `processors/normalizer.py`

```python
from utils.file_io import load_json, save_json
from utils.logger import get_logger

logger = get_logger("normalizer")

def normalize_record(record: dict) -> dict:
    return {
        "id": record.get("id"),
        "source": record.get("source"),
        "source_type": record.get("source_type"),
        "platform_mentioned": record.get("platform", "Myntra"),
        "title": record.get("title"),
        "text": record.get("text"),
        "rating": record.get("rating"),
        "date": record.get("date"),
        "url": record.get("url"),
        "metadata": record.get("metadata", {})
    }

def run_normalization(input_paths: list[str], output_path: str):
    all_records = []
    for path in input_paths:
        all_records.extend(load_json(path))
    normalized = [normalize_record(r) for r in all_records]
    save_json(normalized, output_path)
    logger.info(f"Normalized {len(normalized)} records → {output_path}")
    return normalized
```

**Canonical Schema (all sources → one format):**
```json
{
  "id": "unique_record_id",
  "source": "google_play | apple_app_store | reddit",
  "source_type": "app_review | reddit_post | reddit_comment",
  "platform_mentioned": "Myntra",
  "title": "string or null",
  "text": "cleaned text",
  "rating": "1-5 or null",
  "date": "YYYY-MM-DD or null",
  "url": "string or null",
  "metadata": {}
}
```

### Phase 2 — Expected Output
```
data/normalized/unified_dataset.json   ← all sources merged into one schema
```

### Phase 2 Validation
- [ ] `data/normalized/unified_dataset.json` exists
- [ ] No record has empty `text` field
- [ ] All dates in `YYYY-MM-DD` format
- [ ] Raw files in `data/raw/` are UNCHANGED (verify file size)

---

## 🔍 PHASE 3 — Relevance Filtering

### Objective
From thousands of records, identify conversations relevant to our research problem using keyword + semantic filtering. **No LLM required.**

### Install dependencies

```bash
pip install sentence-transformers scikit-learn torch
```

---

### `processors/relevance/keyword_filter.py`

```python
from utils.file_io import load_config
from utils.logger import get_logger

logger = get_logger("keyword_filter")

def compute_keyword_score(text: str, keyword_groups: dict) -> tuple[float, list[str]]:
    text_lower = text.lower()
    matched_groups = [g for g, kws in keyword_groups.items() if any(kw in text_lower for kw in kws)]
    score = len(matched_groups) / len(keyword_groups)
    return round(score, 4), matched_groups

def run_keyword_filter(records: list[dict]) -> list[dict]:
    keyword_groups = load_config("keyword_lists.json")
    for record in records:
        score, matched = compute_keyword_score(record["text"], keyword_groups)
        record["keyword_score"] = score
        record["keyword_matched_groups"] = matched
    return records
```

---

### `processors/relevance/semantic_filter.py`

```python
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
    texts = [r["text"] for r in records]
    logger.info(f"Encoding {len(texts)} records...")
    record_embeddings = model.encode(texts, convert_to_tensor=True, batch_size=64, show_progress_bar=True)

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
```

**Final Relevance Score Formula:**
```
final_relevance_score = (keyword_weight × keyword_score) + (semantic_weight × semantic_score)
Default weights: keyword=0.4, semantic=0.6
Default threshold: 0.45
```

### Phase 3 — Expected Output
```
data/relevant/relevant_records.json
  ← records with keyword_score, semantic_score, final_relevance_score, relevance_reason
```

### Phase 3 Validation
- [ ] Records have all relevance score fields
- [ ] Spot-check 10 records — do they feel relevant to wishlist/purchase behavior?
- [ ] If fewer than 5% of records pass, lower the threshold in `settings.json`

---

## 🤖 PHASE 4 — AI-Powered Information Extraction

### Objective
Use Groq LLM to extract structured behavioral signals from each relevant record.

### Install dependencies

```bash
pip install groq
```

---

### `ai/prompts/system_prompt.txt`
```
You are a behavioral research analyst. Extract structured information from user reviews about online fashion shopping.

RULES:
1. Only extract what is explicitly stated or very strongly implied.
2. Use "unknown" for any field you cannot determine.
3. Never invent motivations.
4. Do not assume every saved product = purchase intent.
5. Return ONLY valid JSON. No text before or after.
```

### `ai/prompts/extraction_prompt.txt`
```
Analyze the following user review or post about online fashion shopping.

TEXT:
{text}

Return this JSON structure:
{
  "is_relevant": true/false,
  "wishlist_behavior": {"detected": true/false, "type": "potential_purchase|bookmarking|comparison|waiting_for_sale|unknown", "confidence": 0.0-1.0},
  "motivation": ["liked_design|good_price|trending_style|recommendation|unknown"],
  "uncertainties": ["size|fit|quality|material|color|style|price|reviews|unknown"],
  "purchase_blockers": ["low_fit_confidence|price_too_high|conflicting_reviews|no_discount|lack_of_information|unknown"],
  "user_actions": ["searched_external_information|compared_products|visited_offline_store|ordered_multiple_sizes|waited_for_sale|asked_friend|unknown"],
  "external_information_sources": ["Instagram|YouTube|Reddit|friend|other_website|offline_store|unknown"],
  "outcome": "purchased|postponed|abandoned|alternative_purchased|unknown",
  "evidence_spans": ["exact phrases from text supporting your extraction"]
}
```

---

### `ai/extractor.py`

```python
import json
from groq import Groq
from pathlib import Path
from utils.env_loader import get_env
from utils.logger import get_logger

logger = get_logger("extractor")

def load_prompt(filename: str) -> str:
    return (Path("ai/prompts") / filename).read_text(encoding="utf-8")

def extract_signals(record: dict, client: Groq, model: str) -> dict:
    system_prompt = load_prompt("system_prompt.txt")
    user_prompt = load_prompt("extraction_prompt.txt").replace("{text}", record["text"])
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1, max_tokens=1024
        )
        return json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error for {record['id']}: {e}")
        return {"is_relevant": False, "error": "json_parse_error"}
    except Exception as e:
        logger.warning(f"API error for {record['id']}: {e}")
        return {"is_relevant": False, "error": str(e)}
```

---

### `ai/batch_processor.py`

```python
import time
from ai.extractor import extract_signals
from groq import Groq
from utils.env_loader import get_env
from utils.file_io import load_config, load_json, save_json
from utils.logger import get_logger

logger = get_logger("batch_processor")

def run_extraction(input_path: str, output_path: str):
    records = load_json(input_path)
    settings = load_config("settings.json")
    model = settings["ai_extraction"]["groq_model"]
    batch_size = settings["ai_extraction"]["batch_size"]
    max_retries = settings["ai_extraction"]["max_retries"]
    retry_delay = settings["ai_extraction"]["retry_delay_seconds"]

    client = Groq(api_key=get_env("GROQ_API_KEY"))
    results, failed = [], []

    for i, record in enumerate(records):
        logger.info(f"Processing {i+1}/{len(records)}: {record['id']}")
        signals = {}
        for attempt in range(max_retries):
            signals = extract_signals(record, client, model)
            if "error" not in signals: break
            logger.warning(f"Retry {attempt+1}/{max_retries}")
            time.sleep(retry_delay * (attempt + 1))

        if "error" in signals:
            failed.append(record["id"])
        else:
            results.append({**record, "extracted_signals": signals})

        if (i + 1) % batch_size == 0:
            logger.info("Batch done. Sleeping 2s...")
            time.sleep(2)

    save_json(results, output_path)
    logger.info(f"Done. Success: {len(results)}, Failed: {len(failed)}")
    if failed: logger.warning(f"Failed IDs: {failed}")
```

**Critical LLM Rules enforced in system prompt:**
- Only extract explicitly stated information
- Use `"unknown"` when uncertain
- Never invent motivations
- Do not assume saved product = purchase intent

### Phase 4 — Expected Output
```
data/extracted/extracted_signals.json
  ← original records + extracted_signals JSON field per record
```

### Phase 4 Validation
- [ ] Each record has `extracted_signals` key with valid JSON
- [ ] Spot-check 10 records: does extracted JSON match the actual text?
- [ ] `evidence_spans` contain real quotes from the text
- [ ] `is_relevant: false` records contain empty arrays, not invented data


---

## 📊 PHASE 5 — Signal Aggregation & Pattern Discovery

### Objective
Combine extracted signals across all conversations to count frequency, find co-occurrences, and identify behavioral chains.

---

### `analysis/signal_aggregator.py`

```python
from collections import Counter, defaultdict
from utils.file_io import load_json, save_json
from utils.logger import get_logger

logger = get_logger("signal_aggregator")

def aggregate_signals(records: list[dict]) -> dict:
    uncertainty_counts, blocker_counts = Counter(), Counter()
    action_counts, source_counts, outcome_counts = Counter(), Counter(), Counter()
    source_signal_map = defaultdict(Counter)

    for record in records:
        signals = record.get("extracted_signals", {})
        source = record.get("source", "unknown")

        for u in signals.get("uncertainties", []):
            if u != "unknown":
                uncertainty_counts[u] += 1
                source_signal_map[source][f"uncertainty:{u}"] += 1

        for b in signals.get("purchase_blockers", []):
            if b != "unknown": blocker_counts[b] += 1

        for a in signals.get("user_actions", []):
            if a != "unknown": action_counts[a] += 1

        for s in signals.get("external_information_sources", []):
            if s != "unknown": source_counts[s] += 1

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
```

---

### `analysis/pattern_discovery.py`

```python
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
                "record_id": record["id"],
                "chain": {
                    "interest": True,
                    "uncertainties": uncertainties,
                    "external_search": "searched_external_information" in actions,
                    "outcome": outcome
                }
            })
    return chains
```

**Pattern Analysis Dimensions:**

| Dimension | Description |
|---|---|
| Frequency | How often does each signal appear? |
| Co-occurrence | Which signals appear together? |
| Behavioral chains | Interest → Uncertainty → External Search → Delay/Abandon |
| Source comparison | Does the same pattern appear across Play Store, App Store, Reddit? |

### Phase 5 Validation
- [ ] Signal frequencies make sense (size/fit should rank high)
- [ ] Co-occurrences show logical pairs (size + fit uncertainty together)
- [ ] Behavioral chains capture interest → uncertainty → action → outcome flow

---

## 💡 PHASE 6 — Opportunity Discovery

### Objective
Convert repeated signals into named opportunity areas representing potential underlying unmet needs.

**The result format is NOT:** `Problem: Size`

**It IS:**
```
SIGNALS: Size uncertainty + Fit uncertainty + Conflicting reviews
    ↓
POTENTIAL UNDERLYING NEED:
Users lack sufficient confidence to predict how a fashion product will fit before purchasing.
```

> All opportunity statements are **evidence-backed hypotheses** — not final conclusions.

---

### `analysis/opportunity_finder.py`

```python
from utils.logger import get_logger

logger = get_logger("opportunity_finder")

OPPORTUNITY_TEMPLATES = [
    {
        "name": "Fit & Size Confidence Gap",
        "signal_triggers": ["uncertainty:size", "uncertainty:fit", "blocker:low_fit_confidence"],
        "opportunity_statement": (
            "Users lack sufficient confidence to predict how a fashion product will fit "
            "and look on their body before purchasing, leading to purchase delays or abandonment."
        )
    },
    {
        "name": "Price Timing & Sale Awareness",
        "signal_triggers": ["blocker:price_too_high", "action:waited_for_sale", "uncertainty:price"],
        "opportunity_statement": (
            "Users interested in a product postpone purchase while waiting for discounts, "
            "with no in-app support for this waiting behavior."
        )
    },
    {
        "name": "Review Quality & Trustworthiness",
        "signal_triggers": ["blocker:conflicting_reviews", "blocker:lack_of_information"],
        "opportunity_statement": (
            "Users cannot confidently evaluate product quality from existing reviews due "
            "to conflicting information, prompting them to seek external validation."
        )
    },
    {
        "name": "External Information Seeking",
        "signal_triggers": ["action:searched_external_information"],
        "opportunity_statement": (
            "Users leave the platform to search Instagram, YouTube, or Reddit before deciding, "
            "indicating unmet information needs within the app."
        )
    }
]

def find_opportunities(records: list[dict]) -> list[dict]:
    opportunities = []
    for template in OPPORTUNITY_TEMPLATES:
        supporting_ids, quotes = [], []
        for record in records:
            signals = record.get("extracted_signals", {})
            all_signals = (
                [f"uncertainty:{u}" for u in signals.get("uncertainties", []) if u != "unknown"] +
                [f"blocker:{b}" for b in signals.get("purchase_blockers", []) if b != "unknown"] +
                [f"action:{a}" for a in signals.get("user_actions", []) if a != "unknown"]
            )
            if any(t in all_signals for t in template["signal_triggers"]):
                supporting_ids.append(record["id"])
                quotes.extend(signals.get("evidence_spans", []))

        if supporting_ids:
            opportunities.append({
                "name": template["name"],
                "opportunity_statement": template["opportunity_statement"],
                "supporting_record_count": len(supporting_ids),
                "supporting_record_ids": supporting_ids,
                "representative_quotes": list(set(quotes))[:5],
                "classification": "evidence-backed hypothesis"
            })
    return opportunities
```

### Phase 6 Validation
- [ ] At least 2-4 opportunity areas generated
- [ ] Each has supporting record IDs and representative quotes
- [ ] Statements feel grounded in actual data

---

## 📏 PHASE 7 — Quantify & Compare Opportunities

### Objective
Score each opportunity on 5 dimensions and rank them by composite score.

**The 5 Scoring Dimensions:**

| Dimension | Calculation |
|---|---|
| Frequency | Supporting records / Total relevant records |
| Severity | Avg outcome severity (1=purchased → 5=abandoned) |
| Workaround Rate | Records with actions / Records with the issue |
| Metric Relevance | Heuristic based on severity (High/Medium/Low) |
| Evidence Strength | Cross-source > Multi-record > Single-record |

---

### `analysis/opportunity_scorer.py`

```python
from utils.file_io import load_config
from utils.logger import get_logger

logger = get_logger("opportunity_scorer")

OUTCOME_SEVERITY = {
    "purchased": 1, "postponed": 3,
    "abandoned": 5, "alternative_purchased": 4, "unknown": 2
}

def score_opportunities(opportunities: list[dict], records: list[dict], settings: dict) -> list[dict]:
    total = len(records)
    weights = settings["scoring"]

    for opp in opportunities:
        supporting = opp["supporting_record_count"]
        sup_records = [r for r in records if r["id"] in opp["supporting_record_ids"]]

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
        composite = (
            weights["frequency_weight"] * freq_score +
            weights["severity_weight"] * normalized_severity +
            weights["workaround_weight"] * workaround_rate
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
```

**Example Ranked Output:**

| Opportunity | Frequency | Severity | Workaround | Metric Rel. | Evidence | Score |
|---|---|---|---|---|---|---|
| Fit & Size Confidence Gap | High | 4.2 | 68% | High | Cross-source | 0.87 |
| Price Timing & Sale Awareness | High | 3.1 | 42% | High | Cross-source | 0.76 |
| External Information Seeking | Medium | 3.8 | 71% | Medium | Multi-record | 0.69 |
| Review Quality & Trust | Medium | 2.9 | 55% | Medium | Multi-record | 0.61 |

### Phase 7 Validation
- [ ] Each opportunity has all 5 dimension scores populated
- [ ] Opportunities are sorted by composite score (highest first)
- [ ] The "biggest" problems score highest — validates against intuition

---

## 📝 PHASE 8 — Discovery Report

### Objective
Generate a comprehensive, stakeholder-ready research report from all pipeline outputs.

---

### `reports/report_generator.py`

```python
from datetime import date
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("report_generator")

def generate_report(opportunities: list[dict], aggregated: dict, output_path: str):
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
            f"| Frequency Score | {opp['frequency_score']:.1%} |",
            f"| Severity (avg) | {opp['severity_avg']} / 5 |",
            f"| Workaround Rate | {opp['workaround_rate']:.1%} |",
            f"| Metric Relevance | {opp['metric_relevance']} |",
            f"| Evidence Strength | {opp['evidence_strength']} |",
            f"| Composite Score | {opp['composite_score']:.3f} |",
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

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Report saved: {output_path}")
```

**Report sections:**
1. Dataset Summary (total records, per source, signal counts)
2. Top Opportunity Areas (scores, quotes, behavioral chains)
3. Signal Frequency Analysis
4. Behavioral Patterns
5. Source Comparison (Play Store vs App Store vs Reddit)
6. Known Limitations
7. Research Hypotheses for interviews and surveys

### Phase 8 Validation
- [ ] `reports/output/discovery_report_YYYY-MM-DD.md` exists
- [ ] Report is readable and well-structured
- [ ] All opportunities appear with scores and evidence quotes
- [ ] Limitations and research hypotheses sections are present

---

## 🏃 Running the Pipeline

### `main.py` — Full Orchestrator

```python
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
        raw_paths = ["data/raw/play_store_reviews.json", "data/raw/app_store_reviews.json", "data/raw/reddit_data.json"]
        for path in raw_paths:
            records = load_json(path)
            cleaned = clean_records(records, settings)
            save_json(cleaned, path.replace("raw/", "cleaned/"))
        run_normalization([p.replace("raw/", "cleaned/") for p in raw_paths], "data/normalized/unified_dataset.json")

    elif phase == "3":
        from processors.relevance.keyword_filter import run_keyword_filter
        from processors.relevance.semantic_filter import load_model, compute_semantic_scores, compute_final_scores
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
```

### Run Commands

```bash
# Run full pipeline
python main.py

# Run single phase
python main.py --phase 1      # Collection only
python main.py --phase 3      # Relevance filtering only
python main.py --phase 4      # AI extraction only

# Resume from a phase (if previous run failed mid-way)
python main.py --from-phase 4
```

---

## 📦 Final `requirements.txt`

```
python-dotenv>=1.0.0
requests>=2.31.0
google-play-scraper>=1.2.4
app-store-scraper>=0.3.5
praw>=7.7.1
pandas>=2.0.0
beautifulsoup4>=4.12.0
sentence-transformers>=2.2.2
scikit-learn>=1.3.0
groq>=0.9.0
torch>=2.0.0
```

Install everything:
```bash
pip install -r requirements.txt
```

---

## ✅ Complete Implementation Checklist

### Phase 0 — Setup
- [ ] `venv` created and activated
- [ ] `.env` file with all 4 credentials
- [ ] All `config/*.json` files created and valid
- [ ] `utils/` modules import cleanly
- [ ] `base_collector.py` implemented

### Phase 1 — Collection
- [ ] Play Store collector fetches and saves data
- [ ] App Store collector fetches and saves data
- [ ] Reddit collector authenticates + fetches posts + comments with `parent_id`
- [ ] All three raw files in `data/raw/`

### Phase 2 — Cleaning
- [ ] Cleaner removes duplicates, empties, spam, short records
- [ ] Normalizer unifies all sources to canonical schema
- [ ] `data/normalized/unified_dataset.json` created
- [ ] Raw files unchanged

### Phase 3 — Relevance Filtering
- [ ] Keyword filter assigns scores to all records
- [ ] Sentence Transformers model loads locally without API key
- [ ] Semantic scores computed for all records
- [ ] `data/relevant/relevant_records.json` created with relevance metadata

### Phase 4 — AI Extraction
- [ ] Groq API key working
- [ ] Extraction prompt returns valid JSON
- [ ] Batch processor handles rate limits and retries gracefully
- [ ] `data/extracted/extracted_signals.json` created

### Phase 5 — Signals & Patterns
- [ ] Signal frequency counts computed
- [ ] Co-occurrences identified (top 20 pairs)
- [ ] Behavioral chains extracted and stored

### Phase 6 — Opportunities
- [ ] Opportunity areas generated with supporting record IDs
- [ ] Representative quotes attached to each opportunity

### Phase 7 — Scoring
- [ ] All 5 dimensions scored per opportunity
- [ ] Opportunities ranked by composite score
- [ ] `data/extracted/scored_opportunities.json` created

### Phase 8 — Report
- [ ] `reports/output/discovery_report_YYYY-MM-DD.md` generated
- [ ] Report contains all required sections
- [ ] Ready to share with stakeholders

---

*Last updated: 2026-08-27 | Sources: Architecture.md + context.md*
