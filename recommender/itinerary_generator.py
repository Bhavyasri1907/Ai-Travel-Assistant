"""
Itinerary Generator Module for AI Travel Assistant.
Generates structured, day-wise travel plans based on:
Destination, Duration, Budget, Activities/Interests, and Food preferences
(as detailed in Slide 6 & 8 of the project presentation).
"""

class ItineraryGenerator:
    def __init__(self, kb):
        self.kb = kb

    def generate(self, profile: dict) -> dict:
        """
        Synthesizes an itinerary and budget allocation tailored to the user profile.
        """
        dest_canonical = profile.get("destination_canonical") or "hyderabad"
        dest_data = self.kb.get_destination(dest_canonical)

        if not dest_data:
            # Fallback to Hyderabad if destination not recognized
            dest_data = self.kb.get_destination("hyderabad")
            dest_canonical = "hyderabad"

        dest_name = dest_data["name"]
        duration_days = profile.get("duration_days") or 3
        duration_days = max(1, min(duration_days, 5))  # Clamp between 1 and 5 days

        budget_inr = profile.get("budget_inr")
        if not budget_inr:
            budget_inr = dest_data.get("avg_budget_3day", 9000) * (duration_days / 3.0)
            budget_inr = int(round(budget_inr, -2))

        daily_budget = int(budget_inr / duration_days)
        
        # Determine budget tier
        if daily_budget < dest_data.get("min_budget_per_day", 2000):
            tier = "Budget Backpacking (Cost-Effective)"
            tier_badge = "budget"
        elif daily_budget <= dest_data.get("min_budget_per_day", 2000) * 2.2:
            tier = "Standard Comfort (Balanced)"
            tier_badge = "standard"
        else:
            tier = "Premium / Luxury Experience"
            tier_badge = "luxury"

        # Budget Allocation Breakdown
        budget_breakdown = {
            "stay": int(budget_inr * 0.40),
            "food": int(budget_inr * 0.25),
            "activities_entry": int(budget_inr * 0.20),
            "local_commute": int(budget_inr * 0.15)
        }

        # Build Day Plans from templates or knowledge base
        itinerary_templates = dest_data.get("itinerary_templates", {})
        activities_pref = profile.get("activities", [])
        food_pref = profile.get("food_preferences", [])
        
        days_plan = []
        for d in range(1, duration_days + 1):
            key = f"day_{d}"
            template = itinerary_templates.get(key)
            
            if template:
                day_title = template["title"]
                morning = template["morning"]
                afternoon = template["afternoon"]
                evening = template["evening"]
                est_cost = template.get("budget_est", daily_budget)
            else:
                # Fallback generator for extended days
                day_title = f"Day {d}: Exploring Scenic Spots & Local Culture"
                morning = f"Morning visits to famous landmarks and local parks in {dest_name}."
                afternoon = f"Try famous regional dishes at traditional restaurants; leisurely market exploration."
                evening = f"Sunset view followed by casual walking street dinner and souvenir shopping."
                est_cost = daily_budget

            # Customize text if user expressed specific activity preferences
            if "adventure" in activities_pref and "adventure" in dest_data.get("tags", []):
                evening += " (Includes outdoor excitement or thrill sports sessions)"
            if "history" in activities_pref and "history" in dest_data.get("tags", []):
                morning = f"[Historical Landmark Tour] {morning}"
            if "biryani" in food_pref and "biryani" in " ".join(dest_data.get("foods", [])).lower():
                afternoon += " Special recommendation: Taste authentic local Biryani!"

            days_plan.append({
                "day_number": d,
                "title": day_title,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
                "estimated_cost": est_cost,
                "highlight_spots": [att["name"] for att in dest_data.get("attractions", [])[(d-1)*2 : d*2]]
            })

        return {
            "destination": dest_name,
            "region": dest_data.get("region"),
            "category": dest_data.get("category"),
            "tagline": dest_data.get("tagline"),
            "duration_days": duration_days,
            "duration_label": f"{duration_days}-Day Itinerary",
            "total_budget": budget_inr,
            "total_budget_formatted": f"₹{budget_inr:,}",
            "daily_budget_formatted": f"₹{daily_budget:,}/day",
            "tier": tier,
            "tier_badge": tier_badge,
            "budget_breakdown": budget_breakdown,
            "best_season": dest_data.get("best_season"),
            "foods_to_try": dest_data.get("foods", []),
            "transport_info": dest_data.get("transport", {}),
            "days": days_plan,
            "top_attractions": dest_data.get("attractions", [])
        }
