import streamlit as st
import google.generativeai as genai
import json
import re

# --- Page Config ---
st.set_page_config(page_title="IELTS Reading Simulator", layout="wide")

# --- Session State Initialization ---
# We use this to keep the test data persistent across reruns
if "test_data" not in st.session_state:
    st.session_state.test_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --- Sidebar: API Key ---
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Get your key from [Google AI Studio](https://aistudio.google.com/)")

# --- Helper Functions ---
def generate_test(api_key):
    try:
        genai.configure(api_key=api_key)
        # --- SMART MODEL SELECTOR ---
    # This asks Google what models are actually available to this specific API Key
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("No AI models found. Google is blocking this API Key/Region.")
            st.stop()

        # Logic: Try to find a 'flash' model first (fast), otherwise take the first available
        selected_model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        
        # Display which model is being used (Good for debugging/research transparency)
        st.sidebar.success(f"✅ Connected to: {selected_model_name}")
        
        model = genai.GenerativeModel(selected_model_name)

    except Exception as e:
        st.error(f"Error connecting to Google: {e}")
        st.stop()
        
        prompt = """
        Generate an IELTS Academic Reading test in STRICT JSON format.
        The JSON must contain:
        1. "title": A professional academic title.
        2. "passage": A 300-word academic text.
        3. "questions": A list of 3 questions.
           - Mix Multiple Choice and True/False.
           - Each question must have: "id" (int), "question_text" (string), "type" (MCQ/TF), "options" (list of strings or null for TF), "correct_answer" (string).
        
        Return ONLY the JSON object. No markdown, no preamble.
        """
        
        response = model.generate_content(prompt)
        # Remove potential markdown code blocks (```json ... ```)
        clean_json = re.sub(r'```json|```', '', response.text).strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"Error generating test: {e}")
        return None

# --- Main UI ---
st.title("📖 IELTS Reading Simulator")

if st.button("Generate New Reading Test"):
    if not api_key:
        st.warning("Please provide an API Key in the sidebar first!")
    else:
        with st.spinner("Generating academic passage..."):
            data = generate_test(api_key)
            if data:
                st.session_state.test_data = data
                st.session_state.user_answers = {} # Reset answers
                st.session_state.submitted = False
                st.rerun()

# --- Display Content ---
if st.session_state.test_data:
    data = st.session_state.test_data
    
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.subheader(data['title'])
        st.markdown(data['passage'])
    
    with col2:
        st.subheader("Questions")
        for q in data['questions']:
            q_id = str(q['id'])
            
            # Display Question
            if q['type'] == "MCQ":
                st.session_state.user_answers[q_id] = st.radio(
                    f"**Question {q_id}:** {q['question_text']}",
                    options=q['options'],
                    key=f"q_{q_id}",
                    index=None if q_id not in st.session_state.user_answers else None # Simplification
                )
            else: # True/False
                st.session_state.user_answers[q_id] = st.radio(
                    f"**Question {q_id}:** {q['question_text']}",
                    options=["True", "False", "Not Given"],
                    key=f"q_{q_id}",
                    index=None
                )
        
        # --- Grading Logic ---
        if st.button("Check Answers"):
            st.session_state.submitted = True
            
        if st.session_state.submitted:
            score = 0
            st.divider()
            for q in data['questions']:
                q_id = str(q['id'])
                user_ans = st.session_state.user_answers.get(q_id)
                correct_ans = q['correct_answer']
                
                if user_ans == correct_ans:
                    score += 1
                    st.success(f"Q{q_id}: Correct! ({correct_ans})")
                else:
                    st.error(f"Q{q_id}: Incorrect. You said '{user_ans}'. Correct: '{correct_ans}'")
            
            st.metric("Final Score", f"{score}/{len(data['questions'])}")
else:
    st.write("Click the button to generate your first mock exam.")
