"""
NLP Preprocessing Module for AI Travel Assistant.
Implements:
1. Custom Tokenization (preserving amounts like ₹12,000 and phrases like 4-day)
2. Lemmatization (using NLTK WordNetLemmatizer with POS mapping)
3. Stopword Filtering (preserving travel prepositions like 'under', 'for', 'in')
"""

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet

class TravelNLPPreprocessor:
    def __init__(self):
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception:
            self.lemmatizer = None
            
        try:
            # Custom stop words: exclude critical travel words from being dropped
            base_stopwords = set(stopwords.words('english'))
            keep_words = {'under', 'below', 'above', 'for', 'in', 'to', 'with', 'and', 'not', 'day', 'days'}
            self.stopwords = base_stopwords - keep_words
        except Exception:
            self.stopwords = set()
            
        # Custom lemmatization rules for common travel queries
        self.travel_lemma_lookup = {
            "planning": "plan",
            "planned": "plan",
            "plans": "plan",
            "visiting": "visit",
            "visited": "visit",
            "visits": "visit",
            "traveling": "travel",
            "travelling": "travel",
            "travelled": "travel",
            "traveled": "travel",
            "recommending": "recommend",
            "recommendations": "recommend",
            "recommended": "recommend",
            "suggestions": "suggest",
            "suggesting": "suggest",
            "itineraries": "itinerary",
            "destinations": "destination",
            "hotels": "hotel",
            "attractions": "attraction",
            "beaches": "beach",
            "activities": "activity",
            "flights": "flight",
            "trains": "train"
        }

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenizes text while preserving travel constructs like ₹12,000, 4-day, etc.
        """
        # Regex to capture currency (₹12,000 / Rs.15000), hyphenated compounds (4-day, 2-night), and words
        pattern = r'(?:[₹$€£]|Rs\.?)\s*\d+(?:,\d+)*(?:\s*(?:k|thousand|lakh))?|\b\d+-(?:day|night|hr|hour)s?\b|\b\w+\b|[^\w\s]'
        tokens = re.findall(pattern, text)
        return tokens if tokens else text.split()

    def lemmatize_token(self, token: str) -> str:
        """
        Lemmatizes a single token using custom dictionary & WordNetLemmatizer.
        """
        lower = token.lower()
        if lower in self.travel_lemma_lookup:
            return self.travel_lemma_lookup[lower]
        if self.lemmatizer:
            try:
                # Try verb first, then noun
                lemma_v = self.lemmatizer.lemmatize(lower, pos='v')
                if lemma_v != lower:
                    return lemma_v
                return self.lemmatizer.lemmatize(lower, pos='n')
            except Exception:
                pass
        return lower

    def process(self, text: str) -> dict:
        """
        Executes full preprocessing and returns detailed breakdown for visual inspection.
        """
        raw_tokens = self.tokenize(text)
        
        token_analysis = []
        filtered_tokens = []
        lemmatized_tokens = []
        
        for tok in raw_tokens:
            tok_lower = tok.lower()
            is_stop = tok_lower in self.stopwords
            lemma = self.lemmatize_token(tok)
            
            token_analysis.append({
                "token": tok,
                "lemma": lemma,
                "is_stopword": is_stop,
                "is_numeric": bool(re.search(r'\d', tok)),
                "is_currency": bool(re.search(r'[₹$€£]|rs', tok, re.I))
            })
            
            if not is_stop:
                filtered_tokens.append(tok)
                lemmatized_tokens.append(lemma)
                
        cleaned_text = " ".join(lemmatized_tokens)
        
        return {
            "original_query": text,
            "raw_tokens": raw_tokens,
            "tokens_display": " | ".join(raw_tokens),
            "token_analysis": token_analysis,
            "filtered_tokens": filtered_tokens,
            "lemmatized_tokens": lemmatized_tokens,
            "cleaned_text": cleaned_text
        }
