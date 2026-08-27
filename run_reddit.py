import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.reddit.reddit_collector import RedditCollector

if __name__ == "__main__":
    collector = RedditCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
