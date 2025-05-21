from pathlib import Path
import glob
import json
import re
from typing import Dict, List, Any


# add space if you encounter upper case unless it is the first letter
def add_space(text):
    if text == "PenTest":
        return "PenTest"
    text = re.sub(r"([A-Z])", r" \1", text)
    return text.lstrip()


def count_score_by_topic(
    dataset: List[Dict[str, Any]], pending_to_remove: List[Dict[str, Any]] = []
):
    score_by_topic = {}
    total_score_by_topic = {}
    score = 0
    for dataset_row in dataset:
        if dataset_row in pending_to_remove:
            continue
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
    score_float["Overall"] = round(
        100 * float(score) / float((len(dataset) - len(pending_to_remove))), 4
    )
    score_fraction["Overall"] = f"{100 * score}/{len(dataset)-len(pending_to_remove)}"
    return score_float, score_fraction


result_path = Path(__file__).parent.parent.parent / "result"
all_result_files = glob.glob(str(result_path) + "/all_*.json")
leaderboards = []
for eval_result_file in all_result_files:
    leaderboard = {}
    model_name = Path(eval_result_file).stem.split("_")[2]
    creator = Path(eval_result_file).stem.split("_")[1]
    leaderboard["Model"] = model_name
    leaderboard["Creator"] = creator
    if model_name == "gpt-35-turbo" or model_name == "gpt-4":
        leaderboard["Access"] = "API, Web"
    else:
        leaderboard["Access"] = "Weight"
    leaderboard["Submission Date"] = "2023-12-20"
    with open(eval_result_file, "r") as f:
        eval_result = json.load(f)
        pending_to_remove = list(
            filter(lambda x: x["flags"].get("calibrated_answer"), eval_result["detail"])
        )
        pending_to_remove += list(
            filter(lambda x: x["flags"].get("invalid") != None, eval_result["detail"])
        )
        score_float, score_fraction = count_score_by_topic(
            eval_result["detail"], pending_to_remove
        )
        eval_result["score_float"] = score_float
        eval_result["score_fraction"] = score_fraction
        print(eval_result["score_fraction"])
        for topic in eval_result["score_float"]:
            leaderboard[add_space(topic)] = format(
                eval_result["score_float"][topic], ".2f"
            )
        leaderboards.append(leaderboard)

    leaderboards = sorted(leaderboards, key=lambda x: float(x["Overall"]), reverse=True)
    for i in range(len(leaderboards)):
        leaderboards[i]["#"] = str(i + 1)

with open(result_path / "leaderboard.json", "w") as f:
    json.dump(leaderboards, f, ensure_ascii=False, indent=4)
