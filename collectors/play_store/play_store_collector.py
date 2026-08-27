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
