import streamlit as st
import google.generativeai as genai
import json

# Page Config
st.set_page_config(page_title="IELTS Reading Simulator", layout="wide")

st.title("📚 IELTS Reading Simulator")
st.markdown("Generates unique reading passages and questions using Google AI.")

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.markdown("[Get a Key from Google AI Studio](https://aistudio.google.com/app/apikey)")

# --- SESSION STATE (Memory) ---
if 'passage_data' not in st.session_state:
    st.session_state['passage_data'] = None

# --- MAIN LOGIC ---
if api_key:
    # 1. Configure API
    genai.configure(api_key=api_key)

    # 2. SMART MODEL SELECTOR (This fixes the 404/Version errors)
    try:
        available_models = []
        # Ask Google which models are actually available to THIS key
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("❌ No models found. Your API Key might be restricted.")
            st.stop()

        # Logic: Prefer 'flash' (fast), otherwise take 'pro', otherwise take first available
        # This prevents guessing names like 'gemini-1.5-flash' if Google renames them.
        selected_model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        
        st.sidebar.success(f"✅ AI Connected: {selected_model_name}")
        model = genai.GenerativeModel(selected_model_name)

    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        st.stop()

    # 3. GENERATE BUTTON
    if st.button("Generate New Reading Test", type="primary"):
        with st.spinner("AI is writing a new exam for you... (this takes 5-10s)"):
            try:
                # The Prompt
                prompt = """
                Create an IELTS Academic Reading passage (approx 300 words). 
                Topic: Random (Science, History, or Nature).
                Create 3 questions: 
                - 2 Multiple Choice
                - 1 True/False/Not Given.
                
                Output ONLY valid JSON in this format:
                {
                    "title": "Passage Title",
                    "passage": "Full text here...",
                    "questions": [
                        {"id": 1, "text": "Question 1?", "options": ["A", "B", "C"], "answer": "A"},
                        {"id": 2, "text": "Question 2?", "options": ["True", "False", "Not Given"], "answer": "True"}
                    ]
                }
                """
                
                response = model.generate_content(prompt)
                text = response.text
                
                # Clean up JSON (remove ```json wrappers if AI adds them)
                text = text.replace("```json", "").replace("```", "").strip()
                
                # Parse and Save to Memory
                data = json.loads(text)
                st.session_state['passage_data'] = data
                st.rerun() # Refresh to show data

            except Exception as e:
                st.error(f"Generation Failed: {e}")

# --- DISPLAY SECTION ---
data = st.session_state['passage_data']

if data:
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.subheader(f"📖 {data['title']}")
        st.write(data['passage'])
    
    with col2:
        st.subheader("📝 Questions")
        user_answers = {}
        
        with st.form("quiz_form"):
            for q in data['questions']:
                st.write(f"**{q['id']}. {q['text']}**")
                # Create radio buttons for options
                user_answers[q['id']] = st.radio(
                    "Select answer:", 
                    q['options'], 
                    key=f"q_{q['id']}", 
                    label_visibility="collapsed"
                )
                st.divider()
            
            submitted = st.form_submit_button("Check Answers")
            
            if submitted:
                score = 0
                for q in data['questions']:
                    correct = q['answer']
                    user_ans = user_answers[q['id']]
                    if user_ans == correct:
                        score += 1
                        st.success(f"Q{q['id']}: Correct!")
                    else:
                        st.error(f"Q{q['id']}: Incorrect. Answer was {correct}")
                
                st.metric("Final Score", f"{score}/{len(data['questions'])}")

else:
    if not api_key:
        st.info("👈 Please paste your API Key in the sidebar to begin.")
