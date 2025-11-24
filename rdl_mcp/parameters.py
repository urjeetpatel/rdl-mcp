"""RDL parameter operations - add, update parameters."""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Optional

from .xml_utils import parse_rdl_tree, get_namespace, write_xml

logger = logging.getLogger(__name__)


def add_parameter(filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
    """Add a new report parameter."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    # Find or create ReportParameters section
    report_params = root.find(f'{ns}ReportParameters')
    if report_params is None:
        report_params = ET.Element(f'{ns}ReportParameters')
        # Insert after DataSets if it exists
        datasets = root.find(f'{ns}DataSets')
        if datasets is not None:
            idx = list(root).index(datasets) + 1
            root.insert(idx, report_params)
        else:
            root.insert(0, report_params)

    # Check if parameter already exists
    for existing_param in report_params.findall(f'{ns}ReportParameter'):
        if existing_param.get('Name') == name:
            return {'success': False, 'message': f'Parameter "{name}" already exists'}

    # Create new parameter
    new_param = ET.SubElement(report_params, f'{ns}ReportParameter')
    new_param.set('Name', name)

    data_type_elem = ET.SubElement(new_param, f'{ns}DataType')
    data_type_elem.text = data_type

    prompt_elem = ET.SubElement(new_param, f'{ns}Prompt')
    prompt_elem.text = prompt

    write_xml(tree, filepath)
    return {'success': True, 'message': f'Added parameter "{name}"'}


def update_parameter(filepath: str, name: str, prompt: Optional[str] = None,
                     default_value: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing report parameter."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    for param in root.findall(f'.//{ns}ReportParameter'):
        if param.get('Name') == name:
            changes = []

            if prompt is not None:
                prompt_elem = param.find(f'{ns}Prompt')
                if prompt_elem is None:
                    prompt_elem = ET.SubElement(param, f'{ns}Prompt')
                prompt_elem.text = prompt
                changes.append(f'prompt to "{prompt}"')

            if default_value is not None:
                default_values = param.find(f'{ns}DefaultValue')
                if default_values is None:
                    default_values = ET.SubElement(param, f'{ns}DefaultValue')

                values = default_values.find(f'{ns}Values')
                if values is None:
                    values = ET.SubElement(default_values, f'{ns}Values')

                value_elem = values.find(f'{ns}Value')
                if value_elem is None:
                    value_elem = ET.SubElement(values, f'{ns}Value')
                value_elem.text = default_value
                changes.append(f'default value to "{default_value}"')

            if changes:
                write_xml(tree, filepath)
                return {'success': True, 'message': f'Updated parameter "{name}": {", ".join(changes)}'}
            else:
                return {'success': False, 'message': 'No changes specified'}

    return {'success': False, 'message': f'Parameter "{name}" not found'}
