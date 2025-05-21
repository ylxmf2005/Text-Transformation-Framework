from pathlib import Path
import os
from seceval.entity import PageItem, TextArtifact, Question
from seceval.question.prompt import QuestionEvaluationPrompt, QuestionGenerationPrompt
from typing import List
from langchain.schema.messages import BaseMessage
import json
import yaml
import logging
import os

logger = logging.getLogger(__name__)


def get_dataset_path():
    output_path = Path(__file__).parent.parent / "dataset"
    if not output_path.exists():
        output_path.mkdir()
    return output_path


def get_data_path():
    output_path = Path(__file__).parent.parent / "data"
    if not output_path.exists():
        output_path.mkdir()
    return output_path


def get_prompt_path():
    output_path = Path(__file__).parent.parent / "prompt"
    if not output_path.exists():
        output_path.mkdir()
    return output_path


def get_question_path():
    output_path = Path(__file__).parent.parent / "question"
    if not output_path.exists():
        output_path.mkdir()
    return output_path


def save_artifacts(task_name, artifacts: List[TextArtifact]):
    output_path = get_data_path()
    with open(output_path / f"{task_name}.json", "w") as f:
        artifact_dict = [artifact.model_dump() for artifact in artifacts]
        for artifact in artifact_dict:
            artifact.pop("html")
            pass
        json.dump(artifact_dict, f, ensure_ascii=False)


def save_pages(task_name, pages: List[PageItem]):
    output_path = get_data_path()
    with open(output_path / f"{task_name}_pages.json", "w") as f:
        page_dict = [page.model_dump() for page in pages]
        for page in page_dict:
            page.pop("content")
            page.pop("file_path")
        json.dump(page_dict, f, ensure_ascii=False)


def load_artifacts(task_name):
    output_path = get_data_path()
    with open(output_path / f"{task_name}.json", "r") as f:
        artifact_dict = json.load(f)
        artifacts = [TextArtifact(**artifact) for artifact in artifact_dict]
        # sort by page_url, level, title, text
        artifacts = sorted(artifacts, key=lambda x: (x.level, x.title, x.text))
        # remove duplicate artifacts that has the same page_url, level, title, text
        for i in range(len(artifacts) - 1, 0, -1):
            if (
                artifacts[i].level == artifacts[i - 1].level
                and artifacts[i].title == artifacts[i - 1].title
                and artifacts[i].text == artifacts[i - 1].text
            ):
                artifacts.pop(i)

        return artifacts


def load_pages(task_name):
    output_path = get_data_path()
    with open(output_path / f"{task_name}_pages.json", "r") as f:
        page_dict = json.load(f)
        pages = [PageItem(**page) for page in page_dict]
        return pages


def load_prompt_object(task_name):
    output_path = get_prompt_path()
    if os.path.exists(output_path / f"{task_name}.yaml"):
        with open(output_path / f"{task_name}.yaml", "r") as f:
            prompt = yaml.safe_load(f)
    else:
        logger.warning(f"No prompt file found for task {task_name}, use default prompt")
        prompt = {}

    with open(output_path / f"default.yaml", "r") as f:
        default_prompt = yaml.safe_load(f)
    for key, value in default_prompt.items():
        if key not in prompt:
            prompt[key] = value

    return QuestionGenerationPrompt(**prompt)


def load_evaluation_prompt_object(task_name):
    output_path = get_prompt_path()
    if os.path.exists(output_path / f"{task_name}_eval.yaml"):
        with open(output_path / f"{task_name}_eval.yaml", "r") as f:
            prompt = yaml.safe_load(f)
    else:
        logger.warning(f"No prompt file found for task {task_name}, use default prompt")
        prompt = {}

    with open(output_path / f"default_eval.yaml", "r") as f:
        default_prompt = yaml.safe_load(f)
    for key, value in default_prompt.items():
        if key not in prompt:
            prompt[key] = value
    return QuestionEvaluationPrompt(**prompt)


def save_questions_prompt(task_name, prompts: List[List[BaseMessage]]):
    output_path = get_question_path()
    prompt_str = ""
    for idx, prompt in enumerate(prompts):
        prompt_str += "-" * 10 + "Prompt " + str(idx) + "-" * 10 + "\n"
        prompt_str += "SYSTEM: " + prompt[0].content + "\n" + "USER: " + prompt[1].content  # type: ignore
        prompt_str += "\n" + "-" * 30 + "\n"

    with open(output_path / f"{task_name}_prompt.txt", "w") as f:
        f.write(prompt_str)


def save_questions(task_name, questions):
    output_path = get_question_path()
    with open(output_path / f"{task_name}.json", "w") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)


def load_questions(task_name):
    output_path = get_question_path()
    with open(output_path / f"{task_name}.json", "r") as f:
        questions = json.load(f)
        return questions


def save_evaluation(task_name, evaluation):
    output_path = get_question_path()
    with open(output_path / f"{task_name}_eval.json", "w") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=4)


def load_evaluation(task_name):
    output_path = get_question_path()
    with open(output_path / f"{task_name}_eval.json", "r") as f:
        evaluation = json.load(f)
        return evaluation


def save_evaluation_prompt(task_name, prompts: List[List[BaseMessage]]):
    output_path = get_question_path()
    prompt_str = ""
    for idx, prompt in enumerate(prompts):
        prompt_str += "-" * 10 + "Prompt " + str(idx) + "-" * 10 + "\n"
        prompt_str += "SYSTEM: " + prompt[0].content + "\n" + "USER: " + prompt[1].content  # type: ignore
        prompt_str += "\n" + "-" * 30 + "\n"

    with open(output_path / f"{task_name}_eval_prompt.txt", "w") as f:
        f.write(prompt_str)


def save_dataset(topic_name: str, questions: List[Question], append=False):
    dataset_path = get_dataset_path()
    questions_dict = [question.model_dump() for question in questions]
    if append and Path(dataset_path / f"{topic_name}.json").exists():
        with open(dataset_path / f"{topic_name}.json", "r") as f:
            questions_dict = json.load(f) + questions_dict

    with open(dataset_path / f"{topic_name}.json", "w") as f:
        json.dump(questions_dict, f, ensure_ascii=False, indent=4)
