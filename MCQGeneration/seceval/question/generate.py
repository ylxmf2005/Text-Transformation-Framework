from copy import deepcopy
import json
from seceval.llm import setup_model_endpoint, EndpointType
from langchain_core.language_models import LanguageModelInput
import re
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
)
import os
import asyncio
import logging
from typing import Any, Dict, List, Optional

from seceval.question.prompt import QuestionGenerationPrompt, QuestionEvaluationPrompt
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache
from pathlib import Path

from langchain.globals import set_llm_cache

set_llm_cache(
    SQLiteCache(
        database_path=str(Path(__file__).parent.parent.parent / ".langchain.db")
    )
)


logger = logging.getLogger(__name__)

api_key = os.environ["OPENAI_API_KEY"]
api_endpoint = os.environ["OPENAI_API_ENDPOINT"]
api_type = os.environ.get("OPENAI_API_TYPE", "azure")
model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-35-turbo")

azure_params = {
    "deployment_name": model_name,
    "openai_api_base": api_endpoint,
    "openai_api_key": api_key,
    "openai_api_type": api_type,
    "openai_api_version": "2023-07-01-preview",
}

llm = setup_model_endpoint(
    endpoint_type=EndpointType.langchain,
    class_name="AzureChatOpenAI",
    caching_on=False,
    **azure_params,
)


def ai_message_to_json(ai_message: AIMessage):
    assert type(ai_message.content) == str
    json_string = ai_message.content.replace("```json\n", "")
    json_string = json_string.replace("```", "")
    try:
        json_object = json.loads(json_string, strict=False)
    except Exception as e:
        logger.error(f"error in parsing json string: {json_string} due to f{e}")
        json_object = [{"text": json_string, "error": str(e)}]
    return json_object


async def batch_chat_completion(
    model_inputs: List[LanguageModelInput],
    batch_size: int = 10,
    temperature: Optional[float] = None,
) -> List[AIMessage]:
    """
    generate question based on prompt
    """
    result: List[AIMessage] = []
    batch_idx = 0
    batch_model_input: List[LanguageModelInput] = []
    for model_input in model_inputs:
        batch_model_input.append(model_input)
        if len(batch_model_input) == batch_size:
            logger.info(f"processing batch {batch_idx}/{len(model_inputs)//batch_size}")
            llm_response = await llm.abatch(batch_model_input, temperature=temperature)
            result.extend(llm_response)
            batch_model_input = []
            batch_idx += 1
    if len(batch_model_input) > 0:
        llm_response = await llm.abatch(batch_model_input)
        result.extend(llm_response)
    return result


def generate_questions(
    prompt: QuestionGenerationPrompt,
    texts: List[str],
    backgrounds: List[str] = [],
    batch_size: int = 10,
):
    """
    generate question based on prompt
    """
    loop = asyncio.get_event_loop()
    model_inputs = []
    for idx, text in enumerate(texts):
        prompt.text = text
        old_background = prompt.background
        if backgrounds:
            prompt.background = prompt.background + "\n" + backgrounds[idx]
        model_inputs.append(prompt.to_language_model_input())
        prompt.background = old_background
    result = loop.run_until_complete(batch_chat_completion(model_inputs, batch_size))
    result = list(map(ai_message_to_json, result))
    for idx, result_item in enumerate(result):
        if backgrounds:
            background = prompt.background + "\n" + backgrounds[idx]
        else:
            background = prompt.background
        if type(result_item) == list:
            for sub_item in result_item:
                sub_item["text_basis"] = (
                    "The background of the text use as basis for generating questions is:\n"
                    + background
                    + "\n\n"
                    + "The text use as basis for generating questions is:\n"
                    + texts[idx]
                )
        elif type(result_item) == dict:
            result_item["text_basis"] = (
                "The background of the text use as basis for generating questions is:\n"
                + background
                + "\n\n"
                + "The text use as basis for generating questions is:\n"
                + texts[idx]
            )
        else:
            raise Exception(f"unknown type {type(result_item)}")
    return result


def evaluate_questions(
    prompt: QuestionEvaluationPrompt,
    questions_list: List[List[Dict[str, Any]]],
    batch_size: int = 10,
):
    """
    evaluate question based on prompt
    """
    loop = asyncio.get_event_loop()
    model_inputs = []

    for idx, questions in enumerate(questions_list):
        questions_copy = deepcopy(questions)
        if type(questions_copy) == dict:
            questions_copy = [questions_copy]
            questions_list[idx] = [questions_list[idx]]
        for question in questions_copy:
            background = question.pop("text_basis")
            question_keys = list(question.keys())
            for key in question_keys:
                if key not in ["question_description", "choices", "correct_answers"]:
                    question.pop(key)
        prompt.background = background
        prompt.questions = json.dumps(questions_copy)
        model_inputs.append(prompt.to_language_model_input())
    result = loop.run_until_complete(batch_chat_completion(model_inputs, batch_size))
    result = list(map(ai_message_to_json, result))
    for idx, result_item in enumerate(result):
        for sub_idx, sub_item in enumerate(result_item):
            sub_item["original_question"] = questions_list[idx][sub_idx]
    return result
