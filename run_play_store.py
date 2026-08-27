import sys
import os

# Add the root directory to the python path so it can find utils and collectors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.play_store.play_store_collector import PlayStoreCollector

if __name__ == "__main__":
    collector = PlayStoreCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
