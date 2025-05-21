from pydantic import BaseModel, Field
from typing import Any, Dict, List
import yaml
from langchain_core.language_models import LanguageModelInput
from langchain.schema.messages import SystemMessage, HumanMessage, BaseMessage
import os
import logging

logger = logging.getLogger(__name__)


class BasePrompt(BaseModel):
    role: str = Field(description="The role that GPT act as")
    task_description: str = Field(
        description="The description of the task that GPT is going to perform"
    )
    system_prompt_template: str = Field(description="System Prompt Template")
    user_prompt_template: str = Field(description="User Prompt Template")
    output_format: str = Field(description="The desired output format of GPT")

    def to_language_model_input(self) -> LanguageModelInput:
        """
        serialize prompt to yaml
        """
        prompt_dict = self.model_dump()
        for key in prompt_dict:
            if isinstance(prompt_dict[key], list):
                prompt_dict[key] = "\n- ".join(prompt_dict[key])
        system_prompt_template: str = prompt_dict.pop("system_prompt_template")
        user_prompt_template: str = prompt_dict.pop("user_prompt_template")

        system_prompt = SystemMessage(
            content=system_prompt_template.format(**prompt_dict)
        )
        user_prompt = HumanMessage(content=user_prompt_template.format(**prompt_dict))

        chat_messages = [system_prompt, user_prompt]
        logger.debug(f"chat_messages: {chat_messages}")

        return chat_messages


class QuestionGenerationPrompt(BasePrompt):
    background: str = Field(
        description="The background of the text use as basis for generating questions"
    )
    text: str = Field(
        description="The text use as basis for generating questions", default=""
    )
    examination_focus: List[str] = Field(
        description="The examination focus of the questions"
    )
    examination_forms: List[str] = Field(
        description="The examination form of the questions"
    )
    requirements: List[str] = Field(
        description="The constraints for generating questions"
    )


class QuestionEvaluationPrompt(BasePrompt):
    background: str = Field(description="The background of the question", default="")
    questions: str = Field(description="The question to be evaluated", default="")
    issues: List[str] = Field(description="The criteria for evaluating the question")
    revision_strategies: List[str] = Field(
        description="The revise requirement for the question"
    )
