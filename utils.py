import json
import os
import gspread
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_article(topic):
    path = os.path.join(DATA_DIR, topic, "article.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_questions(topic):
    path = os.path.join(DATA_DIR, topic, "questions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_answers(topic):
    path = os.path.join(DATA_DIR, topic, "answers.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_score(user_answers, correct_answers):
    normalized_correct = {int(k): (v if isinstance(v, list) else [v])
                          for k, v in correct_answers.items()}
    normalized_user = {int(k): v for k, v in user_answers.items()}
    total = len(normalized_correct)
    correct = 0
    for q_idx, correct_ans_list in normalized_correct.items():
        user_ans_list = normalized_user.get(q_idx, [])
        if set(user_ans_list) == set(correct_ans_list):
            correct += 1
    return (100 * correct / total) if total > 0 else 0


def flatten_answers(user_answers, correct_answers):
    flat = {}
    normalized_correct = {int(k): (v if isinstance(v, list) else [v])
                          for k, v in correct_answers.items()}
    for idx, ans in user_answers.items():
        flat[f"q{int(idx)}_answer"] = ans
    for idx, ans in normalized_correct.items():
        flat[f"q{int(idx)}_correct"] = ans
    return flat

def count_user_attempts(user_id, topic):
    path = f"data/{topic}/submissions.jsonl"
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("user_id") == user_id:
                    count += 1
            except:
                pass
    return count

def save_submission_local(record, topic):
    os.makedirs(f"data/{topic}", exist_ok=True)
    with open(f"data/{topic}/submissions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
def save_submission_to_sheets(record):
    creds = json.loads(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    worksheet = sh.sheet1 
    row = [
        record["user_id"],
        record["attempt"],
        record["topic"],
        record["score"],
        record["timestamp"],
        json.dumps(record["user_answers"])
    ]

    worksheet.append_row(row)