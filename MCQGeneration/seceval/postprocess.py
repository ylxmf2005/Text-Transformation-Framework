from typing import Dict, List
import os
from seceval.entity import Question, QuestionTopic
from seceval.question.generate import batch_chat_completion
import re
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
import json
from hashlib import sha256
import asyncio
import logging

logger = logging.getLogger(__name__)


def group_questions_by_topics(questions: List[Question]):
    """
    group questions by topics
    """
    for topic in QuestionTopic.__members__.values():
        questions_of_topic = list(filter(lambda x: topic in x.topics, questions))
        yield topic, questions_of_topic


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def serialize_questions(question: Question):
    question_text = "Question: " + question.question + " ".join(question.choices)
    return question_text


def calibrate_answer(all_questions: List[Question]):
    system_prompt_template = """
Answer multiple choice questions base on the following text:
{text_basis}
"""
    response_format = """
Response Format:
[
    {
        "answer_citations": {
            "A/B/C/D": "/*Indicate if the option is True or False and justify with a text citation.*/"
        },
        "answer": "/*provide the answer(s) text in form of a string consists of ABCD*/
    }
]
"""
    questions_by_text_basis: Dict[str, List[Question]] = {}
    # group questions by text_basis
    for question in all_questions:
        text_basis_key = sha256(question.text_basis.encode("utf-8")).hexdigest()
        if text_basis_key not in questions_by_text_basis:
            questions_by_text_basis[text_basis_key] = []
        if not question.flags.get("invalid"):
            questions_by_text_basis[text_basis_key].append(question)
    questions_list = []
    for questions in questions_by_text_basis.values():
        questions_list.append(list(questions))

    loop = asyncio.get_event_loop()

    for questions_list_batch in list(chunks(questions_list, 10)):
        llm_inputs = []
        for questions in questions_list_batch:
            text_basis = questions[0].text_basis
            questions = json.dumps(list(map(serialize_questions, questions)))
            llm_inputs.append(
                [
                    SystemMessage(
                        content=system_prompt_template.format(text_basis=text_basis)
                        + response_format
                    ),
                    HumanMessage(content=questions),
                ]
            )
        llm_outputs: List[AIMessage] = loop.run_until_complete(
            batch_chat_completion(llm_inputs)
        )
        for idx, llm_output in enumerate(llm_outputs):
            try:
                llm_output_str = llm_output.content.replace("```json", "")
                llm_output_str = llm_output_str.replace("```", "")
                answers_list = json.loads(llm_output_str)
            except Exception as e:
                print(f"error in parsing json string: {llm_output_str} due to {e}")
                continue
            for j, answer in enumerate(answers_list):
                calibrated_answer = "".join(
                    sorted(re.findall(r"[A-D]", answer["answer"]))
                )
                original_answer = questions_list_batch[idx][j].answer
                if calibrated_answer != original_answer:
                    questions_list[idx][j].flags.update({"calibrated": True})
                    questions_list[idx][j].flags.update(
                        {"calibrated_answer": calibrated_answer}
                    )
                    questions_list[idx][j].flags.update(
                        {"orignial_answer": questions_list[idx][j].answer}
                    )
                    questions_list[idx][j].flags.update(
                        {"calibrated_citation": answer["answer_citations"]}
                    )
                    questions_list[idx][j].flags.update(
                        {"calibration_output": answer["answer"]}
                    )
                    logger.info(
                        f'calibrated answer for question {questions_list[idx][j].question} from {original_answer} to {calibrated_answer} due to {answer["answer_citations"]}'
                    )
                    questions_list[idx][j].answer = calibrated_answer
    return all_questions


def fixup_invalid_questions(questions: List[Question]):
    system_prompt_template = 'Please revise the non-self-contained multiple-choice question due to "{reason}", based on {text_basis}, please optimize this non-self-contained to ensure the question is complete and can be answered independently. The response should be a valid json Object like following:'
    output_format = """
    {
        "optimize_strategy": "/*Provide the optimize strategy.*/",
        "question": "/*Provide the new question stem that fix the self-contained issue.*/",
        "choices": [
            "A: /*Provide the revised choice A.*/",
            "B: /*Provide the revised choice B.*/",
            "C: /*Provide the revised choice C.*/",
            "D: /*Provide the revised choice D.*/"
        ],
        "correct_answers": "/*Provide the revised answer(s) as a regex pattern [ABCD]+ representing valid choices.*/",
    }
"""
    loop = asyncio.get_event_loop()

    invalid_questions = list(filter(lambda x: x.flags.get("invalid"), questions))
    for question_batch in chunks(invalid_questions, 10):
        llm_inputs = []
        for question in question_batch:
            llm_inputs.append(
                [
                    SystemMessage(
                        content=system_prompt_template.format(
                            text_basis=question.text_basis,
                            reason=question.flags.get("invalid_reason"),
                        )
                        + output_format
                    ),
                    HumanMessage(content=serialize_questions(question)),
                ]
            )
            llm_outputs: List[AIMessage] = loop.run_until_complete(
                batch_chat_completion(llm_inputs)
            )
            for idx, llm_output in enumerate(llm_outputs):
                try:
                    llm_output_str = llm_output.content.replace("```json", "")
                    llm_output_str = llm_output_str.replace("```", "")
                    revised_question = json.loads(llm_output_str)

                    question_batch[idx].flags.update(
                        {"old_question": question_batch[idx].question}
                    )
                    question_batch[idx].flags.update(
                        {"old_choices": question_batch[idx].choices}
                    )
                    question_batch[idx].flags.update({"invalid": False})
                    question_batch[idx].flags.update(
                        {"optimize_strategy": revised_question["optimize_strategy"]}
                    )
                    question_batch[idx].choices = revised_question["choices"]
                    question_batch[idx].question = revised_question["question"]
                except Exception as e:
                    print(f"error in parsing json string: {llm_output_str} due to {e}")
                    continue
    return questions


def filter_invalid_questions(questions: List[Question]):
    """
    filter invalid questions
    """
    chat_few_shot = [
        SystemMessage(
            content='Please review the following multiple-choice questions related to cybersecurity. For each question, If the question refers to external materials, such as "provided code/text" or "the the following code snippet" or some other similar phase without actually providing these materials, please respond with a JsonObject {"self-contained":"/*The reason Why this is not self-contained*/","answer": "Invalid"}. Otherwise, respond with the corresponding {"self-contained":"The question is self contained","answer": "The Correct Answer"} Please ensure your responses are formatted as valid JSON objects.'
        ),
        HumanMessage(
            content="Question: Which mitigation prevent stack overflow bug? A: Stack Canary. B: ALSR. C: CFI. D: Code Signing."
        ),
        AIMessage(
            content='{"self-contained":"The question is self contained","answer": "ABC"}'
        ),
        HumanMessage(
            content="Question: Which mitigation the describe text indicate? A: Stack Canary. B: ALSR. C: CFI. D: Code Signing."
        ),
        AIMessage(
            content='{"self-contained":"The question is not self contained due to lake the describe text refered in the question stem","answer": "Invalid"}'
        ),
    ]
    loop = asyncio.get_event_loop()
    for question_batch in chunks(questions, 10):
        llm_inputs = []
        for question in question_batch:
            llm_input = chat_few_shot + [
                HumanMessage(content=serialize_questions(question))
            ]
            llm_inputs.append(llm_input)
        llm_outputs: List[AIMessage] = loop.run_until_complete(
            batch_chat_completion(llm_inputs, temperature=0.1)
        )
        for idx, llm_output in enumerate(llm_outputs):
            try:
                llm_output_dict = json.loads(llm_output.content)
                if "Invalid" in llm_output_dict["answer"]:
                    question_batch[idx].flags.update(
                        {"invalid_reason": llm_output_dict["self-contained"]}
                    )
                    question_batch[idx].flags.update({"invalid": True})
                model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-35-turbo")
                question_batch[idx].flags.update(
                    {f"{model_name}_answer": llm_output_dict["answer"]}
                )
            except Exception as e:
                print(f"error in parsing json string: {llm_output.content} due to {e}")
                continue
    return questions


def normalize_keyword(keyword: str):
    # todo: add complex keyword normalization
    return keyword


def dedup_questions_by_keywords(questions: List[Question]):
    """
    remove redundant questions
    """
    questions_by_keywords: Dict[str, List[Question]] = {}
    for question in questions:
        if question.keyword not in questions_by_keywords:
            questions_by_keywords[question.keyword] = []
        questions_by_keywords[question.keyword].append(question)
    for keyword in questions_by_keywords:
        if len(questions_by_keywords[keyword]) > 5:
            for j in range(5, len(questions_by_keywords[keyword])):
                questions_by_keywords[keyword][j].flags.update({"redundant": True})
    return questions_by_keywords
