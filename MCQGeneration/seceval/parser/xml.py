from lxml import etree
from typing import Any, Callable, Dict, List, Optional, Set
from seceval.convert import xml_to_md
import re

# Assuming these are defined elsewhere in your codebase.
from seceval.entity import PageItem, TextArtifact, gen_uuid
import logging

logger = logging.getLogger(__name__)


class XmlParser:
    get_element_title: Callable[[etree.ElementBase, int], str]

    def __init__(self, profile: Dict[str, Any] = {}):
        self.max_level = profile.get("max_level", 3)
        self.node_names: Optional[Set[str]] = set(profile.get("node_names", []))
        self.xpath_root = profile.get("xpath_root", "/")
        self.namespaces = profile.get("namespaces", {})
        self.get_element_title = profile.get(
            "get_element_title", lambda node, level: etree.QName(node.tag).localname
        )

    def parse(self, item: PageItem) -> List[TextArtifact]:
        assert item.content is not None
        xpath_root = self.xpath_root
        xml_content = item.content.content

        # Parse the XML content
        root = etree.fromstring(xml_content, None)

        # Find the starting node based on the given XPath
        starting_nodes = root.xpath(xpath_root, namespaces=self.namespaces)
        logger.info(
            f"Found {len(starting_nodes)} starting nodes from XPath {xpath_root} and namespaces {self.namespaces}"
        )

        # List to hold the text artifacts
        artifacts: List[TextArtifact] = []

        # Function to recursively parse the XML
        def parse_node(node: etree.ElementBase, level, parent_id):
            local_tag = etree.QName(node.tag).localname
            # Check if node name is in the valid names set, if provided
            if self.node_names is not None and local_tag not in self.node_names:
                return
            if level > self.max_level:
                # Convert all child nodes to a single markdown string
                try:
                    markdown_content = xml_to_md(etree.tostring(node))
                except etree.XMLSyntaxError as e:
                    logger.warning(f"Failed to parse XML Node {node} due to {e}")
                    markdown_content = ""

                artifact = TextArtifact(
                    page_id=item.id,
                    page_uri=item.uri or item.file_path,
                    page_depth=item.depth,
                    page_type=item.type,
                    id=gen_uuid(),
                    index=len(artifacts),
                    title=self.get_element_title(node, level),
                    level=level,
                    parent_id=parent_id,
                    html="",
                    text=markdown_content,
                )
                artifacts.append(artifact)
                return

            # Create a TextArtifact for the current node
            text_content = ("".join(node.xpath("text()"))).strip()
            artifact = TextArtifact(
                page_id=item.id,
                page_uri=item.uri or item.file_path,
                page_depth=item.depth,
                page_type=item.type,
                id=gen_uuid(),
                index=len(artifacts),
                title=self.get_element_title(node, level),
                level=level,
                parent_id=parent_id,
                html="",
                text=text_content,
            )
            artifacts.append(artifact)

            # Parse child nodes
            for child in node.getchildren():
                parse_node(child, level + 1, artifact.id)

        # Parse starting from each node found by the XPath root
        for node in starting_nodes:
            parse_node(node, 1, None)
        logger.info(f"Parsed {len(artifacts)} text artifacts")

        return artifacts
