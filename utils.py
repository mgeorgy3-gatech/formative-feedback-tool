#utils.py
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
    # --- Detect Google Sheets availability safely ---
    try:
        #secrets_obj = getattr(st, "secrets", None)
        use_google_sheets = (
            hasattr(st, "secrets")
            and "GOOGLE_SHEETS_CREDENTIALS" in st.secrets
            and "GOOGLE_SHEET_ID" in st.secrets
        )
    except Exception:
        use_google_sheets = False

    # --- Google Sheets attempt counting ---
    if use_google_sheets:
        try:
            creds = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
            worksheet = sh.sheet1
            rows = worksheet.get_all_records()

            return sum(
                1 for row in rows
                if str(row.get("User ID", "")).strip() == str(user_id).strip()
                and str(row.get("Topic", "")).strip() == str(topic).strip()
            )
        except Exception as e:
            print("Sheets attempt counting failed, falling back to local:", e)
            
    # --- Local fallback (per user per topic) ---
    path = f"submissions/submissions.jsonl"
    if not os.path.exists(path):
        return 0

    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("user_id") == user_id and rec.get("topic") == topic:
                    count += 1
            except:
                pass

    return count

def save_submission_local(record):
    os.makedirs(f"submissions", exist_ok=True)
    with open(f"submissions/submissions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return True
        
def save_submission_to_sheets(record):
    if not hasattr(st, "secrets"):
        return False
    if "GOOGLE_SHEETS_CREDENTIALS" not in st.secrets:
        return False
    if "GOOGLE_SHEET_ID" not in st.secrets:
        return False

    creds = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    worksheet = sh.sheet1

    headers = ["User ID", "Attempt", "Topic", "Score", "Timestamp", "User Answers"]

    existing_headers = worksheet.row_values(1)
    if existing_headers != headers:
        worksheet.insert_row(headers, 1)

    row = [
        record["user_id"],
        record["attempt"],
        record["topic"],
        record["score"],
        record["timestamp"],
        json.dumps(record["user_answers"])
    ]

    worksheet.append_row(row)
    return True
