import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.youtube.youtube_collector import YouTubeCollector

if __name__ == "__main__":
    collector = YouTubeCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
