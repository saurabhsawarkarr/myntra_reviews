import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.web.web_collector import WebCollector

if __name__ == "__main__":
    collector = WebCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
