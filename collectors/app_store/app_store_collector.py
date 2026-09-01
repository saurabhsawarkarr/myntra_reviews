from app_store_scraper import AppStore
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
import uuid
import os
import json

class AppStoreCollector(BaseCollector):
    APP_ID = "907394059"
    APP_NAME = "myntra"
    COUNTRY = "in"
    OUTPUT_PATH = "data/raw/app_store_reviews.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        max_reviews = settings["collection"]["app_store_max_reviews"]
        
        self.logger.info(f"Fetching up to {max_reviews} reviews using app-store-scraper...")
        try:
            app = AppStore(country=self.COUNTRY, app_name=self.APP_NAME, app_id=self.APP_ID)
            # The scraper fetches in batches. We specify how_many to get the desired amount.
            app.review(how_many=max_reviews)
            
            all_reviews = []
            for raw in app.reviews:
                all_reviews.append(self._normalize(raw))
                
            return all_reviews
        except Exception as e:
            self.logger.error(f"Error fetching from AppStore scraper: {e}")
            return []

    def _normalize(self, raw: dict) -> dict:
        return {
            "id": f"app_{uuid.uuid4().hex}",
            "source": "apple_app_store",
            "source_type": "app_review",
            "platform": "Myntra",
            "title": raw.get("title"),
            "text": raw.get("review"),
            "rating": raw.get("rating"),
            "date": str(raw.get("date"))[:10] if raw.get("date") else None,
            "url": None,
            "metadata": {
                "user_name": raw.get("userName")
            }
        }

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Apple App Store collection (via app-store-scraper)...")
        records = self.collect()
        
        # Load existing so we don't lose data if something fails
        existing_records = []
        if os.path.exists(self.OUTPUT_PATH):
            try:
                with open(self.OUTPUT_PATH, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except Exception:
                pass
                
        seen_texts = {r.get("text") for r in existing_records if isinstance(r, dict) and r.get("text")}
        for r in records:
            if r.get("text") not in seen_texts:
                existing_records.append(r)
                
        self.save(existing_records, self.OUTPUT_PATH)
        return self.summarize(existing_records)
