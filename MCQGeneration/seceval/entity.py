from pydantic import BaseModel

from typing import Any, Dict, Optional, List
from uuid import uuid4
from enum import Enum

from seceval.crawler import TypedContent


class TextArtifact(BaseModel):
    """
    page_id: the id of the page that contains the artifact
    page_url: the url of the artifact
    page_depth: the depth of the page
    page_type: the type of the page

    id: the unique id of the artifact
    parent_id: the id of the parent artifact
    index: the index of the artifact in the page
    level: the header level of the artifact
    title: the title of the artifact
    html: the html content of the artifact
    text: the text content of the artifact
    """

    page_id: str
    page_uri: str
    page_depth: int = 0
    page_type: str

    id: str
    parent_id: Optional[str] = None
    index: int = 0
    level: int = 0
    title: str = ""
    html: str = ""
    text: str = ""


def find_artifact_descendant(
    artifacts: List[TextArtifact], parent: TextArtifact
) -> List[TextArtifact]:
    children: List[TextArtifact] = []
    for artifact in artifacts:
        if artifact.parent_id == parent.id:
            children.append(artifact)
            children.extend(find_artifact_descendant(artifacts, artifact))
    children = sorted(children, key=lambda x: x.index)
    return children


def get_artifact_hierarchy(
    artifacts: List[TextArtifact], target_artifact: TextArtifact
) -> List[TextArtifact]:
    """
    Get the artifact hierarchy of a specific artifact
    """
    if target_artifact.parent_id is None:
        return [target_artifact]
    else:
        parent_artifact = list(
            filter(lambda x: x.id == target_artifact.parent_id, artifacts)
        )
        if not parent_artifact:
            return [target_artifact]
        return get_artifact_hierarchy(artifacts, parent_artifact[0]) + [target_artifact]


class PageItem(BaseModel):
    """
    id: the unique id of the page
    parent_id: the id of the parent page in the page tree
    uri: the uri of the page, if it is a web page, it is the url of the page, if it is a file, it is the path of the file.
    depth: the depth of the page in the page tree
    type: the mime type of the page
    """

    id: str
    uri: str = ""
    depth: int = 0
    file_path: str = ""
    type: str = ""
    parent_id: Optional[str] = None
    content: Optional[TypedContent] = None


def find_page_descendant(pages: List[PageItem], parent: PageItem) -> List[PageItem]:
    children: List[PageItem] = []
    for page in pages:
        if page.parent_id == parent.id:
            children.append(page)
            children.extend(find_page_descendant(pages, page))
    children = sorted(children, key=lambda x: x.depth)
    return children


def get_page_hierarchy(pages: List[PageItem], target_page: PageItem) -> List[PageItem]:
    """
    Get the page hierarchy of a specific page
    """
    if target_page.parent_id is None:
        return [target_page]
    else:
        try:
            parent_page = list(filter(lambda x: x.id == target_page.parent_id, pages))[
                0
            ]
            return get_page_hierarchy(pages, parent_page) + [target_page]
        except IndexError:
            return [target_page]


gen_uuid = lambda: str(uuid4())


class QuestionTopic(str, Enum):
    WebSecurity = "WebSecurity"
    ApplicationSecurity = "ApplicationSecurity"
    NetworkSecurity = "NetworkSecurity"
    SystemSecurity = "SystemSecurity"
    Cryptography = "Cryptography"
    MemorySafety = "MemorySafety"
    PenTest = "PenTest"
    SoftwareSecurity = "SoftwareSecurity"
    Vulnerability = "Vulnerability"


def to_question_topic(task_name: str, topics: List[str]) -> List[QuestionTopic]:
    result = []
    for topic_raw in topics:
        topic_raw = topic_raw.replace(" ", "")
        try:
            topic = QuestionTopic(topic_raw)
            result.append(topic)
        except:
            continue
    if task_name in ["cwe"] and QuestionTopic.Vulnerability not in result:
        result.append(QuestionTopic.Vulnerability)
    if task_name in ["attck", "d3fend"] and QuestionTopic.PenTest not in result:
        result.append(QuestionTopic.PenTest)
    if (
        task_name in ["mozilla_security", "owasp_wstg"]
        and QuestionTopic.WebSecurity not in result
    ):
        result.append(QuestionTopic.WebSecurity)
    if task_name in ["owasg_mastg"] and QuestionTopic.ApplicationSecurity not in result:
        result.append(QuestionTopic.ApplicationSecurity)

    return result


class Question(BaseModel):
    id: str
    source: str
    question: str
    choices: List[str]
    answer: str
    topics: List[QuestionTopic]
    keyword: str
    text_basis: str
    flags: Dict[str, Any] = {}
    redundant: bool = False
