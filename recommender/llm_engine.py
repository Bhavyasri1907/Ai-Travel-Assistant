"""
LLM Engine for TravelGPT.
Provides dynamic, flexible AI conversational responses using:
1. Google Gemini API (gemini-1.5-flash, gemini-2.0-flash)
2. OpenAI API (gpt-4o-mini, gpt-4o)
3. Smart Dynamic Local Recommender (when no API key is provided)
"""

import os
import re
import json

class TravelLLMEngine:
    def __init__(self, kb):
        self.kb = kb
        self.default_gemini_key = (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        self.default_openai_key = os.environ.get("OPENAI_API_KEY")

    def generate_response(self, query: str, conversation_history: list = None, api_key: str = None, provider: str = "gemini") -> dict:
        """
        Generates dynamic conversational response using LLM if key is available,
        or falls back cleanly to the smart dynamic knowledge generator without showing any errors.
        """
        key = api_key or self.default_gemini_key or self.default_openai_key
        provider = (provider or "gemini").lower()

        # If user provided a key (or default key is set), call LLM
        if key:
            try:
                if provider == "openai" or key.startswith("sk-"):
                    return self._call_openai(query, conversation_history, key)
                else:
                    return self._call_gemini(query, conversation_history, key)
            except Exception as e:
                print(f"LLM API error ({provider}): {e}")
                # Fall back cleanly without exposing technical 404/API errors to user
                return self._smart_local_generator(query, conversation_history)

        # Use smart dynamic local response generator
        return self._smart_local_generator(query, conversation_history)

    def _call_gemini(self, query: str, history: list, key: str) -> dict:
        """Calls Google Gemini API with fallback across active flash models."""
        import google.generativeai as genai
        genai.configure(api_key=key)

        supported_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest"
        ]

        system_instruction = (
            "You are TravelGPT, an enthusiastic, knowledgeable and conversational AI travel companion. "
            "You answer questions about travel destinations, itineraries, hill stations, beaches, local cuisines, "
            "budget planning, packing tips, and famous spots worldwide. "
            "Be conversational, engaging, friendly and helpful. Format responses with clean Markdown (bullet points, bold text). "
            "Never give robotic or canned answers. Always address the user's specific request directly."
        )

        chat_history = []
        if history:
            for turn in history[-6:]:  # Keep recent context
                role = "user" if turn.get("sender") == "user" else "model"
                text = turn.get("text", "")
                if text:
                    chat_history.append({"role": role, "parts": [text]})

        last_error = None
        for model_name in supported_models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                chat = model.start_chat(history=chat_history)
                resp = chat.send_message(query)
                reply_text = resp.text

                # Detect any primary destination mentioned to provide visual card
                place_data = self._detect_place_showcase(query, reply_text)

                return {
                    "reply_text": reply_text,
                    "place_showcase": place_data,
                    "source": f"Gemini AI ({model_name})"
                }
            except Exception as ex:
                last_error = ex
                continue

        raise last_error or Exception("No Gemini models responded")

    def _call_openai(self, query: str, history: list, key: str) -> dict:
        """Calls OpenAI API."""
        from openai import OpenAI
        client = OpenAI(api_key=key)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are TravelGPT, an enthusiastic, knowledgeable and conversational AI travel companion. "
                    "You answer questions about travel destinations, itineraries, hill stations, beaches, local cuisines, "
                    "budget planning, packing tips, and famous spots worldwide. "
                    "Be conversational, engaging, friendly and helpful. Format responses with clean Markdown. "
                    "Never give robotic or canned answers. Always address the user's specific request directly."
                )
            }
        ]

        if history:
            for turn in history[-6:]:
                role = "user" if turn.get("sender") == "user" else "assistant"
                text = turn.get("text", "")
                if text:
                    messages.append({"role": role, "content": text})

        messages.append({"role": "user", "content": query})

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        reply_text = completion.choices[0].message.content
        place_data = self._detect_place_showcase(query, reply_text)

        return {
            "reply_text": reply_text,
            "place_showcase": place_data,
            "source": "OpenAI API (Live AI)"
        }

    def _detect_place_showcase(self, query: str, reply: str) -> dict | None:
        """Finds if a major destination was discussed and attaches rich photo cards."""
        q_lower = query.lower()
        
        # Check all destinations in KB
        for dest in self.kb.get_all_destinations():
            name = dest["name"].lower()
            if name in q_lower:
                return dest

        # Check in reply for primary destination
        for dest in self.kb.get_all_destinations():
            name = dest["name"].lower()
            if name in q_lower or f"**{name}**" in reply.lower():
                return dest

        # Check common city keywords in query
        words = re.findall(r'\b[A-Z][a-z]+\b', query)
        for w in words:
            if w.lower() not in ["i", "plan", "trip", "days", "budget", "need", "more", "what", "where"]:
                synth = self.kb.get_destination(w)
        # Check hill stations or beaches category
        if any(h in q_lower for h in ["hill station", "hill stations", "mountain", "hills", "snow"]):
            return self.kb.get_destination("manali")
        if any(b in q_lower for b in ["beach", "beaches", "coastal", "sea"]):
            return self.kb.get_destination("goa")

        return None

    def _smart_local_generator(self, query: str, history: list = None) -> dict:
        """
        Intelligent dynamic generator for when no API key is set or when API rate limits occur.
        Cleanly generates rich destination guides without showing technical errors to the user.
        """
        q_lower = query.lower().strip()
        words = q_lower.split()

        # -----------------------------------------------------------------
        # A. HILL STATIONS (User Screenshot Fix: 'i need more hill stations')
        # -----------------------------------------------------------------
        if any(w in q_lower for w in ["hill station", "hill stations", "hills", "mountains", "snow", "cooler place"]):
            reply_text = (
                "🏔️ **Here are the Best Hill Stations for your trip, categorized by vibes:**\n\n"
                "### 1. **Manali (Himachal Pradesh)** — *Adventure & Snowy Peaks*\n"
                "- **Highlights:** Solang Valley, Rohtang Pass, Atal Tunnel, Old Manali boho cafes.\n"
                "- **Best For:** Paragliding, snow activities, deodar forest walks.\n"
                "- **Must-Try Food:** Himachali Siddu with pure ghee, fresh river trout, steamed momos.\n\n"
                "### 2. **Ooty & Coonoor (Tamil Nadu)** — *Queen of Nilgiris & Tea Estates*\n"
                "- **Highlights:** UNESCO Nilgiri Toy Train, Government Botanical Gardens, Doddabetta Peak, Pykara Lake.\n"
                "- **Best For:** Misty weather, scenic toy train rides, pine forest walks.\n"
                "- **Must-Try Food:** Ooty handmade chocolates, Nilgiri varkey, hot herbal tea.\n\n"
                "### 3. **Munnar (Kerala)** — *Rolling Emerald Tea Plantations*\n"
                "- **Highlights:** KDHP Tea Museum, Eravikulam National Park (Nilgiri Tahr), Mattupetty Dam.\n"
                "- **Best For:** Romantic greenery, misty valley drives, spice plantations.\n"
                "- **Must-Try Food:** Kerala appam with vegetable stew, banana fritters.\n\n"
                "### 4. **Shimla (Himachal Pradesh)** — *Colonial Heritage & Mall Road*\n"
                "- **Highlights:** The Ridge, Christ Church, Jakhu Temple, Kalka-Shimla heritage train.\n"
                "- **Best For:** Family vacations, colonial walking tours, ice skating in winter.\n\n"
                "### 5. **Darjeeling (West Bengal)** — *Kanchenjunga Views & World-Famous Tea*\n"
                "- **Highlights:** Tiger Hill sunrise over Mount Kanchenjunga, Himalayan Mountaineering Institute, Batasia Loop.\n"
                "- **Best For:** Tea garden estates, panoramic snow crests, colonial charm.\n\n"
                "### 6. **Coorg (Kodagu, Karnataka)** — *Coffee Woods & Waterfalls*\n"
                "- **Highlights:** Abbey Falls, Raja's Seat sunset, Dubare Elephant Camp, Tibetan Golden Temple.\n"
                "- **Best For:** Coffee estate homestays, river rafting, peaceful monsoon escapes.\n\n"
                "💬 *Would you like me to show photos, places around, or create a full day-by-day plan for any of these? Just type the name (e.g. 'Tell me about Manali' or 'Plan 3 days in Ooty')!*"
            )
            place = self.kb.get_destination("manali")
            return {"reply_text": reply_text, "place_showcase": place, "source": "Local Travel Engine"}

        # -----------------------------------------------------------------
        # B. BEACHES & COASTAL GETAWAYS
        # -----------------------------------------------------------------
        if any(w in q_lower for w in ["beach", "beaches", "sea", "coastal", "islands"]):
            reply_text = (
                "🏖️ **Top Beach Getaways in India & Nearby:**\n\n"
                "1. **Goa** — *Water sports, vibrant beach shacks, Portuguese forts, and nightlife.*\n"
                "2. **Gokarna (Karnataka)** — *Peaceful, pristine beaches (Om Beach, Kudle) with cliffside trekking.*\n"
                "3. **Andaman & Nicobar Islands** — *Radhanagar Beach, turquoise coral reefs, scuba diving & bioluminescence.*\n"
                "4. **Varkala (Kerala)** — *Unique red cliffs overlooking the Arabian Sea with bohemian cafes.*\n"
                "5. **Pondicherry** — *French colonial promenades, Promenade Beach, surfing at Serenity Beach.*\n\n"
                "Ask me about any of these to see famous places around them and food to try!"
            )
            place = self.kb.get_destination("goa")
            return {"reply_text": reply_text, "place_showcase": place, "source": "Local Travel Engine"}

        # -----------------------------------------------------------------
        # C. SPECIFIC DESTINATION INQUIRY (e.g. 'Tell me about Hyderabad', 'Goa', 'Paris')
        # -----------------------------------------------------------------
        dest = None
        for d in self.kb.get_all_destinations():
            if d["name"].lower() in q_lower:
                dest = d
                break
        
        # If user typed just a single word like 'Paris', 'Jaipur', 'Hyderabad'
        if not dest and len(words) <= 3:
            for w in words:
                synth = self.kb.get_destination(w)
                if synth and synth.get("name").lower() in q_lower:
                    dest = synth
                    break

        if dest:
            reply_text = (
                f"✨ **{dest['name']}** is an amazing destination! ({dest.get('region', '')})\n\n"
                f"*{dest.get('tagline', '')}*\n\n"
                f"🌤️ **Best Time to Visit:** {dest.get('best_season', 'October to March')}\n"
                f"💰 **Estimated 3-Day Budget:** ₹{dest.get('avg_budget_3day', 9000):,} ({dest.get('min_budget_per_day', 2000):,}/day)\n\n"
                f"📸 **Check out the photos, famous places around {dest['name']}, and signature foods below:**"
            )
            return {"reply_text": reply_text, "place_showcase": dest, "source": "Local Travel Engine"}

        # -----------------------------------------------------------------
        # D. PURE GREETINGS (Only when query is actually just a greeting!)
        # -----------------------------------------------------------------
        greeting_words = {"hlo", "hlw", "helo", "hello", "hi", "hey", "namaste", "yo", "sup", "greetings"}
        if len(words) <= 2 and any(w.strip('!.,?') in greeting_words for w in words):
            greeting = "Hlo! 👋" if ("hlo" in q_lower or "hlw" in q_lower) else "Hello! 👋"
            reply_text = (
                f"{greeting} I'm your AI Travel Assistant. Where are you dreaming of traveling next?\n\n"
                "You can ask me anything, such as:\n"
                "- *'I need more hill stations'*\n"
                "- *'Tell me about Hyderabad'*\n"
                "- *'What about Goa?'*\n"
                "- *'Plan a 4-day trip to Bengaluru under ₹12,000'*"
            )
            return {"reply_text": reply_text, "place_showcase": None, "source": "Local Travel Engine"}

        # -----------------------------------------------------------------
        # E. DEFAULT ADAPTIVE RESPONSE
        # -----------------------------------------------------------------
        reply_text = (
            f"I understand you're asking: *\"{query}\"*\n\n"
            "I can help you explore destinations, find famous places around any city, recommend iconic local foods, "
            "or generate a day-wise itinerary matching your budget!\n\n"
            "Tell me more about what you're looking for—like preferred regions (North, South, Coastal, Hills), "
            "your approximate budget, or specific places you'd like to visit."
        )
        return {"reply_text": reply_text, "place_showcase": None, "source": "Local Travel Engine"}
