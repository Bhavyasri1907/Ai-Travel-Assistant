# AI Travel Assistant Chatbot Using Natural Language Processing (NLP)

**Department of Computer Science & Engineering • Aditya University**  
*B.Tech CSE • Minor Project Review*

### Team Members:
- **N.Bhavya Sri**
- **T.Lavanya**
- **S.Srihasini**

---

## 📌 Project Overview

The **AI Travel Assistant Chatbot** is an intelligent, conversational web application that simplifies travel planning using **Natural Language Processing (NLP)**. Instead of manually searching multiple websites, comparing flights, and designing itineraries, users can simply state their travel desires in plain English (e.g., *"Plan a 4-day trip to Bengaluru under ₹12,000"*).

The assistant automatically extracts destination, duration, budget constraints, and personal interests, retains multi-turn conversational context, and generates practical day-by-day itineraries with complete budget allocation breakdowns.

---

## 🏗️ System Architecture & NLP Workflow

The system implements the 7-step pipeline specified in the project review presentation:

```
[01. User Query]
       │
       ▼
[02. NLP Preprocessing] (Tokenization, Lemmatization, Stopword Filtering)
       │
       ▼
[03. Intent Classification] (TF-IDF Vectorization + Machine Learning Classifier)
       │
       ▼
[04. Entity & Preference Extraction] (Destination, Duration, Budget, Activities, Food, Style)
       │
       ▼
[05. Context Manager & Travel KB] (State Memory across turns + Curated Destination Database)
       │
       ▼
[06. Itinerary Generator] (Day-Wise Schedules: Morning/Afternoon/Evening & Cost Breakdown)
       │
       ▼
[07. Interactive Response] (Chat Bubble, Itinerary Card, Confetti, Speech Readout, Live NLP Inspector)
```

### Traditional vs AI-Powered Planning:
- **Traditional:** Search ➔ Compare ➔ Plan *(Manual, fragmented, time-consuming)*
- **AI Assistant:** Ask ➔ Understand ➔ Recommend ➔ Itinerary *(Conversational, contextual, instant)*

---

## 🔬 NLP Module Details

### 1. Tokenization & Compound Handling
Captures currency constructs (e.g. `₹12,000`, `Rs. 15,000`), hyphenated duration expressions (`4-day`, `2-night`), and individual lexical words while stripping irrelevant punctuation.

### 2. Lemmatization (NLTK WordNet & Custom Rules)
Normalizes inflections to dictionary root lemmas:
- `planning` ➔ `plan`
- `visiting` ➔ `visit`
- `traveling` ➔ `travel`
- `recommendations` ➔ `recommend`

### 3. Intent Classification (Machine Learning)
A scikit-learn pipeline utilizing **TF-IDF (unigrams + bigrams)** paired with a **calibrated Logistic Regression** classifier that outputs probability distribution across travel intents:
- `TRIP_PLANNING` (Confidence ~96%)
- `DESTINATION_RECOMMENDATION`
- `HOTEL_ATTRACTION_SEARCH`
- `TRANSPORT_WEATHER_BUDGET`
- `TRAVEL_TIPS_FAQ`
- `GREETING`

### 4. Entity Extraction (Regex & Gazetteers)
- **Destination:** Bengaluru, Hyderabad, Goa, Jaipur, Manali, Kerala, Ooty, Varanasi, etc.
- **Duration:** Normalized into integer days (`4-day` ➔ `4`, `weekend` ➔ `2`)
- **Budget:** Extracted and converted to numerical INR values (`₹12,000` ➔ `12000`, `15k` ➔ `15000`)
- **Interests / Activities:** Adventure, history, beach, nightlife, spiritual, nature, relaxation
- **Food Preferences:** Biryani, local cuisine, street food, seafood, vegetarian

### 5. Multi-Turn Context Management
Maintains traveler state across conversation turns:
- **Turn 1:** *"Plan a trip to Goa for 3 days."* ➔ Sets destination=Goa, duration=3 days.
- **Turn 2:** *"My budget is ₹15,000."* ➔ Retains Goa + 3 days, updates budget to ₹15,000.
- **Turn 3:** *"I like adventure activities."* ➔ Retains all previous entities, updates activities to include water sports and scuba diving!

---

## 🚀 How to Run the Website

### Prerequisites:
- Python 3.10+ installed
- Web browser (Chrome, Edge, Firefox)

### Option 1: Quick Windows Launcher
Double-click `run.bat` in the project directory.

### Option 2: Command Line
1. Open terminal / PowerShell in `ai_travel_assistant`:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Flask server:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🖥️ Website Features

1. **Conversational Chatbot Interface**:
   - Natural language input with preset PPT demo buttons
   - Interactive Itinerary cards with Day 1 / Day 2 / Day 3 breakdowns
   - Budget allocation bar chart (Stay 40%, Food 25%, Sightseeing 20%, Commute 15%)
   - Print / Save Itinerary button
   - Web Speech API microphone input & Speech Synthesis voice readout
2. **Live NLP Engine Inspector (Sidebar)**:
   - Real-time display of tokens, lemmas, intent confidence score, extracted entities, and active session memory profile.
3. **Interactive NLP Sandbox**:
   - Dedicated tab to test any custom query and inspect tokenization tables, lemmatization POS, and intent probability charts.
4. **Curated Travel Knowledge Base**:
   - Filterable catalog of top Indian destinations with attractions, best seasons, and daily budgets.
5. **Aditya University Presentation Review Tab**:
   - Digital presentation deck reflecting the 11 slides from the B.Tech CSE Minor Project review.

---

## 🔮 Future Scope
- Multilingual NLP support (Hindi, Telugu, Tamil, etc.)
- Real-time Weather, Google Maps, and Flight/Train API integration
- Deep Learning / Transformer (LLM) fine-tuning for complex personalized recommendations
