import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.social.social_collector import SocialCollector

if __name__ == "__main__":
    collector = SocialCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
