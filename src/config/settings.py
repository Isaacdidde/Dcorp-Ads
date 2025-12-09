"""
Production-grade application settings for DCorp.

Loads all critical configuration values from environment variables.
If any required value is missing, startup will fail FAST — this prevents
accidental insecure deployments.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ---------------------------------------------------------------
    # 0. DEBUG MODE
    # ---------------------------------------------------------------
    DEBUG = os.getenv("FLASK_DEBUG", "false").strip().lower() == "true"


    # ---------------------------------------------------------------
    # 1. FLASK SECRET KEY
    # ---------------------------------------------------------------
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("❌ Missing FLASK_SECRET_KEY in .env")


    # ---------------------------------------------------------------
    # 2. PUBLIC URLs (Used across ads delivery, callbacks, tracking)
    # ---------------------------------------------------------------
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
    if not PUBLIC_BASE_URL:
        raise ValueError("❌ Missing PUBLIC_BASE_URL in .env")

    # This is used by bidding engine internally
    DCORP_API_URL = os.getenv("DCORP_API_URL")
    if not DCORP_API_URL:
        raise ValueError("❌ Missing DCORP_API_URL in .env")


    # ---------------------------------------------------------------
    # 3. FILE UPLOAD HANDLING
    # ---------------------------------------------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "src/static/uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


    # ---------------------------------------------------------------
    # 4. MONGO DB CONNECTION
    # ---------------------------------------------------------------
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASS = os.getenv("MONGO_PASS")
    MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")   # e.g., cluster0.xxxxx.mongodb.net
    MONGO_DB = os.getenv("MONGO_DB")

    # Enforce strict completeness
    if not all([MONGO_USER, MONGO_PASS, MONGO_CLUSTER, MONGO_DB]):
        raise ValueError("❌ Missing MongoDB environment values (MONGO_USER, MONGO_PASS, MONGO_CLUSTER, MONGO_DB)")

    # Final MongoDB Atlas URI
    MONGO_URI = (
        f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}"
        f"@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority"
    )


    # ---------------------------------------------------------------
    # 5. ADMIN DEFAULT ACCOUNT (ONLY USED IN DEV)
    # ---------------------------------------------------------------
    ADMIN_DEFAULT_NAME = os.getenv("ADMIN_DEFAULT_NAME", "Admin")
    ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_DEFAULT_EMAIL")
    ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_DEFAULT_PASSWORD")
    ADMIN_DEFAULT_ROLE = os.getenv("ADMIN_DEFAULT_ROLE", "superadmin")

    # Only required if DEBUG=true
    if DEBUG and not ADMIN_DEFAULT_EMAIL:
        raise ValueError("❌ Missing ADMIN_DEFAULT_EMAIL in .env for dev seeding")

    if DEBUG and not ADMIN_DEFAULT_PASSWORD:
        raise ValueError("❌ Missing ADMIN_DEFAULT_PASSWORD in .env for dev seeding")


    # ---------------------------------------------------------------
    # 6. JWT CONFIGURATION
    # ---------------------------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("❌ Missing JWT_SECRET_KEY in .env")

    JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", 30))
    JWT_REFRESH_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTES", 43200))  # 30 days


settings = Settings()
