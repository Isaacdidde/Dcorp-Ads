from datetime import datetime, timedelta

def compute_pacing(campaign):
    budget = campaign.get("budget", 0)
    spend = campaign.get("spend", 0)
    created_at = campaign.get("created_at", datetime.utcnow())

    days_running = (datetime.utcnow() - created_at).days + 1

    if spend <= 0 or days_running <= 0:
        return {
            "daily_burn": 0,
            "remaining_days": None,
            "projected_end": None,
            "message": "Not enough data"
        }

    daily_burn = spend / days_running
    remaining_budget = budget - spend

    if daily_burn <= 0:
        return {
            "daily_burn": 0,
            "remaining_days": None,
            "projected_end": None,
            "message": "Spend pace is zero"
        }

    remaining_days = remaining_budget / daily_burn
    projected_end = datetime.utcnow() + timedelta(days=remaining_days)

    return {
        "daily_burn": round(daily_burn, 2),
        "remaining_days": round(remaining_days, 1),
        "projected_end": projected_end.strftime("%d %b %Y"),
        "message": "Healthy pacing" if remaining_days > 3 else "Budget depleting soon"
    }
