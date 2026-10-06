"""
Flask Application for AI Travel Assistant Chatbot Using Natural Language Processing.
Aditya University - Department of Computer Science & Engineering
Team Members: N.Bhavya Sri, T.Lavanya, S.Srihasini
"""

import sys
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Ensure proper path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from nlp_engine import TravelNLPPipeline
from recommender import TravelKnowledgeBase, TravelContextManager, ItineraryGenerator
from recommender.dialogue_manager import TravelDialogueManager

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize core services
nlp_pipeline = TravelNLPPipeline()
travel_kb = TravelKnowledgeBase()
context_manager = TravelContextManager()
itinerary_generator = ItineraryGenerator(travel_kb)
dialogue_manager = TravelDialogueManager(travel_kb, context_manager, itinerary_generator)

# Project Information
PROJECT_INFO = {
    "title": "AI Travel Assistant Chatbot Using Natural Language Processing",
    "subtitle": "Personalized travel planning • destination recommendations • itinerary assistance",
    "project_type": "B.Tech CSE • Minor Project Review",
    "institution": "Aditya University",
    "department": "Department of Computer Science & Engineering",
    "team_members": [
        {"name": "N.Bhavya Sri", "role": "Lead NLP & Pipeline Developer"},
        {"name": "T.Lavanya", "role": "Intent & Entity Model Developer"},
        {"name": "S.Srihasini", "role": "Knowledge Base & UI Developer"}
    ],
    "architecture_steps": [
        {"step": "01", "name": "User Query", "desc": "Natural language travel prompt input"},
        {"step": "02", "name": "NLP Preprocessing", "desc": "Tokenization, Lemmatization, Stopwords"},
        {"step": "03", "name": "Intent Classification", "desc": "TF-IDF + ML Classifier (Confidence %)"},
        {"step": "04", "name": "Entity + Preference", "desc": "Destination, Duration, Budget, Activities"},
        {"step": "05", "name": "Recommendation Engine", "desc": "Travel Knowledge Base & Category Matching"},
        {"step": "06", "name": "Itinerary Generation", "desc": "Day-wise schedules & Budget allocation"},
        {"step": "07", "name": "Contextual Response", "desc": "Interactive Chat & Visual Cards"}
    ]
}

@app.route('/')
def home():
    """Renders the main web application."""
    destinations = travel_kb.get_all_destinations()
    return render_template('index.html', project=PROJECT_INFO, destinations=destinations)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handles chat messages with full NLP analysis and contextual response."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default_user')
    api_key = data.get('api_key')
    provider = data.get('provider', 'gemini')
    conversation_history = data.get('history', [])

    if not message:
        return jsonify({"error": "Empty message provided"}), 400

    # Step 1: Execute NLP pipeline
    nlp_result = nlp_pipeline.process_query(message)

    # Step 2: Generate Contextual Dialogue Response (with LLM API support)
    response_data = dialogue_manager.generate_response(
        session_id=session_id,
        query=message,
        nlp_result=nlp_result,
        api_key=api_key,
        provider=provider,
        conversation_history=conversation_history
    )

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "reply": response_data["reply_text"],
        "place_showcase": response_data.get("place_showcase"),
        "itinerary": response_data["itinerary"],
        "recommended_destinations": response_data["recommended_destinations"],
        "quick_suggestions": response_data["quick_suggestions"],
        "profile": response_data["profile"],
        "nlp_analysis": response_data["nlp_analysis"]
    })

@app.route('/api/analyze_nlp', methods=['POST'])
def api_analyze_nlp():
    """Endpoint for direct NLP inspection of any arbitrary query."""
    data = request.get_json(silent=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query required"}), 400

    result = nlp_pipeline.process_query(query)
    return jsonify({
        "status": "success",
        "analysis": result
    })

@app.route('/api/reset_context', methods=['POST'])
def api_reset_context():
    """Resets conversational memory and travel profile for the session."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id', 'default_user')
    res = context_manager.reset_session(session_id)
    return jsonify(res)

@app.route('/api/destinations', methods=['GET'])
def api_get_destinations():
    """Returns knowledge base destination items."""
    return jsonify({
        "status": "success",
        "destinations": travel_kb.get_all_destinations()
    })

@app.route('/api/destination/<dest_id>', methods=['GET'])
def api_get_single_destination(dest_id):
    """Returns details for a single destination."""
    dest = travel_kb.get_destination(dest_id)
    if not dest:
        return jsonify({"error": "Destination not found"}), 404
    return jsonify({"status": "success", "destination": dest})

@app.route('/api/project_info', methods=['GET'])
def api_get_project_info():
    """Returns metadata for the Aditya University Minor Project review."""
    return jsonify(PROJECT_INFO)

if __name__ == '__main__':
    print("=================================================================")
    print("AI Travel Assistant Chatbot Using Natural Language Processing")
    print("Aditya University - Dept. of Computer Science & Engineering")
    print("Team: N.Bhavya Sri, T.Lavanya, S.Srihasini")
    print("Starting Flask web server on http://127.0.0.1:5000")
    print("=================================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)
