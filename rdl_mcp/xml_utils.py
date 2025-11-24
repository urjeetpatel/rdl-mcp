"""XML utility functions for RDL file handling."""

import xml.etree.ElementTree as ET
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_namespace(root: ET.Element) -> str:
    """Extract the namespace from the root element."""
    match = re.match(r'\{(.+?)\}', root.tag)
    if match:
        return '{' + match.group(1) + '}'
    return ''


def register_namespaces(filepath: str):
    """Register all namespaces found in the file to preserve them when writing."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find all namespace declarations
    ns_pattern = r'xmlns:([a-zA-Z0-9_]+)="([^"]+)"'
    for match in re.finditer(ns_pattern, content):
        prefix = match.group(1)
        uri = match.group(2)
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass  # Namespace already registered

    # Also register the default namespace if present
    default_ns = re.search(r'xmlns="([^"]+)"', content)
    if default_ns:
        # Can't register default namespace with empty prefix in ElementTree
        # but we track it for reference
        pass


def parse_rdl(filepath: str) -> ET.Element:
    """Parse an RDL file and return the root element."""
    tree = ET.parse(filepath)
    return tree.getroot()


def parse_rdl_tree(filepath: str) -> ET.ElementTree:
    """Parse an RDL file and return the ElementTree (for modifications)."""
    register_namespaces(filepath)
    return ET.parse(filepath)


def indent_xml(elem: ET.Element, level: int = 0):
    """Add indentation to XML elements for pretty printing."""
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            indent_xml(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def write_xml(tree: ET.ElementTree, filepath: str):
    """Write an ElementTree to file with proper formatting."""
    root = tree.getroot()
    indent_xml(root)

    # Write with XML declaration
    with open(filepath, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)

    # Fix the XML declaration to use double quotes (SSRS preference)
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace("'", '"', 2)  # Fix XML declaration quotes
    with open(filepath, 'w') as f:
        f.write(content)


def find_parent(root: ET.Element, target: ET.Element) -> Optional[ET.Element]:
    """Find parent element of target within root's tree."""
    for parent in root.iter():
        for child in parent:
            if child is target:
                return parent
    return None
