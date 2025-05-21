from dotenv import load_dotenv
from seceval.entity import gen_uuid

load_dotenv()
from pathlib import Path
import json
import re
from seceval.question.artifact_sampler import get_sampler
from seceval.entity import Question, to_question_topic
import time
from seceval.postprocess import (
    group_questions_by_topics,
    normalize_keyword,
    filter_invalid_questions,
    calibrate_answer,
    fixup_invalid_questions,
)

from seceval.storage import (
    load_artifacts,
    load_evaluation,
    load_evaluation_prompt_object,
    load_questions,
    save_artifacts,
    save_pages,
    load_prompt_object,
    load_pages,
    save_questions,
    save_questions_prompt,
    save_evaluation,
    save_evaluation_prompt,
    save_dataset,
)
from seceval.loader import *
from typing import Any, Dict, List
import random
import argparse
from seceval.loader.base import LoaderBase
from seceval.question.prompt import QuestionGenerationPrompt
from seceval.question.generate import generate_questions, evaluate_questions
import logging
import os

logger = logging.getLogger(__name__)

if os.environ.get("DEBUG"):
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s"
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.FileHandler(f"seceval_{int(time.time())}.log")],
    )

# add more


def load_and_parse(task_name: str):
    loaders: List[LoaderBase] = []

    loaders.append(MIT6858Loader())
    loaders.append(WinSecDocLoader())
    loaders.append(AndroidSecLoader())
    loaders.append(MozillaSecLoader())
    loaders.append(OwaspWstgLoader())
    loaders.append(OwaspMastgLoader())
    loaders.append(CS161Textbook())
    loaders.append(CWELoader())
    loaders.append(LawLoader())
    loaders.append(ATTCKLoader())
    loaders.append(D3FENDLoader())
    loaders.append(ApplePSecDocLoader())
    for loader in loaders:
        if loader.task_name == task_name or task_name == "all":
            pages, artifacts = loader.load()
            save_pages(loader.task_name, pages)
            save_artifacts(loader.task_name, artifacts)


def generate(task_name: str, number: int):
    prompt_object = load_prompt_object(task_name)
    sampler = get_sampler(task_name)
    texts, backgrounds = sampler(number)  # type: ignore
    logger.info(f"Generating questions for {len(texts)} samples")
    questions = generate_questions(prompt_object, texts, backgrounds)
    save_questions(task_name, questions)
    questions_prompt = []
    for idx, text in enumerate(texts):
        prompt_object.text = text
        old_background = prompt_object.background
        if backgrounds:
            prompt_object.background = (
                prompt_object.background + "\n" + backgrounds[idx]
            )
        questions_prompt.append(prompt_object.to_language_model_input())
        prompt_object.background = old_background
    save_questions_prompt(task_name, questions_prompt)
    return questions


def eval(task_name: str, questions_list: List[List[Dict[str, str]]], number: int):
    eval_prompt_object = load_evaluation_prompt_object(task_name)
    eval_prompts = []

    if number != -1:
        questions_list = questions_list[:number]
    evaluation = evaluate_questions(eval_prompt_object, questions_list)
    save_evaluation(task_name, evaluation)
    for questions in questions_list:
        eval_prompt_object.questions = json.dumps(questions)
        eval_prompts.append(eval_prompt_object.to_language_model_input())
    save_evaluation_prompt(task_name, eval_prompts)
    return evaluation


def post_process(task_name: str, questions_list: List[List[Dict[str, str]]]):
    formatted_questions = []
    for questions in questions_list:
        current_formatted_questions = []
        for question in questions:
            question: Dict[str, Any]
            try:
                if question.get("revised_question") is not None:
                    new_question: dict = question["revised_question"]
                    new_question["topic"] = question["original_question"]["topic"]
                    new_question["keyword"] = question["original_question"][
                        "technical_keyword"
                    ]
                    new_question["text_basis"] = question["original_question"][
                        "text_basis"
                    ]
                    question = new_question

                question_text = question["question_description"]
                choices_text = []
                for choice in question["choices"]:
                    choices_text.append(choice + ": " + question["choices"][choice])

                if type(question["technical_keyword"]) == str:
                    keyword = normalize_keyword(question["technical_keyword"])
                else:
                    keyword = normalize_keyword(
                        list(question["technical_keyword"].keys())[0]
                    )

                current_formatted_questions.append(
                    Question(
                        id=gen_uuid(),
                        question=question_text,
                        choices=choices_text,
                        source=task_name,
                        answer="".join(sorted(question["correct_answers"])),
                        topics=to_question_topic(task_name, question["topic"]),
                        keyword=keyword,
                        text_basis=question["text_basis"],
                        flags={},
                    )
                )

            except KeyError as e:
                print(f"error in parsing question {question} due to {e}")

        formatted_questions += current_formatted_questions
    filter_invalid_questions(formatted_questions)
    fixup_invalid_questions(formatted_questions)
    calibrate_answer(formatted_questions)

    save_dataset("all", formatted_questions, append=True)

    for topic, questions in group_questions_by_topics(formatted_questions):
        save_dataset(topic, questions, append=True)


def main():
    parser = argparse.ArgumentParser(description="SecEval CLI")

    parser.add_argument(
        "-t",
        "--task_name",
        default="attck",
        type=str,
        help="Specify the task name to load, parse, generate questions, evaluate questions. If set to 'all' for load and parse, all tasks will be processed",
    )
    parser.add_argument(
        "-n",
        "--number",
        default=2,
        type=int,
        help="Define the number of text artifacts to generate questions for.",
    )
    parser.add_argument(
        "-l",
        "--do_load",
        action="store_true",
        default=False,
        help="Enable loading and parsing.",
    )
    parser.add_argument(
        "-g",
        "--do_generate",
        action="store_true",
        default=False,
        help="Enable question generation.",
    )
    parser.add_argument(
        "-e",
        "--do_eval",
        action="store_true",
        default=False,
        help="Enable question evaluation.",
    )
    parser.add_argument(
        "-p",
        "--do_postprocess",
        action="store_true",
        default=False,
        help="Enable inference.",
    )
    parser.add_argument(
        "--postprocess_on_eval",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-r",
        "--do_random",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if not args.do_random:
        random.seed(666)
    if args.do_load:
        load_and_parse(args.task_name)
    if args.do_generate:
        questions = generate(args.task_name, int(args.number))
    else:
        questions = load_questions(args.task_name)
    if args.do_eval:
        questions_eval = eval(args.task_name, questions, int(args.number))
    elif args.do_postprocess and args.postprocess_on_eval:
        questions_eval = load_evaluation(args.task_name)
    if args.do_postprocess:
        if args.postprocess_on_eval:
            post_process(args.task_name, questions_eval)  # type: ignore
        else:
            post_process(args.task_name, questions)


if __name__ == "__main__":
    main()
