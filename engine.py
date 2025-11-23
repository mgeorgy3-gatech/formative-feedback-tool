from openai import OpenAI
import os, json, datetime as dt
import streamlit as st
from dotenv import load_dotenv
from prompts import (
    build_system_prompt, 
    build_user_prompt)
from utils import (
    load_article,
    load_answers,
    compute_score,
    flatten_answers,
    count_user_attempts,
    save_submission_local,
    save_submission_to_sheets
)

load_dotenv()

def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_feedback(article, correct_answers, user_answers):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(article, correct_answers, user_answers)}
        ]
    )
    return response.choices[0].message.content

def handle_submission(submission_payload):
    user_id = submission_payload["user_id"]
    topic = submission_payload["topic"]
    article = load_article(topic)
    user_answers = submission_payload["answers"]

    correct_answers = load_answers(topic)
    score = compute_score(user_answers, correct_answers)
    flat = flatten_answers(user_answers, correct_answers)

    attempt_number = count_user_attempts(user_id, topic)

    # Block if already attempted twice (no saving, no feedback)
    if attempt_number >= 2:
        return {
            "feedback": None,
            "attempt": attempt_number + 1,
            "score": None,
            "blocked": True
        }

    # Attempt 1 feedback rule
    feedback = None
    if attempt_number == 0 and score < 100:
        # feedback = get_feedback(article, correct_answers, user_answers)
        feedback = "Simulated feedback.."

    # Build stored record
    record = {
        "user_id": user_id,
        "topic": topic,
        "timestamp": dt.datetime.now().isoformat(),
        "attempt": attempt_number + 1,
        "score": score,
        "user_answers": user_answers
    }
    record.update(flat)
    try:
        secrets_obj = getattr(st, "secrets", None)
        use_google_sheets = (
            secrets_obj is not None
            and isinstance(secrets_obj, dict)
            and "GOOGLE_SHEETS_CREDENTIALS" in secrets_obj
            and "GOOGLE_SHEET_ID" in secrets_obj
        )
    except Exception:
        use_google_sheets = False

    write_result = False
    if use_google_sheets:
        save_submission_to_sheets(record)
    else:
        save_submission_local(record)

    if write_result == False:
        raise RuntimeError("Failed to save submission record")
    
    return {
        "feedback": feedback,
        "attempt": attempt_number + 1,
        "score": score,
        "blocked": False
    }