from pathlib import Path
import glob
import json
from typing import Dict, List, Any

result_path = Path(__file__).parent.parent.parent / "result"
all_results = glob.glob(str(result_path) + "/all_*.json")
leaderboards = []


def count_score_by_topic(dataset: List[Dict[str, Any]]):
    score_by_topic = {}
    total_score_by_topic = {}
    score = 0
    for dataset_row in dataset:
        for topic in dataset_row["topics"]:
            if topic not in score_by_topic:
                score_by_topic[topic] = 0
                total_score_by_topic[topic] = 0
            score_by_topic[topic] += dataset_row["score"]
            total_score_by_topic[topic] += 1
        score += dataset_row["score"]
    score_fraction = {
        k: f"{v}/{total_score_by_topic[k]}" for k, v in score_by_topic.items()
    }
    score_float = {
        k: round(100 * float(v) / float(total_score_by_topic[k]), 4)
        for k, v in score_by_topic.items()
    }
    score_float["Overall"] = round(100 * float(score) / float(len(dataset)), 4)
    score_fraction["Overall"] = f"{100 * score}/{len(dataset)}"
    return score_fraction, score_float


bad_item = 0
invalid_item = 0
with open(result_path / "all_microsoft_Orca-2-7b.json", "r") as f:
    data = json.load(f)
    for item in data["detail"]:
        if not item["flags"].get("gpt-4_answer"):
            bad_item += 1
            continue
        if item["flags"].get("gpt-4_answer") == "Invalid":
            invalid_item += 1
            continue
        item["llm_answer"] = item["flags"]["gpt-4_answer"]
        item["llm_output"] = item["flags"]["gpt-4_answer"]
        item["score"] = item["llm_answer"] == item["answer"]
    data["score_fraction"], data["score_float"] = count_score_by_topic(data["detail"])
    print("bad item", bad_item)
    print("invalid item", invalid_item)

with open(result_path / "all_OpenAI_GPT-4-turbo.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
