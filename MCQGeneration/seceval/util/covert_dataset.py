from pathlib import Path
import json
import random

with open(Path(__file__).parent.parent.parent / "dataset" / "all.json") as f:
    questions = json.load(f)
new_questions = []
for question in questions:
    if question["flags"].get("invalid") != None:
        continue
    if question["flags"].get("calibrated_answer"):
        continue
    question.pop("flags")
    question.pop("text_basis")
    question.pop("redundant")
    # question["keyword"] = question.pop("Keyword")
    new_questions.append(question)


random.seed(42)
random.shuffle(new_questions)
print(len(new_questions))
with open(Path(__file__).parent.parent.parent / "dataset" / "problems.json", "w") as f:
    json.dump(new_questions, f, ensure_ascii=False, indent=4)
