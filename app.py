import streamlit as st
from utils import load_article, load_questions
from engine import handle_submission

st.set_page_config(page_title="🧠 Reading Comprehension Quiz", layout="centered")

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "feedback" not in st.session_state:
    st.session_state.feedback = None

if "attempt" not in st.session_state:
    st.session_state.attempt = None

topic = "ai"

# ---------------------------------------------------------
# Phone number page
# ---------------------------------------------------------
if not st.session_state.user_id and not st.session_state.quiz_started:
    st.title("📱 Enter Your Phone Number")

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("### +20")
    with col2:
        number_part = st.text_input("Phone number (without +20)", max_chars=10)

    if st.button("Start Quiz"):
        if not number_part.isdigit() or len(number_part) != 10:
            st.error("Please enter exactly 10 digits.")
            st.stop()

        st.session_state.user_id = "+20" + number_part
        st.session_state.quiz_started = True
        st.rerun()

    st.stop()

# ---------------------------------------------------------
# Thank you / results page
if st.session_state.submitted:
    # Blocked (already took 2 attempts)
    if st.session_state.attempt >= 3:
        st.title("Oops!")
        st.markdown("You have already taken two attempts for this topic. Maybe try a different topic?")
        st.stop()

    st.title("🎉 Thank You!")

    # Always show score when available
    if st.session_state.score is not None:
        st.subheader("📊 Your Score")
        st.markdown(f"**{st.session_state.score}%**")

    # Attempt 1 — feedback shown only if not perfect
    if st.session_state.attempt == 1:
        if st.session_state.feedback:
            st.subheader("📘 Feedback")
            st.write(st.session_state.feedback)
        else:
            st.markdown("✅ Perfect score — no feedback needed!")

    # Attempt 2 — no feedback
    elif st.session_state.attempt == 2:
        st.markdown("✅ Your second attempt has been submitted.")
        st.markdown("There is no feedback for the second attempt.")

    st.stop()

# ---------------------------------------------------------
# Quiz page
# ---------------------------------------------------------
st.title("🧠 Reading Comprehension Quiz")
st.markdown(f"**User:** {st.session_state.user_id}")

article = load_article(topic)
st.markdown("### Article")
st.write(article)

st.markdown("---")
questions = load_questions(topic)
user_answers = {}

for i, q in enumerate(questions):
    st.write(f"**Q{i+1}. {q['question']}**")
    selected = []
    for opt in q["options"]:
        if st.checkbox(opt, key=f"q{i}_{opt}"):
            selected.append(opt)
    user_answers[i] = selected
    st.markdown("---")

if st.button("Submit Answers"):
    payload = {
        "user_id": st.session_state.user_id,
        "topic": topic,
        "answers": user_answers,
        "num_questions": len(questions),
    }

    with st.spinner("Processing your submission..."):
        result = handle_submission(payload)

    if result.get("blocked"):
        st.session_state.submitted = True
        st.session_state.attempt = result.get("attempt")
        st.session_state.feedback = None
        st.session_state.score = None
    else:
        st.session_state.feedback = result.get("feedback")
        st.session_state.attempt = result.get("attempt")
        st.session_state.score = result.get("score")
        st.session_state.submitted = True

    st.rerun()
