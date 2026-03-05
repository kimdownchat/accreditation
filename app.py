import streamlit as st
import sqlite3
import pandas as pd
import random
import json
from datetime import datetime

st.set_page_config(
    page_title="MedExam - Medical Exam Practice",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "selftest.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def load_specialties():
    conn = get_connection()
    df = pd.read_sql("SELECT code, name FROM specialty ORDER BY name", conn)
    conn.close()
    return df

def load_questions_by_specialty(specialty_code, limit=50):
    conn = get_connection()
    query = """
        SELECT id, html, answers, speciality_id, discipline, done_count
        FROM question 
        WHERE speciality_id = ?
        ORDER BY RANDOM()
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(specialty_code, limit))
    conn.close()
    return df

def load_multi_by_specialty(specialty_code, limit=10):
    conn = get_connection()
    query = """
        SELECT id, theme_param, case_content_json, done_count
        FROM multi 
        WHERE speciality = ?
        ORDER BY RANDOM()
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(specialty_code, limit))
    conn.close()
    return df

def init_session_state():
    if 'exam_active' not in st.session_state:
        st.session_state.exam_active = False
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False
    if 'selected_specialty' not in st.session_state:
        st.session_state.selected_specialty = None
    if 'exam_mode' not in st.session_state:
        st.session_state.exam_mode = "mcq"

def render_html(html_content):
    if html_content:
        return f"<div class='question-text'>{html_content}</div>"
    return ""

def parse_answers(answers_json):
    try:
        return json.loads(answers_json) if isinstance(answers_json, str) else answers_json
    except:
        return []

def check_answer(answer_id, selected_id):
    return answer_id == selected_id

def calculate_score(questions, user_answers):
    score = 0
    for q in questions:
        q_id = q['id']
        if q_id in user_answers:
            answers = parse_answers(q['answers'])
            correct = next((a for a in answers if a.get('is_correct')), None)
            if correct and correct.get('id') == user_answers[q_id]:
                score += 1
    return score

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main-content {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 1rem;
    }
    
    .question-card {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    
    .question-text {
        font-size: 1.1rem;
        line-height: 1.8;
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    .answer-option {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .answer-option:hover {
        border-color: #667eea;
        transform: translateX(5px);
    }
    
    .answer-option.selected {
        border-color: #667eea;
        background: #f0f4ff;
    }
    
    .answer-option.correct {
        border-color: #48bb78;
        background: #f0fff4;
    }
    
    .answer-option.incorrect {
        border-color: #f56565;
        background: #fff5f5;
    }
    
    .progress-bar {
        background: #e2e8f0;
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
    }
    
    .stat-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .specialty-select {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
    }
    
    h1, h2, h3 {
        color: #2d3748;
    }
    
    .stSelectbox, .stNumberInput, .stSlider {
        background: white;
        border-radius: 10px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

def home_page():
    st.markdown('<div class="specialty-select">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🏥 MedExam</h1>
            <p style="font-size: 1.2rem; color: #718096;">Medical Exam Practice Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        specialties = load_specialties()
        specialty_options = {row['name']: row['code'] for _, row in specialties.iterrows()}
        
        selected_name = st.selectbox("Select Specialty", list(specialty_options.keys()), index=0)
        st.session_state.selected_specialty = specialty_options[selected_name]
        
        exam_mode = st.radio("Exam Mode", ["Multiple Choice (MCQ)", "Case Studies"], horizontal=True)
        st.session_state.exam_mode = "mcq" if exam_mode == "Multiple Choice (MCQ)" else "case"
        
        num_questions = st.slider("Number of Questions", 10, 100, 25, 5)
        
        if st.button("Start Exam", type="primary", use_container_width=True):
            if st.session_state.exam_mode == "mcq":
                questions = load_questions_by_specialty(st.session_state.selected_specialty, num_questions)
            else:
                questions = load_multi_by_specialty(st.session_state.selected_specialty, num_questions)
            
            if len(questions) > 0:
                st.session_state.questions = questions.to_dict('records')
                st.session_state.current_index = 0
                st.session_state.answers = {}
                st.session_state.exam_active = True
                st.session_state.show_result = False
                st.rerun()
            else:
                st.error("No questions available for this specialty!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def exam_page():
    questions = st.session_state.questions
    current_index = st.session_state.current_index
    total = len(questions)
    
    with st.sidebar:
        st.markdown("### 📊 Exam Progress")
        progress = (current_index + 1) / total
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress * 100}%"></div>
        </div>
        """, unsafe_allow_html=True)
        st.write(f"Question {current_index + 1} of {total}")
        
        st.markdown("### 📈 Stats")
        answered = len(st.session_state.answers)
        st.metric("Answered", answered)
        st.metric("Remaining", total - answered)
        
        if st.button("End Exam & Show Results"):
            st.session_state.show_result = True
            st.rerun()
        
        if st.button("Exit Exam"):
            st.session_state.exam_active = False
            st.session_state.questions = []
            st.rerun()
    
    if current_index >= total:
        st.session_state.show_result = True
        st.rerun()
    
    question = questions[current_index]
    
    st.markdown(f"""
    <div class="question-card">
        <div class="question-text">
            {render_html(question.get('html', ''))}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    answers = parse_answers(question.get('answers') or question.get('case_content_json'))
    
    if not isinstance(answers, list):
        try:
            answers = json.loads(str(answers)) if answers else []
        except:
            answers = []
    
    st.markdown("### Select your answer:")
    
    current_answer = st.session_state.answers.get(question['id'])
    
    for i, answer in enumerate(answers):
        answer_id = answer.get('id', chr(65 + i))
        answer_html = answer.get('html', str(answer))
        
        col = st.columns([1])
        with col:
            if st.button(
                f"{answer_id}. {answer_html[:100]}..." if len(str(answer_html)) > 100 else f"{answer_id}. {answer_html}",
                key=f"answer_{question['id']}_{i}",
                use_container_width=True
            ):
                st.session_state.answers[question['id']] = answer_id
                st.rerun()
        
        if current_answer == answer_id:
            st.markdown(f":blue[✓ Selected: {answer_id}]")
    
    col1, col2 = st.columns(2)
    with col1:
        if current_index > 0 and st.button("← Previous", use_container_width=True):
            st.session_state.current_index -= 1
            st.rerun()
    
    with col2:
        if st.button("Next →", type="primary", use_container_width=True):
            if question['id'] in st.session_state.answers:
                st.session_state.current_index += 1
                st.rerun()
            else:
                st.warning("Please select an answer before continuing!")

def result_page():
    questions = st.session_state.questions
    total = len(questions)
    score = calculate_score(questions, st.session_state.answers)
    percentage = (score / total * 100) if total > 0 else 0
    
    st.markdown("""
    <div class="score-card">
        <h2>🎉 Exam Complete!</h2>
        <h1 style="font-size: 4rem; margin: 1rem 0;">{:.0f}%</h1>
        <p style="font-size: 1.5rem;">{} out of {} correct</p>
    </div>
    """.format(percentage, score, total), unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Questions", total)
    with col2:
        st.metric("Correct", score, delta=score)
    with col3:
        st.metric("Incorrect", total - score, delta=-(total - score))
    with col4:
        st.metric("Score", f"{percentage:.1f}%")
    
    st.markdown("### 📝 Review Answers")
    
    for i, q in enumerate(questions):
        with st.expander(f"Question {i + 1}"):
            st.markdown(f"**Question:** {q.get('html', '')[:200]}...")
            
            answers = parse_answers(q.get('answers') or q.get('case_content_json'))
            user_answer = st.session_state.answers.get(q['id'])
            correct = next((a for a in answers if a.get('is_correct')), None)
            
            for answer in answers:
                answer_id = answer.get('id', '')
                answer_html = answer.get('html', '')
                
                if answer.get('is_correct'):
                    st.markdown(f"✅ **Correct:** {answer_html}")
                elif answer_id == user_answer:
                    st.markdown(f"❌ **Your Answer:** {answer_html}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Again", type="primary", use_container_width=True):
            st.session_state.exam_active = True
            st.session_state.show_result = False
            st.session_state.current_index = 0
            st.session_state.answers = {}
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.exam_active = False
            st.session_state.questions = []
            st.session_state.show_result = False
            st.rerun()

def main():
    init_session_state()
    
    if st.session_state.show_result:
        result_page()
    elif st.session_state.exam_active:
        exam_page()
    else:
        home_page()

if __name__ == "__main__":
    main()
