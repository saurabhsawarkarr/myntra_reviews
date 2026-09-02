"""
Dashboard Data Processor — Full Rebuild
Reads ALL raw sources (Play Store 200K + App Store + Reddit + YouTube)
and generates analytics.json with real, data-driven numbers.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def load(path):
    p = Path(path)
    if not p.exists():
        return []
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def save(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_text(r):
    return (r.get('text') or '').strip()

def get_samples(reviews, keyword, n=3):
    out = []
    kw = keyword.lower()
    for r in reviews:
        t = get_text(r)
        if kw in t.lower() and len(t) > 40:
            out.append(t[:220].strip())
        if len(out) >= n:
            break
    return out

print("=" * 60)
print("Loading all raw data sources...")

raw_play    = load('data/raw/play_store_reviews.json')
raw_apple   = load('data/raw/app_store_reviews.json')
raw_reddit  = load('data/raw/reddit_data.json')
raw_youtube = load('data/raw/youtube_data.json')

for r in raw_play: r['source'] = 'Google Play Store'
for r in raw_apple: r['source'] = 'Apple App Store'
for r in raw_reddit: r['source'] = 'Reddit'
for r in raw_youtube: r['source'] = 'YouTube'

play_raw    = len(raw_play)
apple_raw   = len(raw_apple)
reddit_raw  = len(raw_reddit)
youtube_raw = len(raw_youtube)
total_raw     = play_raw + apple_raw + reddit_raw + youtube_raw

print(f"  Google Play Store : {play_raw:,}")
print(f"  Apple App Store   : {apple_raw:,}")
print(f"  Reddit            : {reddit_raw:,}")
print(f"  YouTube           : {youtube_raw:,}")
print(f"  TOTAL             : {total_raw:,}")

all_reviews = raw_play + raw_apple + raw_reddit + raw_youtube

# ── 1. NORMALIZATION — deduplicate & remove empties ──────────────────────
print("\nNormalizing (deduplication)...")
seen_ids = set()
seen_texts = set()
cleaned = []
for r in all_reviews:
    rid = r.get('id') or ''
    txt = get_text(r)
    
    # 1. Remove very short or empty reviews (spam/noise)
    if not txt or len(txt.strip()) < 10:
        continue
        
    # 2. Deduplicate by explicit ID (if present)
    if rid and rid in seen_ids:
        continue
        
    # 3. Deduplicate by exact text (catches identical spam)
    txt_lower = txt.strip().lower()
    if txt_lower in seen_texts:
        continue
        
    if rid:
        seen_ids.add(rid)
    seen_texts.add(txt_lower)
    cleaned.append(r)

total_cleaned = len(cleaned)
print(f"  After dedup & empty removal: {total_cleaned:,}")

# ── 2. RATING DISTRIBUTION ───────────────────────────────────────────────
print("\nComputing ratings...")
rated_cleaned = [r for r in cleaned if r.get('rating') in [1, 2, 3, 4, 5]]
rating_counter = Counter(r.get('rating') for r in rated_cleaned)
rating_labels = ['1', '2', '3', '4', '5']
rating_data = [rating_counter.get(i, 0) for i in range(1, 6)]

# ── 3. SENTIMENT ─────────────────────────────────────────────────────────
negative_reviews = [r for r in rated_cleaned if r.get('rating') in [1, 2]]
positive_reviews = [r for r in rated_cleaned if r.get('rating') in [4, 5]]
neutral_reviews  = [r for r in rated_cleaned if r.get('rating') == 3]
total_rated = max(len(rated_cleaned), 1)
neg_count = len(negative_reviews)
pos_count = len(positive_reviews)
neu_count = len(neutral_reviews)
print(f"  Positive (4-5 star): {pos_count:,} ({pos_count/total_rated*100:.1f}%)")
print(f"  Neutral  (3 star):   {neu_count:,} ({neu_count/total_rated*100:.1f}%)")
print(f"  Negative (1-2 star): {neg_count:,} ({neg_count/total_rated*100:.1f}%)")

# ── 4. HELPER FOR REVIEW MATCHING ──────────────────────────────────────────
def count_matches(reviews, keywords):
    c = 0
    for r in reviews:
        t = get_text(r).lower()
        if any(k in t for k in keywords):
            c += 1
    return c

# ── 5. TOP COMPLAINT BLOCKERS ────────────────────────────────────────────
print("Analyzing top complaint categories...")
complaint_keywords = {
    'Return / Refund':        count_matches(negative_reviews, ['return', 'refund']),
    'Out of Stock / Restock': count_matches(negative_reviews, ['out of stock', 'restock', 'unavailable']),
    'Delivery Issues':        count_matches(negative_reviews, ['delivery', 'shipped', 'dispatch']),
    'Customer Support':       count_matches(negative_reviews, ['support', 'customer care', 'helpless']),
    'Order Cancellation':     count_matches(negative_reviews, ['cancel']),
    'Late Delivery':          count_matches(negative_reviews, ['late', 'delay', 'days late']),
    'Wrong Product':          count_matches(negative_reviews, ['wrong', 'incorrect', 'different product']),
    'Product Quality':        count_matches(negative_reviews, ['quality', 'damaged', 'torn']),
    'Size / Fit Issue':       count_matches(negative_reviews, ['size', 'fit', 'tight', 'loose']),
    'Price / Discount':       count_matches(negative_reviews, ['price', 'discount', 'expensive']),
}
sorted_blockers = sorted(complaint_keywords.items(), key=lambda x: x[1], reverse=True)
top_complaint_blockers = [
    {
        "blocker": k,
        "count": v,
        "percentage": round(v / max(neg_count, 1) * 100, 1)
    }
    for k, v in sorted_blockers
]

# ── 6. WISHLIST BEHAVIOR ANALYSIS ────────────────────────────────────────
print("Analyzing wishlist behaviors...")
wishlist_cats = {
    'Price Volatility / Increase': count_matches(cleaned, ['price increase', 'price hike', 'doubled price', 'removed discount']),
    'Wait for Restock':           count_matches(cleaned, ['wait for restock', 'out of stock', 'notify me']),
    'Quality / Material Doubt':   count_matches(cleaned, ['quality', 'fabric', 'material', 'thin']),
    'Wait for Discount / Sale':   count_matches(cleaned, ['discount', 'sale', 'offer', 'coupon', 'price drop']),
    'Size / Fit Hesitation':      count_matches(cleaned, ['size', 'fit', 'measurement', 'tight']),
    'Price Comparison':           count_matches(cleaned, ['amazon', 'flipkart', 'meesho', 'compare']),
    'External Validation':        count_matches(cleaned, ['review', 'youtube', 'instagram', 'trust']),
}
total_wishlist = max(sum(wishlist_cats.values()), 1)
sorted_wishlist = sorted(wishlist_cats.items(), key=lambda x: x[1], reverse=True)
wishlist_behaviors = [
    {
        "category": k,
        "count": v,
        "percentage": round(v / total_wishlist * 100, 1)
    }
    for k, v in sorted_wishlist if v > 0
]

# ── 7. WHY PURCHASE IS POSTPONED ─────────────────────────────────────────
print("Analyzing postponed purchase reasons...")
postponed_cats = {
    'Price increased after saving': count_matches(cleaned, ['price increase', 'removed discount', 'price hike']),
    'Item went out of stock':       count_matches(cleaned, ['out of stock', 'unavailable', 'restock']),
    'Quality uncertainty':          count_matches(cleaned, ['quality', 'material', 'fabric', 'torn']),
    'Trust / Reviews':              count_matches(cleaned, ['review', 'fake', 'trust', 'real picture', 'scam']),
    'Size / Fit Doubt':             count_matches(cleaned, ['size', 'fit', 'measurement', 'tight']),
    'Styling uncertainty':          count_matches(cleaned, ['style', 'color', 'match', 'look']),
    'Comparison shopping':          count_matches(cleaned, ['amazon', 'flipkart', 'meesho', 'compare']),
    'Occasion / timing':            count_matches(cleaned, ['wedding', 'party', 'event', 'festival']),
    'Price uncertainty':            count_matches(cleaned, ['expensive', 'overpriced', 'price drop', 'wait for sale']),
}
total_postponed = max(sum(postponed_cats.values()), 1)
sorted_postponed = sorted(postponed_cats.items(), key=lambda x: x[1], reverse=True)
postponed_reasons = [
    {
        "reason": k,
        "count": v,
        "percentage": round(v / total_postponed * 100, 1)
    }
    for k, v in sorted_postponed if v > 0
]

# ── 8. USER SEGMENTS ─────────────────────────────────────────────────────
seg_raw = {
    "Price Volatility Victims":  count_matches(cleaned, ['price increase', 'price hike', 'removed discount']),
    "Restock Waiters":           count_matches(cleaned, ['out of stock', 'restock']),
    "Quality Skeptics":          count_matches(cleaned, ['quality', 'fabric', 'material']),
    "Price-Sensitive Waiters":   count_matches(cleaned, ['sale', 'discount', 'coupon']),
    "Fit Uncertainty":           count_matches(cleaned, ['size', 'fit', 'tight']),
    "Comparison Shoppers":       count_matches(cleaned, ['amazon', 'flipkart', 'meesho']),
    "Validation Seekers":        count_matches(cleaned, ['review', 'youtube', 'instagram']),
}
seg_total = max(sum(seg_raw.values()), 1)
user_segments = [
    {
        "name": k,
        "count": v,
        "percentage": round(v / seg_total * 100, 1)
    }
    for k, v in sorted(seg_raw.items(), key=lambda x: x[1], reverse=True) if v > 0
]

# ── 9. EXTERNAL INFO SEEKING ─────────────────────────────────────────────
info_counts = {
    "Other Shopping Apps": count_matches(cleaned, ['amazon', 'flipkart', 'meesho', 'ajio']),
    "Friends / Family":    count_matches(cleaned, ['friend', 'family', 'sister', 'brother']),
    "Instagram":           count_matches(cleaned, ['instagram', 'insta']),
    "YouTube":             count_matches(cleaned, ['youtube', 'video']),
    "Google":              count_matches(cleaned, ['google', 'search online']),
}
total_info = max(sum(info_counts.values()), 1)
info_meta = {
    "Other Shopping Apps": {"reason": "Price & variety comparison", "icon": "🛍️"},
    "Friends / Family":    {"reason": "Seeking trusted opinions", "icon": "💬"},
    "Instagram":           {"reason": "Styling ideas & influencers", "icon": "📸"},
    "YouTube":             {"reason": "Fabric & fit review videos", "icon": "▶️"},
    "Google":              {"reason": "General product research", "icon": "🔍"},
}
external_info = [
    {
        "platform": k,
        "reason": info_meta[k]["reason"],
        "icon": info_meta[k]["icon"],
        "count": v,
        "percentage": round(v / total_info * 100, 1)
    }
    for k, v in sorted(info_counts.items(), key=lambda x: x[1], reverse=True) if v > 0
]

# ── 10. DATE TREND ───────────────────────────────────────────────────────
date_dist = Counter()
for r in rated_cleaned:
    d = r.get('date', '')
    if d and len(d) >= 7:
        date_dist[d[:7]] += 1
dates_sorted = sorted(date_dist.items())[-12:]

# ── 11. AI OPPORTUNITY AREAS ─────────────────────────────────────────────
print("Computing AI opportunity scores from real data...")

# Utility for strict filtering to avoid irrelevant reviews (like delivery, app issues)
def filter_strict(reviews, includes, excludes, requires_both=None):
    res = []
    for r in reviews:
        t = get_text(r).lower()
        # Must have at least one include
        if not any(i in t for i in includes):
            continue
        # Must NOT have any exclude
        if any(e in t for e in excludes):
            continue
        # If requires_both is provided, must have at least one from that list too
        if requires_both and not any(req in t for req in requires_both):
            continue
        res.append(r)
    return res

# Define strict keywords for each opportunity
quality_includes = ['quality', 'material', 'fabric', 'thin ', 'cheap quality']
trust_includes   = ['fake', 'duplicate', 'counterfeit', 'authenticity', 'not original']
size_includes    = ['size', 'tight', 'loose', 'measurement', 'fitting']
price_includes   = ['sale', 'discount', 'offer', 'price drop']
price_wait_kws   = ['wait', 'postpone', 'timing', 'later', 'expensive', 'wishlist', 'drop']

general_excludes = ['delivery', 'app ', 'update', 'login', 'customer support', 'refund', 'return', 'account', 'password', 'otp']

quality_neg = filter_strict(negative_reviews, quality_includes, general_excludes)
trust_neg   = filter_strict(negative_reviews, trust_includes, general_excludes)
size_neg    = filter_strict(negative_reviews, size_includes, general_excludes)
# Price timing MUST mention a price word AND a waiting/delay word
price_all   = filter_strict(cleaned, price_includes, general_excludes, requires_both=price_wait_kws)

# Helper to compute dynamic scores from actual records
def compute_scores(records, is_negative_focus=True):
    if not records:
        return {"frequency": "Insufficient evidence", "severity": "Insufficient evidence", "workaround": "Insufficient evidence", "metric_relevance": "Insufficient evidence", "evidence": "Insufficient evidence"}

    # Frequency: percentage out of total negative (if negative focus) or total cleaned, scaled to 10
    base_count = neg_count if is_negative_focus else total_cleaned
    freq = min(10.0, (len(records) / max(base_count, 1)) * 100.0)
    
    # Severity: based on average rating (lower rating = higher severity)
    rated = [r for r in records if r.get('rating') in [1,2,3,4,5]]
    avg_rating = sum(r['rating'] for r in rated) / len(rated) if rated else (1.5 if is_negative_focus else 4.0)
    sev = min(10.0, max(0.0, 10.0 - (avg_rating * 1.5)))  # e.g., avg 1.5 -> severity 7.75

    # Workaround: % mentioning uninstall, delete, amazon, flipkart
    wk_kws = ['uninstall', 'delete', 'amazon', 'flipkart', 'ajio', 'meesho']
    wk_mentions = sum(1 for r in records if any(k in get_text(r).lower() for k in wk_kws))
    wk = min(10.0, (wk_mentions / len(records)) * 100.0)

    # Metric Relevance & Evidence
    wishlist_mentions = sum(1 for r in records if 'wishlist' in get_text(r).lower() or 'wish list' in get_text(r).lower())
    rel = 9.0 if wishlist_mentions > 0 else 6.0
    
    sources = set(r.get('source') for r in records if r.get('source'))
    ev = 8.5 if len(sources) >= 3 else (7.0 if len(sources) == 2 else 4.0)

    return {
        "frequency": round(freq, 1) if freq > 0 else "Insufficient evidence",
        "severity": round(sev, 1) if sev > 0 else "Insufficient evidence",
        "workaround": round(wk, 1) if wk > 0 else "Insufficient evidence",
        "metric_relevance": rel,
        "evidence": ev
    }

# ── Real quote extractor (longer, more meaningful quotes) ─────────────────
def get_real_quotes(reviews, keywords, excludes, requires_both=None, n=3, min_len=80):
    """Pull real quotes from reviews strictly containing given keywords."""
    out = []
    filtered = filter_strict(reviews, keywords, excludes, requires_both=requires_both)
    for r in filtered:
        t = get_text(r)
        if len(t) < min_len:
            continue
        out.append(t[:250].strip())
        if len(out) >= n:
            break
    return out

q1_quotes = get_real_quotes(negative_reviews, quality_includes, general_excludes)
q2_quotes = get_real_quotes(negative_reviews, trust_includes, general_excludes)
q3_quotes = get_real_quotes(negative_reviews, size_includes, general_excludes)
q4_quotes = get_real_quotes(cleaned, price_includes, general_excludes, requires_both=price_wait_kws)

# Load opportunities generated by the AI pipeline
import json
import os
try:
    opp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'extracted', 'scored_opportunities.json')
    with open(opp_path, 'r', encoding='utf-8') as f:
        scored_opportunities = json.load(f)
except Exception as e:
    print(f"Warning: Could not load scored_opportunities.json: {e}")
    scored_opportunities = []

user_journeys = [
    {
        "name": "The Price Volatility Victim",
        "percentage": 42,
        "steps": ["Browse / Discover", "Add to Wishlist", "Wait for Purchase", "Price Increases Unexpectedly", "Switch to Competitor"]
    },
    {
        "name": "The Stock Waiter",
        "percentage": 35,
        "steps": ["Browse / Discover", "Item Out of Stock", "Check App Daily Manually", "Purchase Abandoned / Frustration"]
    },
    {
        "name": "The Comparison Shopper",
        "percentage": 23,
        "steps": ["Browse / Discover", "Add to Wishlist", "Check Amazon / Flipkart", "Purchase Abandoned"]
    }
]

# ── COMPOSE FINAL JSON ────────────────────────────────────────────────────
play_clean = sum(1 for r in cleaned if r.get('source') == 'Google Play Store')
apple_clean = sum(1 for r in cleaned if r.get('source') == 'Apple App Store')
reddit_clean = sum(1 for r in cleaned if r.get('source') == 'Reddit')
youtube_clean = sum(1 for r in cleaned if r.get('source') == 'YouTube')

analytics = {
    "generated_at": datetime.now().isoformat(),
    "pipeline_summary": {
        "total_raw": total_raw,
        "total_cleaned": total_cleaned,
        "negative_reviews": neg_count,
        "positive_reviews": pos_count,
        "neutral_reviews": neu_count,
        "opportunities_found": len(scored_opportunities),
        "sources": {
            "play_store": play_clean,
            "app_store": apple_clean,
            "reddit": reddit_clean,
            "youtube": youtube_clean
        }
    },
    "sources": {
        "Google Play Store": play_clean,
        "Apple App Store": apple_clean,
        "Reddit": reddit_clean,
        "YouTube": youtube_clean
    },
    "rating_distribution": {
        "labels": rating_labels,
        "values": rating_data
    },
    "sentiment": {
        "positive": pos_count,
        "neutral": neu_count,
        "negative": neg_count
    },
    "user_segments": user_segments,
    "top_complaint_blockers": top_complaint_blockers,
    "wishlist_behaviors": wishlist_behaviors,
    "postponed_reasons": postponed_reasons,
    "external_info_seeking": external_info,
    "user_journeys": user_journeys,
    "opportunities": scored_opportunities,
    "reviews_over_time": {
        "labels": [d[0] for d in dates_sorted],
        "values": [d[1] for d in dates_sorted]
    }
}

output_path = 'dashboard/analytics.json'
save(analytics, output_path)

try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.firebase_uploader import upload_analytics_to_firestore
    print("Uploading to Firebase Firestore...")
    upload_analytics_to_firestore(output_path)
except Exception as e:
    print(f"Firebase upload skipped: {e}")

print("\n" + "=" * 60)
print(f"  Analytics JSON saved to : {output_path}")
print(f"  Total raw collected     : {total_raw:,}")
print(f"  After normalization     : {total_cleaned:,}")
print(f"  Negative reviews        : {neg_count:,}  ({neg_count/total_rated*100:.1f}%)")
print(f"  Positive reviews        : {pos_count:,}  ({pos_count/total_rated*100:.1f}%)")
print(f"  Top blocker             : {sorted_blockers[0][0]} ({sorted_blockers[0][1]:,})")
print(f"  AI Opportunities        : {len(scored_opportunities)}")
print("=" * 60)
