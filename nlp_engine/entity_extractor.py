"""
Entity Extraction Module for AI Travel Assistant.
Extracts travel entities from queries:
- Destination (Bengaluru, Hyderabad, Goa, Jaipur, Paris, Bali, Dubai, etc., and arbitrary place names)
- Duration (e.g., 4-day, 3 days, weekend -> 2 days)
- Budget (e.g., ₹12,000, 15k, under 10000)
- Activities / Interests (adventure, history, scuba, food, beaches)
- Food Preferences (biryani, seafood, vegetarian, street food)
- Travel Style (solo, family, couple, budget, luxury)
- Travel Dates / Season (weekend, December, summer, winter)
"""

import re

class TravelEntityExtractor:
    def __init__(self):
        # Known destinations & aliases
        self.destination_gazetteer = {
            "hyderabad": ["hyderabad", "hyd", "cyberabad", "secunderabad"],
            "goa": ["goa", "panaji", "baga", "calangute"],
            "bengaluru": ["bengaluru", "bangalore", "blr"],
            "jaipur": ["jaipur", "pink city"],
            "manali": ["manali", "kullu manali", "solang"],
            "kerala": ["kerala", "munnar", "alleppey", "alappuzha", "kochi", "cochin"],
            "ooty": ["ooty", "udhagamandalam", "nilgiris", "coonoor"],
            "varanasi": ["varanasi", "kashi", "banaras", "benares"],
            "agra": ["agra", "taj mahal"],
            "mumbai": ["mumbai", "bombay"],
            "delhi": ["delhi", "new delhi"],
            "paris": ["paris", "france"],
            "bali": ["bali", "ubud", "indonesia"],
            "dubai": ["dubai", "uae"],
            "shimla": ["shimla"],
            "ladakh": ["ladakh", "leh"],
            "udaipur": ["udaipur"],
            "rishikesh": ["rishikesh"],
            "pondicherry": ["pondicherry", "puducherry"],
            "darjeeling": ["darjeeling"],
            "tokyo": ["tokyo", "japan"],
            "london": ["london", "uk"]
        }

        # Activity keywords
        self.activity_keywords = {
            "adventure": ["adventure", "trekking", "hiking", "water sports", "scuba", "scuba diving", "paragliding", "rafting", "parasailing", "kayaking", "safari", "camping"],
            "history": ["history", "historical", "heritage", "monuments", "forts", "palaces", "museums", "architecture", "ancient"],
            "beach": ["beach", "beaches", "sea", "coastal", "ocean", "waves", "shacks", "sunbathing"],
            "nightlife": ["nightlife", "clubs", "pubs", "bars", "parties", "casino", "live music"],
            "nature": ["nature", "tea gardens", "hills", "mountains", "waterfalls", "greenery", "wildlife", "botanical", "lakes", "backwaters", "forest"],
            "spiritual": ["spiritual", "temples", "ghats", "aarti", "pilgrimage", "prayers", "darshan"],
            "relaxation": ["relax", "relaxation", "peaceful", "calm", "leisure", "chill", "spa", "ayurveda"],
            "shopping": ["shopping", "bazaars", "markets", "pearls", "handicrafts", "textiles", "souvenirs"]
        }

        # Food keywords
        self.food_keywords = {
            "local cuisine": ["local food", "local cuisine", "traditional food", "authentic food"],
            "biryani": ["biryani", "dum biryani", "hyderabadi biryani"],
            "street food": ["street food", "chaat", "kachori", "samosa", "panipuri", "street bites"],
            "seafood": ["seafood", "fish curry", "prawns", "fish", "crab"],
            "vegetarian": ["veg", "vegetarian", "pure veg", "jain food"],
            "desserts": ["dessert", "sweets", "mithai", "ghewar", "chocolates", "ice cream"]
        }

        # Travel styles
        self.style_keywords = {
            "solo": ["solo", "alone", "myself", "by myself"],
            "couple": ["couple", "honeymoon", "partner", "wife", "husband", "romantic"],
            "family": ["family", "parents", "kids", "children"],
            "friends": ["friends", "buddies", "gang", "group"],
            "budget": ["budget", "cheap", "backpacking", "affordable", "low cost", "pocket friendly"],
            "luxury": ["luxury", "luxurious", "5 star", "resort", "premium", "lavish"]
        }

    def extract_entities(self, query: str) -> dict:
        """Extracts all entities and returns structured output with entity tags and spans."""
        q_lower = query.lower()
        extracted = {
            "destination": None,
            "destination_canonical": None,
            "duration": None,
            "duration_days": None,
            "budget": None,
            "budget_inr": None,
            "activities": [],
            "food_preferences": [],
            "travel_style": None,
            "timing_or_season": None,
            "entity_spans": []
        }

        # Exclude greetings from being treated as destinations
        greeting_words = {"hlo", "hlw", "helo", "hello", "hi", "hey", "namaste", "yo", "sup", "thanks"}
        if q_lower.strip() in greeting_words:
            return extracted

        # 1. Extract Destination from Gazetteer
        for canonical, aliases in self.destination_gazetteer.items():
            for alias in aliases:
                pattern = r'\b' + re.escape(alias) + r'\b'
                match = re.search(pattern, q_lower)
                if match:
                    extracted["destination"] = alias.title()
                    extracted["destination_canonical"] = canonical
                    extracted["entity_spans"].append({
                        "entity": "Destination",
                        "value": alias.title(),
                        "start": match.start(),
                        "end": match.end()
                    })
                    break
            if extracted["destination"]:
                break

        # 1b. Dynamic extraction if destination not in gazetteer:
        # e.g. "tell me about Pondicherry", "places in Shimla", "what about Tokyo"
        if not extracted["destination"]:
            dynamic_patterns = [
                r'\b(?:tell me about|what about|explore|details (?:of|for|about)|visit|trip to|travel to|going to|fly to|places in|places around|attractions in|food in)\s+([A-Za-z\s]+?)(?:\s*(?:under|for|\?|\.|$))',
                r'\babout\s+([A-Za-z]+)\b'
            ]
            for pat in dynamic_patterns:
                m = re.search(pat, query, re.I)
                if m:
                    candidate = m.group(1).strip()
                    if candidate.lower() not in greeting_words and len(candidate) > 2:
                        extracted["destination"] = candidate.title()
                        extracted["destination_canonical"] = candidate.lower()
                        extracted["entity_spans"].append({
                            "entity": "Destination",
                            "value": candidate.title(),
                            "start": m.start(1),
                            "end": m.end(1)
                        })
                        break

        # If user just sent a single word like "Hyderabad", "Goa", "Paris", "Manali"
        if not extracted["destination"] and len(query.strip().split()) == 1 and query.strip().lower() not in greeting_words:
            candidate = query.strip()
            if len(candidate) > 2 and candidate.isalpha():
                extracted["destination"] = candidate.title()
                extracted["destination_canonical"] = candidate.lower()
                extracted["entity_spans"].append({
                    "entity": "Destination",
                    "value": candidate.title(),
                    "start": 0,
                    "end": len(candidate)
                })

        # 2. Extract Duration
        duration_patterns = [
            (r'(\d+)\s*-(?:day|days)', lambda m: (int(m.group(1)), f"{m.group(1)}-day")),
            (r'(\d+)\s+(?:day|days)', lambda m: (int(m.group(1)), f"{m.group(1)} days")),
            (r'(\d+)\s+(?:night|nights)', lambda m: (int(m.group(1)) + 1, f"{m.group(1)} nights")),
            (r'\b(weekend)\b', lambda m: (2, "Weekend (2 days)")),
            (r'\b(one|a)\s+week\b', lambda m: (7, "1 week (7 days)")),
            (r'\bfor\s+(\d+)\s+days?\b', lambda m: (int(m.group(1)), f"{m.group(1)} days"))
        ]
        
        for pat, converter in duration_patterns:
            match = re.search(pat, q_lower)
            if match:
                days, text_val = converter(match)
                extracted["duration_days"] = days
                extracted["duration"] = text_val
                extracted["entity_spans"].append({
                    "entity": "Duration",
                    "value": text_val,
                    "start": match.start(),
                    "end": match.end()
                })
                break

        # 3. Extract Budget
        budget_patterns = [
            r'(?:under|below|around|within|budget of)?\s*[₹$€£]\s*([\d,]+)(?:\s*(?:k|thousand|lakh))?',
            r'(?:under|below|around|within|budget of)?\s*(?:rs\.?|inr)\s*([\d,]+)(?:\s*(?:k|thousand|lakh))?',
            r'(?:under|below|budget of)\s+([\d,]+)(?:\s*(?:k|thousand|lakh|rupees|rs))?',
            r'\b([\d]+)\s*k\b',
            r'\b(\d{4,6})\s*(?:rupees|rs|inr)\b'
        ]

        for pat in budget_patterns:
            match = re.search(pat, q_lower)
            if match:
                raw_str = match.group(0).strip()
                digits_str = match.group(1).replace(',', '') if match.group(1) else ""
                if not digits_str and "k" in raw_str:
                    num_match = re.search(r'(\d+)', raw_str)
                    num = int(num_match.group(1)) * 1000 if num_match else None
                elif digits_str:
                    try:
                        num = int(digits_str)
                        if "k" in raw_str.lower() and num < 1000:
                            num *= 1000
                        elif "lakh" in raw_str.lower():
                            num *= 100000
                    except ValueError:
                        num = None
                else:
                    num = None

                if num:
                    extracted["budget_inr"] = num
                    extracted["budget"] = f"₹{num:,}"
                    extracted["entity_spans"].append({
                        "entity": "Budget",
                        "value": f"₹{num:,}",
                        "start": match.start(),
                        "end": match.end()
                    })
                    break

        # 4. Extract Activities & Interests
        for act_category, keywords in self.activity_keywords.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_lower):
                    if act_category not in extracted["activities"]:
                        extracted["activities"].append(act_category)
                    break

        # 5. Extract Food Preferences
        for food_type, keywords in self.food_keywords.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_lower):
                    if food_type not in extracted["food_preferences"]:
                        extracted["food_preferences"].append(food_type)
                    break

        # 6. Extract Travel Style
        for style, keywords in self.style_keywords.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', q_lower):
                    extracted["travel_style"] = style.capitalize()
                    break
            if extracted["travel_style"]:
                break

        # 7. Extract Timing / Season
        season_matches = re.findall(r'\b(winter|summer|monsoon|autumn|spring|december|january|february|weekend|next week)\b', q_lower)
        if season_matches:
            extracted["timing_or_season"] = season_matches[0].capitalize()

        return extracted
