import os
import json
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from collectors.base_collector import BaseCollector
from utils.file_io import load_config

class RedditCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/reddit_data.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        
        max_posts = settings.get("collection", {}).get("reddit_max_posts_per_query", 50)
        all_records = []
        seen_urls = set()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
                })

                for query in queries:
                    self.logger.info(f"Searching Reddit (Playwright) for: {query}")
                    search_url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}"
                    
                    try:
                        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                        page.wait_for_timeout(5000) 
                        
                        for _ in range(40):
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(2000)
                            
                        html = page.content()
                        soup = BeautifulSoup(html, "html.parser")
                        
                        posts = soup.find_all("shreddit-post")
                        if not posts:
                            anchors = soup.find_all("a", href=True)
                            valid_anchors = [a for a in anchors if "/comments/" in a['href']]
                            posts = valid_anchors
                            
                        count = 0
                        for post in posts:
                            if count >= max_posts:
                                break
                            
                            url = ""
                            title = ""
                            text = ""
                            author = ""
                            
                            if post.name == "shreddit-post":
                                url = "https://www.reddit.com" + post.get("permalink", "")
                                title = post.get("post-title", "")
                                author = post.get("author", "")
                                text = post.get_text(strip=True)[:500]
                            else:
                                url = "https://www.reddit.com" + post['href'] if post['href'].startswith("/") else post['href']
                                title = post.get_text(strip=True)
                                text = title
                                
                            if not url or url in seen_urls or "/comments/" not in url:
                                continue
                                
                            seen_urls.add(url)
                            all_records.append({
                                "id": f"reddit_playwright_{hash(url)}",
                                "source": "reddit",
                                "source_type": "reddit_post",
                                "platform": "Myntra",
                                "title": title,
                                "text": text,
                                "rating": None,
                                "date": None,
                                "url": url,
                                "metadata": {
                                    "author": author,
                                    "query": query
                                }
                            })
                            count += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error scraping {query} on Reddit: {e}")
                        
                    time.sleep(3)
                
                browser.close()
        except Exception as e:
            self.logger.error(f"Playwright initialization failed: {e}")

        return all_records

    def validate(self, record: dict) -> bool:
        return bool(record.get("url"))

    def run(self):
        self.logger.info("Starting Reddit Collection (Playwright)...")
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
