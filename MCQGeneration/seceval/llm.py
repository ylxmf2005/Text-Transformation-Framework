from typing import Any, List
from langchain.schema.language_model import BaseLanguageModel

import importlib
from dataclasses import dataclass
from enum import Enum
import logging
import os


@dataclass
class EndpointType(str, Enum):
    langchain = "langchain"
    native_langchain = "native_langchain"


def get_class_from_modules(module_list: List[str], class_name: str) -> Any:
    for module_name in module_list:
        try:
            return getattr(importlib.import_module(module_name), class_name)
        except AttributeError:
            continue
        except Exception as e:
            raise e
    return None


def setup_model_endpoint(
    endpoint_type: EndpointType,
    class_name: str,
    caching_on: bool,
    **kwargs,
) -> BaseLanguageModel:
    if (
        endpoint_type == EndpointType.langchain
        or endpoint_type == EndpointType.native_langchain
    ):
        if caching_on:
            from langchain.cache import SQLiteCache
            from langchain.globals import set_llm_cache

            set_llm_cache(SQLiteCache(database_path=".langchain.db"))

        if endpoint_type == "langchain":
            module_search_paths = [
                "langchain.chat_models",
                "langchain.llms",
            ]
        else:
            module_search_paths = [
                "seceval.question.native_langchain_llms",
            ]

        ep_class = get_class_from_modules(module_search_paths, class_name)

        if ep_class is None:
            raise RuntimeError(f"Unknown class_name {class_name}")

        return ep_class(**kwargs)
    else:
        raise ValueError(f"Unknown endpoint type: {endpoint_type}")
