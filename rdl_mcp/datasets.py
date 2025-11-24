"""RDL dataset operations - update stored procedure, add/remove fields."""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any

from .xml_utils import parse_rdl_tree, get_namespace, write_xml

logger = logging.getLogger(__name__)


def update_stored_procedure(filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
    """Update the stored procedure name for a dataset."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    for dataset in root.findall(f'.//{ns}DataSet'):
        if dataset.get('Name') == dataset_name:
            query = dataset.find(f'{ns}Query')
            if query is not None:
                command_text = query.find(f'{ns}CommandText')
                if command_text is not None:
                    command_text.text = new_sproc
                    write_xml(tree, filepath)
                    return {'success': True, 'message': f'Updated stored procedure to "{new_sproc}"'}

    return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}


def add_dataset_field(filepath: str, dataset_name: str, field_name: str,
                      data_field: str, type_name: str) -> Dict[str, Any]:
    """Add a new field to a dataset."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)
    rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'

    # Register the rd namespace
    ET.register_namespace('rd', 'http://schemas.microsoft.com/SQLServer/reporting/reportdesigner')

    for dataset in root.findall(f'.//{ns}DataSet'):
        if dataset.get('Name') == dataset_name:
            # Find or create Fields element
            fields = dataset.find(f'{ns}Fields')
            if fields is None:
                # Insert Fields after Query if it exists
                query = dataset.find(f'{ns}Query')
                fields = ET.Element(f'{ns}Fields')
                if query is not None:
                    idx = list(dataset).index(query) + 1
                    dataset.insert(idx, fields)
                else:
                    dataset.insert(0, fields)

            # Check if field already exists
            for existing_field in fields.findall(f'{ns}Field'):
                if existing_field.get('Name') == field_name:
                    return {'success': False, 'message': f'Field "{field_name}" already exists'}

            # Create new field
            new_field = ET.SubElement(fields, f'{ns}Field')
            new_field.set('Name', field_name)

            data_field_elem = ET.SubElement(new_field, f'{ns}DataField')
            data_field_elem.text = data_field

            type_elem = ET.SubElement(new_field, f'{rd_ns}TypeName')
            type_elem.text = type_name

            write_xml(tree, filepath)
            return {'success': True, 'message': f'Added field "{field_name}" to dataset "{dataset_name}"'}

    return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}


def remove_dataset_field(filepath: str, dataset_name: str, field_name: str) -> Dict[str, Any]:
    """Remove a field from a dataset."""
    tree = parse_rdl_tree(filepath)
    root = tree.getroot()
    ns = get_namespace(root)

    for dataset in root.findall(f'.//{ns}DataSet'):
        if dataset.get('Name') == dataset_name:
            fields = dataset.find(f'{ns}Fields')
            if fields is None:
                return {'success': False, 'message': f'Dataset "{dataset_name}" has no fields'}

            for field in fields.findall(f'{ns}Field'):
                if field.get('Name') == field_name:
                    fields.remove(field)
                    write_xml(tree, filepath)
                    return {'success': True, 'message': f'Removed field "{field_name}" from dataset "{dataset_name}"'}

            return {'success': False, 'message': f'Field "{field_name}" not found in dataset "{dataset_name}"'}

    return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}
