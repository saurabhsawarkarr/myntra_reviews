# 🏛️ Architecture — Myntra Review AI Discovery Engine

## 🔀 Hybrid Data Strategy
- **Play Store & App Store:** Static Dataset Loading (from Kaggle, AppAnnie, etc.). Bypasses live API scraping for speed and reliability.
- **Reddit:** Live API Fetching (via PRAW) to capture the latest, highly-specific fashion discussions.

## 🔄 Data Flow

```
PHASE 1: COLLECTION
┌────────────────┐      ┌───────────────┐
│ Manual CSV/JSON│      │ Live Reddit   │
│ (App/Play Store│      │ API (PRAW)    │
└───────┬────────┘      └───────┬───────┘
        │                       │
        ↓                       ↓
  data/raw/*.csv        data/raw/reddit.json

PHASE 2: NORMALIZATION
┌───────────────────────────────────────┐
│ normalizer.py reads both CSV and JSON │
│ and standardizes to Canonical Schema  │
└───────────────────────────────────────┘
```
