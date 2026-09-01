import os
import json
import time
import uuid
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
from duckduckgo_search import DDGS

class WebCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/web_data.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        
        max_results = settings.get("collection", {}).get("web_search_max_results", 50)
        
        all_records = []
        seen_urls = set()
        
        # We can append "forum" or "community" to queries if we want specific community chatter
        # Or search on Quora: "site:quora.com Myntra wishlist"
        
        # Let's add some custom community targeted queries on top of the generic ones
        community_queries = []
        for q in queries:
            if "wishlist" in q.lower():
                community_queries.append(f"{q} forum")
                community_queries.append(f"{q} site:quora.com")
                
        # Combine them
        target_queries = list(set(queries + community_queries))
        
        with DDGS() as ddgs:
            for query in target_queries:
                self.logger.info(f"Searching Web (DuckDuckGo) for: {query}")
                try:
                    # Search text
                    results = ddgs.text(query, max_results=max_results, backend='html')
                    for result in results:
                        url = result.get("href")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        
                        all_records.append({
                            "id": f"web_{uuid.uuid4().hex}",
                            "source": "web_search",
                            "source_type": "web_article",
                            "platform": "Myntra",
                            "title": result.get("title"),
                            "text": result.get("body"), # Snippet
                            "rating": None,
                            "date": None, # duckduckgo_search doesn't always provide dates for regular text search
                            "url": url,
                            "metadata": {
                                "search_query": query
                            }
                        })
                except Exception as e:
                    self.logger.error(f"Error fetching web results for '{query}': {e}")
                
                time.sleep(3) # Prevent rate limits
                
        return all_records

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("url"))

    def run(self):
        self.logger.info("Starting Web Community collection...")
        records = self.collect()
        
        existing_records = []
        if os.path.exists(self.OUTPUT_PATH):
            try:
                with open(self.OUTPUT_PATH, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except Exception:
                pass
                
        seen_urls = {r.get("url") for r in existing_records if isinstance(r, dict) and r.get("url")}
        for r in records:
            if r.get("url") not in seen_urls:
                existing_records.append(r)
                
        self.save(existing_records, self.OUTPUT_PATH)
        return self.summarize(existing_records)
