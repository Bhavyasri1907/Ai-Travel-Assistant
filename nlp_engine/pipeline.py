"""
Unified NLP Pipeline Module for AI Travel Assistant.
Coordinates preprocessing, intent classification, and entity extraction.
"""

from .preprocessor import TravelNLPPreprocessor
from .intent_classifier import TravelIntentClassifier
from .entity_extractor import TravelEntityExtractor

class TravelNLPPipeline:
    def __init__(self):
        self.preprocessor = TravelNLPPreprocessor()
        self.intent_classifier = TravelIntentClassifier()
        self.entity_extractor = TravelEntityExtractor()

    def process_query(self, query: str) -> dict:
        """
        Executes end-to-end NLP pipeline:
        1. Preprocessing (Tokenization, Lemmatization, Stopword filtering)
        2. Intent Classification (ML TF-IDF + Logistic Regression)
        3. Entity & Preference Extraction (Destination, Duration, Budget, Activities, Food)
        """
        # Step 1: Preprocessing
        preprocessed = self.preprocessor.process(query)
        
        # Step 2: Intent Classification
        intent_res = self.intent_classifier.predict(query)
        
        # Step 3: Entity Extraction
        entities = self.entity_extractor.extract_entities(query)

        # Highlighted query HTML construction for visual presentation
        annotated_query = self._build_annotated_html(query, entities.get("entity_spans", []))

        return {
            "query": query,
            "preprocessing": preprocessed,
            "intent": intent_res,
            "entities": entities,
            "annotated_query_html": annotated_query
        }

    def _build_annotated_html(self, query: str, spans: list[dict]) -> str:
        """Creates an HTML snippet with color-coded chips around recognized entities."""
        if not spans:
            return query
        
        # Sort spans in reverse order to replace without disturbing indices
        sorted_spans = sorted(spans, key=lambda s: s["start"], reverse=True)
        res = query
        color_map = {
            "Destination": "#3b82f6",  # Blue
            "Duration": "#10b981",     # Emerald
            "Budget": "#f59e0b",       # Amber
            "Activities": "#8b5cf6"    # Purple
        }
        
        for s in sorted_spans:
            start, end = s["start"], s["end"]
            entity_type = s["entity"]
            color = color_map.get(entity_type, "#6366f1")
            val = query[start:end]
            badge_html = f'<span class="entity-badge" style="background-color: {color}22; border: 1px solid {color}; color: {color}; padding: 2px 6px; border-radius: 4px; font-weight: 600;" title="{entity_type}">{val} <small style="font-size:0.7em; opacity:0.8;">[{entity_type}]</small></span>'
            res = res[:start] + badge_html + res[end:]
        return res
