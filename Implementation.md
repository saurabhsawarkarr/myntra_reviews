# 🚀 Implementation Plan — Myntra Review AI Discovery Engine (Hybrid Approach)

> **Architecture Pivot:** Phase 1 (Data Collection) uses a Hybrid Strategy. 
> - Google Play and Apple App Store data will be loaded from static CSV/JSON files in `data/raw/`.
> - Reddit data will be fetched live via PRAW API.

---

## 📡 PHASE 1: Data Collection & Static Loading

### Sub-Phase 1.1: Static Data Loader (Play Store & App Store)
**File:** `collectors/static_loaders/app_store_loader.py`
Instead of scraping, this script validates and copies manually downloaded CSV/JSON datasets into our pipeline.

```python
import os, shutil
from utils.logger import get_logger

class StaticDataLoader:
    def __init__(self):
        self.logger = get_logger("static_loader")
        self.expected_files = ["play_store_static.csv", "app_store_static.csv"]

    def run(self):
        self.logger.info("Verifying static dataset presence...")
        for filename in self.expected_files:
            source = os.path.join("data/external", filename)
            dest = os.path.join("data/raw", filename)
            if os.path.exists(source):
                shutil.copy(source, dest)
                self.logger.info(f"Loaded {filename} into data/raw/")
            else:
                self.logger.warning(f"Missing {filename} in data/external/")
```

### Sub-Phase 1.2: Reddit Collector (Live Fetch)
**File:** `collectors/reddit/reddit_collector.py`
Connects to Reddit using PRAW and queries live subreddits based on `search_queries.json`.

```python
import praw, json
from utils.env_loader import get_env
from utils.logger import get_logger

class RedditCollector:
    def run(self):
        logger = get_logger("reddit_collector")
        logger.info("Fetching Reddit data via API...")
        # PRAW fetching logic goes here
        # Output saved to data/raw/reddit_data.json
```

---

## 🧹 PHASE 2: Cleaning & Normalization

**File:** `processors/normalizer.py`
Because the app store data now comes from CSVs, the normalizer must parse CSVs into standard JSON dictionaries before applying our canonical schema.

```python
import pandas as pd
import json

def run_normalization():
    records = []
    # 1. Read static CSVs (Play Store, App Store)
    if os.path.exists("data/raw/play_store_static.csv"):
        df_play = pd.read_csv("data/raw/play_store_static.csv")
        records.extend(df_play.to_dict(orient="records"))
    
    # 2. Read live JSON (Reddit)
    if os.path.exists("data/raw/reddit_data.json"):
        with open("data/raw/reddit_data.json", "r") as f:
            records.extend(json.load(f))
            
    # Normalize to canonical schema
    # Save to data/normalized/unified_dataset.json
```

---

## 🏃 Orchestrator (`main.py`)

```python
import argparse
from collectors.static_loaders.app_store_loader import StaticDataLoader
from collectors.reddit.reddit_collector import RedditCollector

def run_phase(phase: str):
    if phase == "1.1":
        StaticDataLoader().run()
    elif phase == "1.2":
        RedditCollector().run()
    elif phase == "1":
        run_phase("1.1")
        run_phase("1.2")
    elif phase == "2":
        # run normalization
        pass
    # ... remaining phases 3-8

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=str)
    args = parser.parse_args()
    if args.phase:
        run_phase(args.phase)
```
