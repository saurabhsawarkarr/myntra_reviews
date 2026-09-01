import os
import json
import time
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from collectors.base_collector import BaseCollector
from utils.file_io import load_config

class SocialCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/social_data.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        
        # We will only look for social media sites
        target_sites = ["twitter.com", "instagram.com", "facebook.com", "quora.com", "linkedin.com"]
        
        all_records = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
                })

                # Go to a neutral search engine that doesn't block as aggressively as Google
                search_engine = "https://html.duckduckgo.com/html/?q="
                
                # Filter queries for only those involving 'wishlist' to speed things up
                wishlist_queries = [q for q in queries if "wishlist" in q.lower()]
                if not wishlist_queries:
                    wishlist_queries = ["Myntra wishlist"]

                for site in target_sites:
                    for query in wishlist_queries:
                        advanced_query = f"site:{site} \"{query}\""
                        self.logger.info(f"Searching for Social Posts: {advanced_query}")
                        
                        try:
                            encoded_q = urllib.parse.quote_plus(advanced_query)
                            page.goto(search_engine + encoded_q, wait_until="domcontentloaded", timeout=30000)
                            
                            html = page.content()
                            soup = BeautifulSoup(html, "html.parser")
                            
                            results = soup.find_all("a", class_="result__url")
                            snippets = soup.find_all("a", class_="result__snippet")
                            titles = soup.find_all("h2", class_="result__title")
                            
                            for i, res in enumerate(results):
                                try:
                                    url = res.get("href")
                                    if not url or url in seen_urls:
                                        continue
                                        
                                    title = titles[i].get_text(strip=True) if i < len(titles) else ""
                                    snippet = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                                    
                                    seen_urls.add(url)
                                    all_records.append({
                                        "id": f"social_{hash(url)}",
                                        "source": site.split('.')[0],
                                        "source_type": "social_post",
                                        "platform": "Myntra",
                                        "title": title,
                                        "text": snippet,
                                        "rating": None,
                                        "date": None,
                                        "url": "https://" + url.replace(" ", "") if not url.startswith("http") else url,
                                        "metadata": {
                                            "query": query
                                        }
                                    })
                                except Exception:
                                    continue
                                
                        except Exception as e:
                            self.logger.error(f"Error executing search {advanced_query}: {e}")
                            
                        time.sleep(4)
                        
                browser.close()
        except Exception as e:
            self.logger.error(f"Playwright error in SocialCollector: {e}")

        return all_records

    def validate(self, record: dict) -> bool:
        return bool(record.get("url") and record.get("text"))

    def run(self):
        self.logger.info("Starting Social Media Collection (Playwright)...")
        records = self.collect()
        
        existing_records = []
        if os.path.exists(self.OUTPUT_PATH):
            try:
                with open(self.OUTPUT_PATH, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except Exception:
                pass
                
        seen_ids = {r.get("id") for r in existing_records if isinstance(r, dict) and r.get("id")}
        for r in records:
            if r.get("id") not in seen_ids:
                existing_records.append(r)
                
        self.save(existing_records, self.OUTPUT_PATH)
        return self.summarize(existing_records)
