import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.app_store.app_store_collector import AppStoreCollector

if __name__ == "__main__":
    collector = AppStoreCollector()
    summary = collector.run()
    print("Collection Summary:", summary)
