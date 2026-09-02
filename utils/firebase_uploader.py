import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
from utils.logger import get_logger

logger = get_logger("firebase_uploader")

def upload_analytics_to_firestore(analytics_path="dashboard/analytics.json"):
    key_path = "serviceAccountKey.json"
    
    if not os.path.exists(key_path):
        logger.error(f"Cannot upload to Firebase: {key_path} not found.")
        return False
        
    if not os.path.exists(analytics_path):
        logger.error(f"Cannot upload to Firebase: {analytics_path} not found.")
        return False

    try:
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        
        # Read the local analytics.json
        with open(analytics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Push to a document named 'latest' in the 'analytics' collection
        doc_ref = db.collection('analytics').document('latest')
        doc_ref.set(data)
        
        logger.info("Successfully uploaded analytics data to Firestore!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload to Firestore: {e}")
        return False

if __name__ == "__main__":
    upload_analytics_to_firestore()
