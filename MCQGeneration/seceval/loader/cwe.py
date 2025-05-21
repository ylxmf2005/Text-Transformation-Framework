from seceval.loader.base.file import FileLoader
from seceval.loader.base import LoaderBase, LoaderType
from seceval.convert import html_to_md
from typing import List
from lxml import etree
import re


def get_element_title(node: etree.ElementBase, depth: int):
    if node.attrib.get("Name") and node.attrib.get("ID"):
        return f'CWE {node.attrib.get("ID")}: {node.attrib.get("Name")}'
    return etree.QName(node.tag).localname


class CWELoader(FileLoader):
    task_name = "cwe"
    # wget https://cwe.mitre.org/data/xml/views/699.xml.zip && unzip 699.xml.zip
    # wget https://cwe.mitre.org/data/xml/views/1000.xml.zip && unzip 1000.xml.zip
    # wget https://cwe.mitre.org/data/xml/views/1194.xml.zip && unzip 1194.xml.zip
    dirname = "/nfs_ml/datasets/SecEval/Vulnerability/raw/"
    filename_pattern = "*.xml"
    parser_profile = {
        "xpath_root": "/cwe:Weakness_Catalog/cwe:Weaknesses/cwe:Weakness",
        "namespaces": {"cwe": "http://cwe.mitre.org/cwe-7"},
        "max_level": 1,
        "node_names": [
            "Weakness",
            "Description",
            "Extended_Description",
            "Demonstrative_Examples",
            "Potential_Mitigations",
        ],
        "get_element_title": get_element_title,
    }
