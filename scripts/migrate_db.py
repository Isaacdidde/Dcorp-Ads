"""
Database Migration Script

Initializes required collections + indexes for the DCorp Ads Platform.

Run:
    python scripts/migrate_db.py
"""

from database.connection import get_db
from datetime import datetime


def migrate():
    db = get_db()
    print("\n=== Running Database Migration ===\n")

    # ------------------------------
    # USERS COLLECTION
    # ------------------------------
    users = db.get_collection("users")

    users.create_index("email", unique=True)
    print("[OK] users: unique index on email")

    users.create_index("role")
    print("[OK] users: index on role")

    # ------------------------------
    # PRODUCTS COLLECTION
    # ------------------------------
    products = db.get_collection("products")

    products.create_index("code", unique=True)
    print("[OK] products: unique index on code")

    # ------------------------------
    # ADVERTISERS COLLECTION
    # ------------------------------
    advertisers = db.get_collection("advertisers")

    advertisers.create_index("email", unique=True)
    print("[OK] advertisers: unique index on email")

    advertisers.create_index("wallet_balance")
    print("[OK] advertisers: index on wallet_balance")

    # ------------------------------
    # CAMPAIGNS COLLECTION
    # ------------------------------
    campaigns = db.get_collection("campaigns")

    campaigns.create_index([("advertiser_id", 1)])
    print("[OK] campaigns: index on advertiser_id")

    campaigns.create_index([("status", 1)])
    print("[OK] campaigns: index on status")

    # ------------------------------
    # ADS COLLECTION
    # ------------------------------
    ads = db.get_collection("ads")

    ads.create_index([("campaign_id", 1)])
    print("[OK] ads: index on campaign_id")

    ads.create_index([("status", 1)])
    print("[OK] ads: index on status")

    ads.create_index([("targeting.device", 1)])
    print("[OK] ads: index on targeting.device")

    # ------------------------------
    # ANALYTICS COLLECTION
    # ------------------------------
    analytics = db.get_collection("analytics")

    analytics.create_index([("timestamp", -1)])
    print("[OK] analytics: index on timestamp")

    analytics.create_index([("product_code", 1)])
    print("[OK] analytics: index on product_code")

    analytics.create_index([("event", 1)])
    print("[OK] analytics: index on event type")

    # TTL example (optional):
    # analytics.create_index("timestamp", expireAfterSeconds=90*24*3600)

    # ------------------------------
    # TRANSACTIONS COLLECTION
    # ------------------------------
    transactions = db.get_collection("transactions")

    transactions.create_index([("advertiser_id", 1)])
    print("[OK] transactions: index on advertiser_id")

    transactions.create_index([("type", 1)])
    print("[OK] transactions: index on type")

    print("\n=== Migration Completed Successfully ===\n")


if __name__ == "__main__":
    migrate()
