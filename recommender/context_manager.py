"""
Context Management Module for AI Travel Assistant.
Implements multi-turn dialogue memory and progressive traveler profile building
matching Slide 7 of the project specification.
"""

from datetime import datetime

class UserTravelProfile:
    def __init__(self):
        self.destination = None
        self.destination_canonical = None
        self.duration = None
        self.duration_days = None
        self.budget = None
        self.budget_inr = None
        self.activities = []
        self.food_preferences = []
        self.travel_style = None
        self.timing_or_season = None
        self.turn_count = 0
        self.last_updated = datetime.now()

    def to_dict(self) -> dict:
        return {
            "destination": self.destination,
            "destination_canonical": self.destination_canonical,
            "duration": self.duration,
            "duration_days": self.duration_days,
            "budget": self.budget,
            "budget_inr": self.budget_inr,
            "activities": self.activities,
            "food_preferences": self.food_preferences,
            "travel_style": self.travel_style,
            "timing_or_season": self.timing_or_season,
            "turn_count": self.turn_count
        }

class TravelContextManager:
    def __init__(self):
        self.sessions = {}

    def get_or_create_session(self, session_id: str = "default") -> dict:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "profile": UserTravelProfile(),
                "history": [],
                "created_at": datetime.now()
            }
        return self.sessions[session_id]

    def update_context(self, session_id: str, entities: dict, query_text: str) -> dict:
        """
        Updates traveler profile with newly extracted entities across conversational turns.
        Returns a dict of newly updated fields to enable conversational acknowledgment.
        """
        session = self.get_or_create_session(session_id)
        profile: UserTravelProfile = session["profile"]
        profile.turn_count += 1
        profile.last_updated = datetime.now()

        updated_fields = []

        # 1. Update Destination
        if entities.get("destination"):
            if profile.destination != entities["destination"]:
                profile.destination = entities["destination"]
                profile.destination_canonical = entities.get("destination_canonical")
                updated_fields.append("destination")

        # 2. Update Duration
        if entities.get("duration_days"):
            if profile.duration_days != entities["duration_days"]:
                profile.duration_days = entities["duration_days"]
                profile.duration = entities.get("duration")
                updated_fields.append("duration")

        # 3. Update Budget
        if entities.get("budget_inr"):
            if profile.budget_inr != entities["budget_inr"]:
                profile.budget_inr = entities["budget_inr"]
                profile.budget = entities.get("budget")
                updated_fields.append("budget")

        # 4. Update Activities
        for act in entities.get("activities", []):
            if act not in profile.activities:
                profile.activities.append(act)
                if "activities" not in updated_fields:
                    updated_fields.append("activities")

        # 5. Update Food Preferences
        for food in entities.get("food_preferences", []):
            if food not in profile.food_preferences:
                profile.food_preferences.append(food)
                if "food_preferences" not in updated_fields:
                    updated_fields.append("food_preferences")

        # 6. Update Travel Style
        if entities.get("travel_style"):
            profile.travel_style = entities["travel_style"]
            updated_fields.append("travel_style")

        # 7. Update Season
        if entities.get("timing_or_season"):
            profile.timing_or_season = entities["timing_or_season"]
            updated_fields.append("timing_or_season")

        return {
            "current_profile": profile.to_dict(),
            "updated_fields": updated_fields,
            "turn_number": profile.turn_count
        }

    def record_turn(self, session_id: str, query: str, response: str, intent: dict, entities: dict):
        """Records a completed conversation turn for dialogue history."""
        session = self.get_or_create_session(session_id)
        session["history"].append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "query": query,
            "response": response,
            "intent": intent.get("top_intent"),
            "confidence": intent.get("confidence_percent"),
            "entities": entities
        })

    def get_profile(self, session_id: str = "default") -> dict:
        session = self.get_or_create_session(session_id)
        return session["profile"].to_dict()

    def reset_session(self, session_id: str = "default"):
        """Clears memory and starts a fresh conversation session."""
        self.sessions[session_id] = {
            "profile": UserTravelProfile(),
            "history": [],
            "created_at": datetime.now()
        }
        return {"status": "success", "message": "Context memory reset successfully"}
