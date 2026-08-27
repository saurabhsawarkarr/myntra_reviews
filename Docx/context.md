# 📦 Project Context — Myntra Review AI Discovery Engine

> **Purpose of this file:** This is the single source of truth for the entire project. Read this before writing any code, prompt, or pipeline step. Every module, data schema, and decision should align with what is described here.

---

## 🧭 Project Summary

**Project Name:** AI-Powered Discovery Engine for Wishlist-to-Purchase Drop-Off in Online Fashion Shopping

**Initial Product Focus:** Myntra

**Core Business Question:**
> How can we increase the conversion of users who add fashion products to their wishlist into users who purchase those products within 30 days?

This project builds an **AI-Powered Discovery Engine** that:
- Collects publicly available user feedback and discussions at scale
- Processes and filters them for research relevance
- Extracts structured behavioral signals using an LLM
- Discovers recurring patterns in user behavior
- Generates evidence-backed opportunity areas

---

## ❓ Primary Research Question

> **Why do users add or save fashion products but fail to purchase them, and what recurring unmet needs or opportunity areas may influence the conversion from product interest to purchase?**

### Wishlist Behavior
- Why do users save fashion products?
- Is the wishlist used for genuine purchase intent, bookmarking, comparison, or waiting for discounts?

### Purchase Blockers
- What prevents users from purchasing products they are interested in?
- What causes postponement?
- What uncertainties remain after identifying a product?

### Decision-Making Behavior
- How do users compare multiple products?
- What information do they seek before purchasing?
- What do they search for *outside* the platform?
- What workarounds do they use?

### Potential Uncertainty Areas (Not Assumptions — Detection Targets)
Size, Fit, Quality, Material, Actual Appearance, Styling, Price, Discounts, Product Reviews, Trust, Alternatives, Comparison, Social Validation

---

## 🏗️ System Architecture Overview

`
DATA SOURCES
    ┌──────────────┬──────────────┐
    ↓              ↓              ↓
Google Play    Apple App      Reddit
  Store          Store          API
    └──────────────┼──────────────┘
                   ↓
         PHASE 1: COLLECTION
                   ↓
           RAW DATA STORE
                   ↓
    PHASE 2: CLEANING & NORMALIZATION
                   ↓
           UNIFIED DATASET
                   ↓
     PHASE 3: RELEVANCE FILTERING
                   ↓
          RELEVANT DATASET
                   ↓
    PHASE 4: AI INFORMATION EXTRACTION
                   ↓
        STRUCTURED USER SIGNALS
                   ↓
       PHASE 5: PATTERN DISCOVERY
                   ↓
      PHASE 6: OPPORTUNITY DISCOVERY
                   ↓
       PHASE 7: QUANTIFY & COMPARE
                   ↓
       DISCOVERY REPORT / DASHBOARD
                   ↓
       SURVEYS + USER INTERVIEWS
                   ↓
       VALIDATED PRODUCT PROBLEM
                   ↓
          IDEATION + SOLUTION
`

---

## 🗂️ Project Directory Structure

`
ai-discovery-engine/
│
├── collectors/
│   ├── play_store/
│   ├── app_store/
│   └── reddit/
│
├── processors/
│   ├── cleaning/
│   ├── normalization/
│   └── relevance/
│
├── ai/
│   ├── extractor/
│   └── prompts/
│
├── analysis/
│   ├── signals/
│   ├── patterns/
│   └── opportunities/
│
├── data/
│   ├── raw/
│   ├── cleaned/
│   ├── normalized/
│   ├── relevant/
│   └── extracted/
│
├── reports/
├── config/
└── main.py
`

---

## ⚙️ Project Constraints

| Constraint | Detail |
|---|---|
| Budget | Free / open-source tools wherever possible |
| Language | Python + free/open-source libraries |
| Storage | Local storage (no paid databases) |
| AI API | Groq API (free tier) — use sparingly where LLM adds clear value |
| Scraping | No paid scraping platforms |
| Vector DB | No paid vector databases |

**Credentials (never hardcoded — use environment variables):**
`
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USER_AGENT
GROQ_API_KEY
`

---

## 📡 Data Sources (v1)

Only three sources for the first version:
1. **Google Play Store** — Myntra app reviews
2. **Apple App Store** — Myntra app reviews
3. **Reddit API** — posts and comments from relevant subreddits

> Additional sources (YouTube, fashion communities, social media) are deferred until the initial pipeline is proven.

---

## 🔄 Phase-by-Phase Build Specification

---

### PHASE 0 — Project Setup & Architecture

**Goal:** Create a modular architecture that supports adding new data sources without changing the entire system.

- Each module has a single responsibility
- Config files store search queries and subreddits (never hardcoded)

---

### PHASE 1 — Multi-Source Data Collection

**Goal:** Collect raw public feedback from the three sources. No AI analysis in this phase.

**Flow:** CONNECT → COLLECT → VALIDATE BASIC FIELDS → STORE RAW DATA

---

#### Sub-Phase 1.1 — Google Play Store Collector

**Output:** data/raw/play_store_reviews.json

**Required fields per record:**
review_id, source, platform, rating, review_text, review_date, user_name, app_version, thumbs_up_count

Example record:
```json
{
  "id": "play_123456",
  "source": "google_play",
  "source_type": "app_review",
  "platform": "Myntra",
  "text": "I saved the product but wasn't sure about the size.",
  "rating": 3,
  "date": "2026-08-20",
  "metadata": {
    "app_version": "5.0",
    "thumbs_up_count": 2
  }
}
```

---

#### Sub-Phase 1.2 — Apple App Store Collector

**Output:** data/raw/app_store_reviews.json

**Required fields per record:**
review_id, source, platform, rating, title, review_text, date, author, app_version

Example record:
```json
{
  "id": "app_123456",
  "source": "apple_app_store",
  "source_type": "app_review",
  "platform": "Myntra",
  "title": "Good app but confusing sizing",
  "text": "I like the products but I can never decide which size to buy.",
  "rating": 3,
  "date": "2026-08-20",
  "metadata": {}
}
```

---

#### Sub-Phase 1.3 — Reddit Collector

**Output:** data/raw/reddit_data.json

**Authentication:** Reddit API via PRAW (environment variables, never hardcoded)

**Search Queries** (stored in config/search_queries.json):
Myntra, Myntra wishlist, Myntra saved items, Myntra shopping experience, Myntra size, Myntra fit, Myntra quality, Myntra reviews, Myntra alternatives, Myntra discount, online fashion shopping India, buying clothes online India, fashion shopping size issue, online shopping fit problem

**Target Subreddits** (stored in config/subreddits.json):
Communities related to: Indian fashion, Indian shopping, Myntra, online shopping, fashion advice, clothing recommendations.

Post record example:
`json
{
  "id": "reddit_post_123",
  "source": "reddit",
  "source_type": "reddit_post",
  "title": "Question about buying clothes from Myntra",
  "text": "I have shortlisted several dresses but can't decide.",
  "date": "2026-08-20",
  "url": "source_url",
  "metadata": {
    "subreddit": "example_subreddit",
    "score": 42,
    "num_comments": 15
  }
}
`

Comment record example:
`json
{
  "id": "reddit_comment_456",
  "source": "reddit",
  "source_type": "reddit_comment",
  "parent_id": "reddit_post_123",
  "text": "I usually check Instagram or YouTube before buying.",
  "date": "2026-08-20",
  "url": "source_url",
  "metadata": {
    "subreddit": "example_subreddit",
    "score": 10
  }
}
`

---

#### Phase 1 Output Summary

Files:
- data/raw/play_store_reviews.json
- data/raw/app_store_reviews.json
- data/raw/reddit_data.json

Collection summary to generate:
- Google Play reviews collected: X
- Apple App Store reviews collected: X
- Reddit posts collected: X
- Reddit comments collected: X
- Collection errors: X
- Duplicate records skipped: X

---

### PHASE 2 — Cleaning & Normalization

**Goal:** Convert raw multi-source data into a clean, consistent dataset.

**Tools:** Python + Pandas + Regex + standard libraries (NO LLM required)

**Cleaning Tasks:**
- Remove duplicate records
- Remove empty records
- Normalize whitespace
- Remove unnecessary HTML
- Handle null values
- Standardize dates and source names
- Remove obvious spam
- Remove extremely short/meaningless records
- Preserve original text

> RULE: NEVER overwrite raw source data. Always create new processed files.

**Canonical Data Schema:**
`json
{
  "id": "unique_record_id",
  "source": "reddit",
  "source_type": "reddit_comment",
  "platform_mentioned": "Myntra",
  "title": null,
  "text": "Actual cleaned user feedback",
  "rating": null,
  "date": "2026-08-20",
  "url": "source_url",
  "metadata": {}
}
`

**Output:** data/normalized/unified_dataset.json

---

### PHASE 3 — Relevance Filtering

**Goal:** Identify conversations potentially relevant to the research problem.

**Approach:** Multi-stage filtering (keyword first, then semantic). No LLM required.

#### Layer 1 — Keyword Filtering

Wishlist/saving: wishlist, wish list, saved, save for later, shortlisted, shortlist, kept aside, bookmarked
Purchase intent: wanted to buy, planning to buy, thinking of buying, buy later, purchase later
Purchase delay: wait, waiting, postpone, later, couldn't decide, not buying yet
Uncertainty: confused, not sure, uncertain, doubt, couldn't decide
Fashion signals: size, fit, quality, material, colour, color, style, look, price, discount, sale, review
External info behavior: YouTube, Instagram, Reddit, asked friends, other website, offline store

#### Layer 2 — Semantic Filtering

**Tool:** Sentence Transformers (local free embedding model)

Semantic concepts to match against:
- Saving products for later
- Intention to purchase
- Difficulty deciding
- Purchase uncertainty
- Comparing fashion products
- Searching outside the shopping platform
- Delaying a fashion purchase

**Output:** data/relevant/relevant_records.json

Each record includes relevance_score and relevance_reason:
`json
{
  "id": "reddit_123",
  "text": "I kept three dresses aside until I figured out which one would suit me.",
  "keyword_score": 0.2,
  "semantic_score": 0.88,
  "final_relevance_score": 0.82
}
`

---

### PHASE 4 — AI-Powered Information Extraction

**Goal:** Extract structured behavioral signals from relevant conversations using an LLM.

**LLM Provider:** Groq API (free tier) — key stored in GROQ_API_KEY env variable

**Extraction schema:**
`json
{
  "is_relevant": true,
  "wishlist_behavior": {
    "detected": true,
    "type": "potential_purchase",
    "confidence": 0.85
  },
  "motivation": ["liked_design"],
  "uncertainties": ["size", "fit"],
  "purchase_blockers": ["low_fit_confidence"],
  "user_actions": ["searched_external_information"],
  "external_information_sources": ["Instagram"],
  "outcome": "unknown",
  "evidence_spans": [
    "wasn't sure about the size",
    "checked Instagram reels"
  ]
}
`

**Critical AI Rules (LLM must follow):**
- Only extract information explicitly stated or strongly supported by the text
- Use "unknown" when information is unavailable
- Do not invent user motivations
- Do not assume every saved product = purchase intent
- Do not classify sentiment unless it directly contributes to the research question

---

### PHASE 5 — Signal Aggregation & Pattern Discovery

**Goal:** Combine extracted signals across all conversations to find patterns.

| Dimension | Description |
|---|---|
| Frequency | How often does each signal appear? |
| Co-occurrence | Which signals appear together? |
| Behavioral chains | e.g. Interest → Uncertainty → External Search → Purchase Delay |
| Source comparison | Does the same pattern appear across Play Store, App Store, Reddit? |

---

### PHASE 6 — Opportunity Discovery

**Goal:** Convert repeated signals into potential underlying unmet needs.

Example:
`
SIGNALS: Size uncertainty + Fit uncertainty + Conflicting reviews + External try-on research
    ↓
POTENTIAL UNDERLYING NEED:
Users lack sufficient confidence to predict how a fashion product will fit and look before purchasing.
`

> All opportunity statements are evidence-backed hypotheses — not final conclusions until validated through primary research (surveys, interviews).

---

### PHASE 7 — Quantify & Compare Opportunity Areas

Each opportunity is scored on 5 dimensions:

| Dimension | Description |
|---|---|
| Frequency | Relevant records for opportunity / Total relevant records |
| Severity | 1 (minor) → 5 (causes abandonment) |
| Workaround Rate | Users who used workaround / Users experiencing issue |
| Metric Relevance | Strength of link to wishlist → purchase drop-off |
| Evidence Strength | Single record → Multiple records → Across multiple sources |

Example output table:

| Opportunity | Frequency | Severity | Workaround Rate | Metric Relevance | Evidence Strength |
|---|---|---|---|---|---|
| Fit confidence | High | High | High | High | High |
| Price timing | High | Medium | Medium | High | High |
| Product comparison | Medium | High | High | Medium/High | Medium |
| Styling confidence | Medium | Medium | High | Medium | Medium |

---

### PHASE 8 — Discovery Report

**Goal:** Generate a comprehensive research report from all pipeline outputs.

Report must include:
- Dataset summary (total collected, per source, relevant records)
- Top opportunity areas (evidence count, severity, workaround rate, metric relevance, evidence sources, behavioral pattern chain)
- Supporting evidence and representative user statements
- Source distribution
- Behavioral patterns
- Segment differences (where detectable)
- Opportunity scores
- Known limitations
- Research hypotheses for interviews and surveys

---

## 🔑 Key Design Principles

| Principle | Rule |
|---|---|
| Modular | Each module has one responsibility. New source should not break existing ones. |
| Raw data immutability | Never overwrite raw data. Always write to new files. |
| No AI for simple tasks | Use Python/Pandas for cleaning. Sentence Transformers for semantic filtering. Groq LLM only for structured extraction. |
| No hardcoded secrets | All credentials via environment variables. |
| Config-driven | Search queries and subreddits in config/, not in code. |
| Evidence-first | The LLM must not invent or assume. Only extract what the text supports. |
| Hypothesis-driven output | Final opportunities are labeled as hypotheses — not proven conclusions. |

---

## 📁 Key File Paths Reference

| File | Purpose |
|---|---|
| config/search_queries.json | Reddit search queries |
| config/subreddits.json | Target subreddits |
| data/raw/play_store_reviews.json | Raw Google Play data |
| data/raw/app_store_reviews.json | Raw App Store data |
| data/raw/reddit_data.json | Raw Reddit posts + comments |
| data/normalized/unified_dataset.json | Cleaned, unified schema |
| data/relevant/relevant_records.json | Relevance-filtered records |
| data/extracted/ | LLM-extracted structured signals |
| reports/ | Final discovery reports |

---

*Last updated: 2026-08-27 | Source: Problem_statement.txt*
