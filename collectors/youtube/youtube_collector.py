import os
import json
import time
from collectors.base_collector import BaseCollector
from utils.file_io import load_config
from youtubesearchpython import VideosSearch
from youtube_comment_downloader import YoutubeCommentDownloader

class YouTubeCollector(BaseCollector):
    OUTPUT_PATH = "data/raw/youtube_data.json"

    def collect(self) -> list[dict]:
        settings = load_config("settings.json")
        queries = load_config("search_queries.json")
        
        # Safe fallback if these don't exist in settings yet
        max_videos = settings.get("collection", {}).get("youtube_max_videos_per_query", 5)
        max_comments = settings.get("collection", {}).get("youtube_max_comments_per_video", 50)
        
        all_records = []
        seen_vids = set()
        
        downloader = YoutubeCommentDownloader()
        
        for query in queries:
            self.logger.info(f"Searching YouTube for: {query}")
            try:
                videos_search = VideosSearch(query, limit = max_videos)
                results = videos_search.result()
                
                for video in results.get('result', []):
                    vid_id = video.get('id')
                    if not vid_id or vid_id in seen_vids:
                        continue
                    seen_vids.add(vid_id)
                    
                    self.logger.info(f"Fetching comments for video: {video.get('title')}")
                    
                    # Add video metadata
                    desc = video.get("descriptionSnippet")
                    desc_text = desc[0].get("text", "") if isinstance(desc, list) and len(desc) > 0 else video.get("title")
                    
                    all_records.append({
                        "id": f"yt_vid_{vid_id}",
                        "source": "youtube",
                        "source_type": "youtube_video",
                        "platform": "Myntra",
                        "title": video.get("title"),
                        "text": desc_text,
                        "rating": None,
                        "date": video.get("publishedTime"),
                        "url": video.get("link"),
                        "metadata": {
                            "channel": video.get("channel", {}).get("name"),
                            "views": video.get("viewCount", {}).get("text")
                        }
                    })
                    
                    # Fetch comments
                    count = 0
                    try:
                        comments = downloader.get_comments(vid_id)
                        for comment in comments:
                            if count >= max_comments:
                                break
                            
                            all_records.append({
                                "id": f"yt_comment_{comment.get('cid')}",
                                "source": "youtube",
                                "source_type": "youtube_comment",
                                "platform": "Myntra",
                                "title": None,
                                "text": comment.get('text'),
                                "rating": None,
                                "date": comment.get('time'), 
                                "url": f"https://www.youtube.com/watch?v={vid_id}&lc={comment.get('cid')}",
                                "metadata": {
                                    "author": comment.get('author'),
                                    "votes": comment.get('votes'),
                                    "video_id": vid_id
                                }
                            })
                            count += 1
                    except Exception as e:
                        self.logger.error(f"Error fetching comments for {vid_id}: {e}")
                        
            except Exception as e:
                self.logger.error(f"Error searching YouTube for {query}: {e}")
                
            time.sleep(2) # rate limit prevention
            
        return all_records

    def validate(self, record: dict) -> bool:
        return bool(record.get("text") and record.get("id"))

    def run(self):
        self.logger.info("Starting YouTube collection...")
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
