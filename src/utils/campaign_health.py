# utils/campaign_health.py

def compute_campaign_health(campaign):
    """
    Always returns a dict:
      { "score": int, "message": str }
    """

    # Extract values safely
    impressions = campaign.get("impressions", 0)
    clicks = campaign.get("clicks", 0)
    budget = campaign.get("budget", 0)
    spend = campaign.get("spend", 0)

    # Basic CTR-based score
    ctr = (clicks / impressions * 100) if impressions > 0 else 0

    # Spend ratio (lower is better)
    spend_ratio = (spend / budget * 100) if budget > 0 else 0

    # Compute combined score
    score = 0

    # CTR contribution (max 60)
    score += min(60, ctr * 1.5)

    # Spend balance contribution (max 40)
    if spend_ratio < 50:
        score += 35
    elif spend_ratio < 80:
        score += 25
    elif spend_ratio < 120:
        score += 10

    # Clamp score between 0–100
    score = int(max(0, min(100, score)))

    # Determine message
    if score >= 70:
        message = "Healthy — strong deliverability"
    elif score >= 40:
        message = "Moderate — needs monitoring"
    else:
        message = "Poor — action required"

    return {
        "score": score,
        "message": message
    }
