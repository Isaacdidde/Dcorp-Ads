"""
MongoDB Index Definitions for all Ads Collections

Indexes are optimized for:
• Fast bidding engine lookups
• High-volume impression/click recording
• Efficient analytics queries
• Low-latency slot → eligible campaigns selection

Run this file once at startup or via a management command.
"""

from database.connection import get_collection
from pymongo import ASCENDING, DESCENDING, HASHED


def create_indexes():
    print("\n🛠 Creating MongoDB Indexes for Ads System…\n")

    # ---------------------------------------------------------
    # 1. AD CAMPAIGNS (Main collection used by bidding engine)
    # ---------------------------------------------------------
    campaigns = get_collection("ad_campaigns")

    campaigns.create_index([("status", ASCENDING)])
    campaigns.create_index([("slot_id", ASCENDING)])
    campaigns.create_index([("budget", DESCENDING)])
    campaigns.create_index([("bid_amount", DESCENDING)])

    # Most important index for bidding:
    campaigns.create_index(
        [("slot_id", ASCENDING), ("status", ASCENDING), ("budget", DESCENDING), ("bid_amount", DESCENDING)],
        name="slot_status_budget_bid_index"
    )

    # Lookup by advertiser
    campaigns.create_index([("user_id", ASCENDING)], name="campaign_user_lookup")

    # By creation time
    campaigns.create_index([("created_at", DESCENDING)])


    # ---------------------------------------------------------
    # 2. AD CREATIVES
    # ---------------------------------------------------------
    creatives = get_collection("ad_creatives")

    creatives.create_index([("campaign_id", ASCENDING)], name="creative_campaign_lookup")
    creatives.create_index([("slot_id", ASCENDING)], name="creative_slot_lookup")
    creatives.create_index([("status", ASCENDING)], name="creative_status_lookup")
    creatives.create_index([("created_at", DESCENDING)])


    # ---------------------------------------------------------
    # 3. AD SLOTS
    # ---------------------------------------------------------
    ad_slots = get_collection("ad_slots")

    ad_slots.create_index([("slot_id", ASCENDING)], unique=True, name="unique_slot_id")


    # ---------------------------------------------------------
    # 4. IMPRESSIONS LOG
    # ---------------------------------------------------------
    imps = get_collection("ads_impressions")

    imps.create_index([("campaign_id", ASCENDING), ("timestamp", DESCENDING)], name="imp_campaign_time")
    imps.create_index([("slot_id", ASCENDING), ("timestamp", DESCENDING)], name="imp_slot_time")

    # IP analytics (optional, hashed is efficient)
    imps.create_index([("ip", HASHED)], name="imp_ip_lookup")

    # Time-based queries
    imps.create_index([("timestamp", DESCENDING)], name="imp_time_desc")


    # ---------------------------------------------------------
    # 5. CLICKS LOG
    # ---------------------------------------------------------
    clicks = get_collection("ads_clicks")

    clicks.create_index([("campaign_id", ASCENDING), ("timestamp", DESCENDING)], name="click_campaign_time")
    clicks.create_index([("slot_id", ASCENDING), ("timestamp", DESCENDING)], name="click_slot_time")

    clicks.create_index([("ip", HASHED)], name="click_ip_lookup")
    clicks.create_index([("timestamp", DESCENDING)], name="click_time_desc")


    # ---------------------------------------------------------
    # 6. AD TRACKING (optional merged tracking collection)
    # ---------------------------------------------------------
    tracking = get_collection("ad_tracking")

    tracking.create_index([("event", ASCENDING)], name="track_event_type")
    tracking.create_index([("campaign_id", ASCENDING)], name="track_campaign_lookup")
    tracking.create_index([("slot_id", ASCENDING)], name="track_slot_lookup")
    tracking.create_index([("timestamp", DESCENDING)], name="track_time_desc")

    print("\n✅ MongoDB Ads Indexes Created Successfully!\n")
