import requests
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
import uuid

class AppStoreCollector(BaseCollector):
    APP_ID = "907394059"
    COUNTRY = "in"
    OUTPUT_PATH = "data/raw/app_store_reviews.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        max_reviews = settings["collection"]["app_store_max_reviews"]
        all_reviews = []
        
        # iTunes RSS feed only allows up to 10 pages of 50 reviews (500 max)
        for page in range(1, 11):
            url = f"https://itunes.apple.com/{self.COUNTRY}/rss/customerreviews/page={page}/id={self.APP_ID}/sortby=mostrecent/json"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch page {page}. Status: {response.status_code}")
                    break
                    
                data = response.json()
                entries = data.get("feed", {}).get("entry", [])
                
                # If entries is a dict (only 1 review), wrap it in a list
                if isinstance(entries, dict):
                    entries = [entries]
                    
                if not entries:
                    break
                
                for entry in entries:
                    # Skip the app metadata entry (which doesn't have an author name)
                    if "author" in entry and "name" in entry["author"]:
                        all_reviews.append(self._normalize(entry))
                        
                if len(all_reviews) >= max_reviews:
                    break
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
                
        return all_reviews[:max_reviews]

    def _normalize(self, raw: dict) -> dict:
        return {
            "id": f"app_{raw.get('id', {}).get('label', uuid.uuid4().hex)}",
            "source": "apple_app_store",
            "source_type": "app_review",
            "platform": "Myntra",
            "title": raw.get("title", {}).get("label"),
            "text": raw.get("content", {}).get("label"),
            "rating": int(raw.get("im:rating", {}).get("label", 0)),
            "date": None,
            "url": raw.get("author", {}).get("uri", {}).get("label"),
            "metadata": {
                "app_version": raw.get("im:version", {}).get("label"),
                "user_name": raw.get("author", {}).get("name", {}).get("label")
            }
        }

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Apple App Store collection (via RSS)...")
        records = self.collect()
        self.save(records, self.OUTPUT_PATH)
        return self.summarize(records)
