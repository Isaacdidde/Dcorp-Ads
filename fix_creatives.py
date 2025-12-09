from database.connection import get_collection
from bson import ObjectId

creatives = get_collection("ad_creatives")
campaigns = get_collection("campaigns")

print("Fixing creatives...")

count = 0

for cre in creatives.find():
    cid = cre.get("campaign_id")

    # Convert ObjectId → string
    if isinstance(cid, ObjectId):
        cid_str = str(cid)
        creatives.update_one(
            {"_id": cre["_id"]},
            {"$set": {"campaign_id": cid_str}}
        )
        cid = cid_str
        count += 1

    # Sync creative status with campaign status
    camp = campaigns.find_one({"_id": ObjectId(cid)})
    if camp:
        creatives.update_one(
            {"_id": cre["_id"]},
            {"$set": {"status": camp.get("creative_status", "pending")}}
        )

print(f"Done. Updated {count} creatives.")
