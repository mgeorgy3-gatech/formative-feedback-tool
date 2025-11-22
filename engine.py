# engine.py
from openai import OpenAI
import os, json, datetime as dt
from prompts import (
    build_system_prompt, 
    build_user_prompt)
from utils import (
    load_article,
    load_answers,
    compute_score,
    flatten_answers,
    count_user_attempts
)

# LLM
def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_feedback(article, correct_answers, user_answers):
    client = get_client()
    #prompt = build_prompt(article, correct_answers, user_answers)

    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(article, correct_answers, user_answers)}
        ]
    )
    return response.choices[0].message.content


# Save one line in a topic submissions.jsonl
def save_submission(record, topic):
    os.makedirs(f"data/{topic}", exist_ok=True)
    with open(f"data/{topic}/submissions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def handle_submission(submission_payload):
    """
    submission_payload:
    {
        user_id,
        topic,
        answers,
        num_questions
    }
    """

    user_id = submission_payload["user_id"]
    topic = submission_payload["topic"]
    user_answers = submission_payload["answers"]

    correct_answers = load_answers(topic)
    article = load_article(topic)
    score = compute_score(user_answers, correct_answers)
    flat = flatten_answers(user_answers, correct_answers)

    # 🔥 NEW: detect attempt count
    attempt_number = count_user_attempts(user_id, topic)

    # Attempt 1 → formative → send to LLM
    feedback = None
    if attempt_number == 0 and score < 1:
        feedback = get_feedback(article, correct_answers, user_answers)

    # Attempt 2 → NO feedback, just save
    # Attempt >2 → allowed but no feedback (simple)

    record = {
        "user_id": user_id,
        "topic": topic,
        "timestamp": dt.datetime.now().isoformat(),
        "attempt": attempt_number + 1,
        "score": score,
        "user_answers": user_answers
        #"feedback": feedback
    }
    record.update(flat)

    save_submission(record, topic)

    return {
    "feedback": feedback,
    "attempt": attempt_number + 1,
    "score": score
    }
