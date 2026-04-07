# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'medexpiry-hackathon-2026')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # Firebase Config
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', 'demo-key')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'medexpiry-demo')

    # Google Maps
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'your-maps-key')

    # OCR Config
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'/usr/bin/tesseract')

    # Alert thresholds (days)
    EXPIRY_CRITICAL = 7
    EXPIRY_WARNING = 30
    EXPIRY_SOON = 90
