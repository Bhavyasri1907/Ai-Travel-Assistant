"""
Dialogue Manager Module for AI Travel Assistant.
Provides conversational responses tailored to the user:
- Connects to Google Gemini / OpenAI when API key is provided for live AI intelligence
- Smart dynamic response generator for hill stations, beaches, itineraries, and foods
- Ensures queries like 'i need more hill stations' receive comprehensive recommendations instead of greetings!
- Visual Place Showcase with images, famous attractions around it, and famous regional foods
"""

from .llm_engine import TravelLLMEngine

class TravelDialogueManager:
    def __init__(self, kb, context_manager, itinerary_generator):
        self.kb = kb
        self.context_manager = context_manager
        self.itinerary_generator = itinerary_generator
        self.llm_engine = TravelLLMEngine(kb)

    def generate_response(self, session_id: str, query: str, nlp_result: dict, api_key: str = None, provider: str = "gemini", conversation_history: list = None) -> dict:
        intent_info = nlp_result["intent"]
        entities = nlp_result["entities"]
        top_intent = intent_info["top_intent"]
        q_lower = query.lower().strip()
        words = q_lower.split()

        # Step 1: Update Context Memory
        update_info = self.context_manager.update_context(session_id, entities, query)
        profile = update_info["current_profile"]
        updated_fields = update_info["updated_fields"]

        reply_text = ""
        itinerary_data = None
        place_showcase = None
        recommended_destinations = []
        quick_suggestions = []

        detected_dest = entities.get("destination") or profile.get("destination")

        # -------------------------------------------------------------
        # 1. IF USER PROVIDED AN API KEY (LIVE GEMINI / OPENAI LLM)
        # -------------------------------------------------------------
        if api_key or self.llm_engine.default_gemini_key or self.llm_engine.default_openai_key:
            llm_res = self.llm_engine.generate_response(
                query=query,
                conversation_history=conversation_history,
                api_key=api_key,
                provider=provider
            )
            reply_text = llm_res["reply_text"]
            place_showcase = llm_res.get("place_showcase")

            # Check if query requests itinerary
            if any(w in q_lower for w in ["plan", "itinerary", "schedule"]) and detected_dest:
                itinerary_data = self.itinerary_generator.generate(profile)

            # Record turn & return
            self.context_manager.record_turn(session_id, query, reply_text, intent_info, entities)
            return {
                "reply_text": reply_text,
                "place_showcase": place_showcase,
                "itinerary": itinerary_data,
                "recommended_destinations": recommended_destinations,
                "quick_suggestions": ["Plan a trip", "Famous food to try", "Places around here"],
                "profile": profile,
                "nlp_analysis": nlp_result
            }

        # -------------------------------------------------------------
        # 2. HILL STATIONS & NATURE (Fix for: 'i need more hill stations')
        # -------------------------------------------------------------
        if any(w in q_lower for w in ["hill station", "hill stations", "hills", "mountains", "snow", "cooler place"]):
            local_res = self.llm_engine._smart_local_generator(query, conversation_history)
            reply_text = local_res["reply_text"]
            place_showcase = local_res.get("place_showcase")
            
            quick_suggestions = [
                "Tell me about Manali",
                "Tell me about Ooty",
                "Tell me about Munnar",
                "Plan 3 days in Manali"
            ]

        # -------------------------------------------------------------
        # 3. BEACHES & ISLANDS
        # -------------------------------------------------------------
        elif any(w in q_lower for w in ["beach", "beaches", "sea", "islands", "coastal"]):
            local_res = self.llm_engine._smart_local_generator(query, conversation_history)
            reply_text = local_res["reply_text"]
            place_showcase = local_res.get("place_showcase")
            quick_suggestions = [
                "What about Goa?",
                "Tell me about Bali",
                "Plan a 3-day trip to Goa"
            ]

        # -------------------------------------------------------------
        # 4. PURE GREETINGS (ONLY when query is actually a greeting word alone!)
        # -------------------------------------------------------------
        elif len(words) <= 2 and any(w.strip('!.,?') in ["hlo", "hlw", "helo", "hello", "hi", "hey", "namaste", "yo", "sup"] for w in words):
            greeting_word = "Hlo! 👋" if ("hlo" in q_lower or "hlw" in q_lower) else "Hello! 👋"
            reply_text = (
                f"{greeting_word} Great to connect with you! Where are you planning to travel next?\n\n"
                "Tell me any place you have in mind (like **Hyderabad**, **Goa**, **Jaipur**, **Manali**, or **Paris**), "
                "or ask me recommendations like *'I need more hill stations'*, and I'll show you famous spots around it, food, and photos!\n\n"
                "*(Tip: Click the 🔑 API Key button on the top right to plug in your Gemini or OpenAI key for live ChatGPT responses!)*"
            )
            quick_suggestions = [
                "I need more hill stations",
                "Tell me about Hyderabad",
                "What about Goa?",
                "Plan a 4-day trip to Bengaluru under ₹12,000"
            ]

        # -------------------------------------------------------------
        # 5. PLACE INQUIRY & VISUAL SHOWCASE (Images, Famous Places Around, Famous Foods)
        # -------------------------------------------------------------
        elif top_intent == "PLACE_INQUIRY" or (detected_dest and not entities.get("duration_days") and not entities.get("budget_inr") and top_intent not in ["TRANSPORT_WEATHER_BUDGET"]):
            dest_name = detected_dest or "Hyderabad"
            dest_data = self.kb.get_destination(dest_name)
            if not dest_data:
                dest_data = self.kb.get_destination("hyderabad")

            place_showcase = dest_data
            reply_text = (
                f"✨ **{dest_data['name']}** is a fantastic choice! ({dest_data.get('region', 'Travel Destination')})\n\n"
                f"*{dest_data.get('tagline', '')}*\n\n"
                f"📸 **Here are photos, famous places to visit around {dest_data['name']}, and iconic local foods you must try:**"
            )

            quick_suggestions = [
                f"Plan a 3-day trip to {dest_data['name']}",
                f"What is the budget for {dest_data['name']}?",
                f"Places around {dest_data['name']}",
                "Suggest another destination"
            ]

        # -------------------------------------------------------------
        # 6. CONTEXTUAL REFINEMENT TURN (Multi-Turn Flow)
        # -------------------------------------------------------------
        elif profile.get("destination") and len(updated_fields) > 0 and top_intent not in ["GREETING", "DESTINATION_RECOMMENDATION"]:
            dest = profile["destination"]
            dur = profile.get("duration") or "3 days"
            
            if "budget" in updated_fields and "activities" in updated_fields:
                reply_text = f"✨ **Updated your plan!** I've adjusted your **{dur} {dest}** itinerary to fit your budget of **{profile['budget']}** and included **{', '.join(profile['activities'])}** activities."
            elif "budget" in updated_fields:
                reply_text = f"💰 **Budget Updated!** I'll adjust your **{dur} {dest}** plan to fit your budget of **{profile['budget']}**. Here is your updated cost allocation and itinerary."
            elif "activities" in updated_fields:
                act_str = ", ".join(profile["activities"])
                reply_text = f"🏄 **Preferences Added!** I'll include suitable **{act_str}** activities into your **{dest}** itinerary."
            else:
                reply_text = f"🗺️ **Updated Itinerary for {dest}** based on your latest preferences."

            itinerary_data = self.itinerary_generator.generate(profile)
            dest_data = self.kb.get_destination(dest)
            if dest_data:
                place_showcase = dest_data

            if not profile.get("budget"):
                quick_suggestions.append("My budget is ₹15,000")
            if "adventure" not in profile.get("activities", []):
                quick_suggestions.append("I like adventure activities")
            quick_suggestions.append(f"Famous food to try in {dest}")

        # -------------------------------------------------------------
        # 7. TRIP PLANNING INTENT (Itinerary + Visuals)
        # -------------------------------------------------------------
        elif top_intent == "TRIP_PLANNING" or entities.get("destination"):
            dest_name = profile.get("destination") or "Hyderabad"
            dur_days = profile.get("duration_days") or 3
            
            itinerary_data = self.itinerary_generator.generate(profile)
            dest_data = self.kb.get_destination(dest_name)
            if dest_data:
                place_showcase = dest_data

            reply_text = (
                f"🎉 **Sure! I've crafted a personalized {dur_days}-day itinerary for {dest_name}!**\n\n"
                f"📍 **Destination:** {dest_name} • {dur_days} Days\n"
                f"💰 **Estimated Budget:** {itinerary_data.get('total_budget_formatted')} ({itinerary_data.get('tier')})\n"
                f"🌤️ **Best Season:** {dest_data.get('best_season') if dest_data else 'October to March'}\n\n"
                "Take a look at the photos, famous attractions, and day-wise schedule below. "
                "You can refine this plan anytime by telling me your budget or favourite activities!"
            )

            if not profile.get("budget"):
                quick_suggestions.append("My budget is ₹15,000")
            if not profile.get("activities"):
                quick_suggestions.append("I like adventure activities")
            quick_suggestions.append(f"Famous food to try in {dest_name}")
            quick_suggestions.append(f"Places around {dest_name}")

        # -------------------------------------------------------------
        # 8. GENERAL / DEFAULT ADAPTIVE RESPONSE
        # -------------------------------------------------------------
        else:
            local_res = self.llm_engine._smart_local_generator(query, conversation_history)
            reply_text = local_res["reply_text"]
            place_showcase = local_res.get("place_showcase")
            quick_suggestions = [
                "I need more hill stations",
                "Tell me about Hyderabad",
                "What about Goa?",
                "Plan a 4-day trip to Bengaluru under ₹12,000"
            ]

        # Record conversation turn
        self.context_manager.record_turn(session_id, query, reply_text, intent_info, entities)

        return {
            "reply_text": reply_text,
            "place_showcase": place_showcase,
            "itinerary": itinerary_data,
            "recommended_destinations": recommended_destinations,
            "quick_suggestions": quick_suggestions,
            "profile": profile,
            "nlp_analysis": nlp_result
        }
