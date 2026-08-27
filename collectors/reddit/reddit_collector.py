import praw, uuid
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
from utils.env_loader import get_env

class RedditCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/reddit_data.json"

    def _get_client(self):
        return praw.Reddit(
            client_id=get_env("REDDIT_CLIENT_ID"),
            client_secret=get_env("REDDIT_CLIENT_SECRET"),
            user_agent=get_env("REDDIT_USER_AGENT")
        )

    def collect(self) -> list[dict]:
        reddit = self._get_client()
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        subreddits = load_config("subreddits.json")
        max_posts = settings["collection"]["reddit_max_posts_per_query"]
        max_comments = settings["collection"]["reddit_max_comments_per_post"]

        records, seen_ids = [], set()

        for query in queries:
            self.logger.info(f"Searching: {query}")
            for post in reddit.subreddit("all").search(query, limit=max_posts):
                if post.id in seen_ids: continue
                seen_ids.add(post.id)
                records.append(self._normalize_post(post))
                records.extend(self._get_comments(post, max_comments, seen_ids))

        for sub in subreddits:
            try:
                for post in reddit.subreddit(sub).new(limit=max_posts):
                    if post.id in seen_ids: continue
                    seen_ids.add(post.id)
                    records.append(self._normalize_post(post))
                    records.extend(self._get_comments(post, max_comments, seen_ids))
            except Exception as e:
                self.logger.warning(f"Could not access r/{sub}: {e}")

        return records

    def _normalize_post(self, post) -> dict:
        return {
            "id": f"reddit_post_{post.id}",
            "source": "reddit",
            "source_type": "reddit_post",
            "platform": "Myntra",
            "title": post.title,
            "text": post.selftext or post.title,
            "rating": None,
            "date": str(post.created_utc)[:10],
            "url": f"https://reddit.com{post.permalink}",
            "metadata": {"subreddit": str(post.subreddit), "score": post.score, "num_comments": post.num_comments}
        }

    def _get_comments(self, post, max_comments, seen_ids) -> list[dict]:
        comments = []
        try:
            post.comments.replace_more(limit=0)
            for c in post.comments.list()[:max_comments]:
                if c.id in seen_ids: continue
                seen_ids.add(c.id)
                comments.append({
                    "id": f"reddit_comment_{c.id}",
                    "source": "reddit",
                    "source_type": "reddit_comment",
                    "platform": "Myntra",
                    "title": None,
                    "text": c.body,
                    "rating": None,
                    "date": str(c.created_utc)[:10],
                    "url": f"https://reddit.com{c.permalink}",
                    "metadata": {"subreddit": str(c.subreddit), "score": c.score, "parent_id": f"reddit_post_{post.id}"}
                })
        except Exception as e:
            self.logger.warning(f"Comment error on post {post.id}: {e}")
        return comments

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting Reddit collection...")
        records = self.collect()
        self.save(records, self.OUTPUT_PATH)
        return self.summarize(records)
