# utils.py
import json
import os

DATA_DIR = "data"

# ---------------------------------------------
# Load the article text for a topic
# ---------------------------------------------
def load_article(topic):
    path = os.path.join(DATA_DIR, topic, "article.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------
# Load the multiple-choice questions
# ---------------------------------------------
def load_questions(topic):
    path = os.path.join(DATA_DIR, topic, "questions.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------
# Load correct answers (same format as user answers)
# ---------------------------------------------
def load_answers(topic):
    path = os.path.join(DATA_DIR, topic, "answers.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------
# Compute score as percentage correct (0–1)
# ---------------------------------------------
def compute_score(user_answers, correct_answers):
    total = len(correct_answers)
    correct = 0
    for q_idx, correct_ans in correct_answers.items():
        user_ans = user_answers.get(int(q_idx), [])
        if set(user_ans) == set(correct_ans):
            correct += 1
    return correct / total


# ---------------------------------------------
# Flatten nested answers so pandas can analyze easily
# ---------------------------------------------
def flatten_answers(user_answers, correct_answers):
    flat = {}
    for idx, ans in user_answers.items():
        flat[f"q{idx}_answer"] = ans
    for idx_str, ans in correct_answers.items():
        flat[f"q{idx_str}_correct"] = ans
    return flat

# utils.py
import json
import os

# ... existing utils for loading questions, answers, etc.


# Count attempts for this user in submissions.jsonl
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


# def build_feedback_prompt(user_answers, correct_answers, article):
#     return f"""
#         You are an academic formative feedback assistant.
#         Here is the article the student was asked to read:

#         ARTICLE:
#         {article}

#         ---

#         Here are the correct answers for the quiz:
#         {json.dumps(correct_answers, indent=2)}

#         ---

#         Here are the student's answers:
#         {json.dumps(user_answers, indent=2)}

#         ---

#         TASK:
#         Provide concise, constructive formative feedback.

#         Your feedback should:
#         - explain what they understood correctly
#         - explain misconceptions (if any)
#         - give guidance on how to improve understanding
#         - be friendly and educational
#         - reference the article content when helpful

#         Return only the feedback text.
#         """

