#!/usr/bin/env python3
"""
MCP Server for RDL (Report Definition Language) Report Editing
Provides high-level tools for reading and modifying SSRS/RDL reports
"""

import json
import sys
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom

# MCP Protocol implementation
class MCPServer:
    def __init__(self):
        self.tools = {}
        self.register_tools()
    
    def register_tools(self):
        """Register all available RDL tools"""
        self.tools = {
            "describe_rdl_report": self.describe_rdl_report,
            "get_rdl_datasets": self.get_rdl_datasets,
            "get_rdl_parameters": self.get_rdl_parameters,
            "get_rdl_columns": self.get_rdl_columns,
            "update_column_header": self.update_column_header,
            "update_column_width": self.update_column_width,
            "update_stored_procedure": self.update_stored_procedure,
            "add_parameter": self.add_parameter,
            "update_parameter": self.update_parameter,
            "validate_rdl": self.validate_rdl,
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "protocolVersion": "0.1.0",
                "serverInfo": {
                    "name": "rdl-mcp-server",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        
        elif method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "describe_rdl_report",
                        "description": "Get a high-level summary of the RDL report structure including datasets, parameters, and table layout",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"}
                            },
                            "required": ["filepath"]
                        }
                    },
                    {
                        "name": "get_rdl_datasets",
                        "description": "Get all datasets in the report with their fields, queries, and stored procedures",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"}
                            },
                            "required": ["filepath"]
                        }
                    },
                    {
                        "name": "get_rdl_parameters",
                        "description": "Get all report parameters with their types, prompts, and valid values",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"}
                            },
                            "required": ["filepath"]
                        }
                    },
                    {
                        "name": "get_rdl_columns",
                        "description": "Get table columns with their headers, widths, field bindings, and formatting",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"}
                            },
                            "required": ["filepath"]
                        }
                    },
                    {
                        "name": "update_column_header",
                        "description": "Update a column header text in the report table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "old_header": {"type": "string", "description": "Current header text to find"},
                                "new_header": {"type": "string", "description": "New header text"}
                            },
                            "required": ["filepath", "old_header", "new_header"]
                        }
                    },
                    {
                        "name": "update_column_width",
                        "description": "Update a column width in the report table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "column_index": {"type": "integer", "description": "Zero-based column index"},
                                "new_width": {"type": "string", "description": "New width (e.g., '2.5in', '3cm')"}
                            },
                            "required": ["filepath", "column_index", "new_width"]
                        }
                    },
                    {
                        "name": "update_stored_procedure",
                        "description": "Update the stored procedure name/path for a dataset",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "dataset_name": {"type": "string", "description": "Name of the dataset to update"},
                                "new_sproc": {"type": "string", "description": "New stored procedure name"}
                            },
                            "required": ["filepath", "dataset_name", "new_sproc"]
                        }
                    },
                    {
                        "name": "add_parameter",
                        "description": "Add a new report parameter",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "name": {"type": "string", "description": "Parameter name"},
                                "data_type": {"type": "string", "description": "Data type (String, Integer, DateTime, Boolean)"},
                                "prompt": {"type": "string", "description": "User-facing prompt text"}
                            },
                            "required": ["filepath", "name", "data_type", "prompt"]
                        }
                    },
                    {
                        "name": "update_parameter",
                        "description": "Update an existing report parameter",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "name": {"type": "string", "description": "Parameter name"},
                                "prompt": {"type": "string", "description": "New prompt text"},
                                "default_value": {"type": "string", "description": "New default value"}
                            },
                            "required": ["filepath", "name"]
                        }
                    },
                    {
                        "name": "validate_rdl",
                        "description": "Validate the RDL XML structure and report any issues",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"}
                            },
                            "required": ["filepath"]
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**tool_args)
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                except Exception as e:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error: {str(e)}"
                            }
                        ],
                        "isError": True
                    }
        
        return {"error": "Unknown method"}
    
    # ===== RDL Tool Implementations =====
    
    def _parse_rdl(self, filepath: str) -> ET.Element:
        """Parse RDL XML file and return root element"""
        tree = ET.parse(filepath)
        return tree.getroot()
    
    def _get_namespace(self, root: ET.Element) -> str:
        """Extract the namespace from the root element"""
        # RDL namespace is typically http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition
        if root.tag.startswith('{'):
            return root.tag.split('}')[0] + '}'
        return ''
    
    def describe_rdl_report(self, filepath: str) -> Dict[str, Any]:
        """Get high-level report structure summary"""
        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)
        
        # Get datasets
        datasets = []
        for dataset in root.findall(f'.//{ns}DataSet'):
            name = dataset.get('Name')
            query = dataset.find(f'{ns}Query')
            command_type = query.find(f'{ns}CommandType').text if query.find(f'{ns}CommandType') is not None else 'Unknown'
            command_text = query.find(f'{ns}CommandText').text if query.find(f'{ns}CommandText') is not None else 'N/A'
            
            field_count = len(dataset.findall(f'.//{ns}Field'))
            
            datasets.append({
                'name': name,
                'command_type': command_type,
                'command': command_text,
                'field_count': field_count
            })
        
        # Get parameters
        param_count = len(root.findall(f'.//{ns}ReportParameter'))
        
        # Get table info
        tablix = root.find(f'.//{ns}Tablix')
        column_count = len(tablix.findall(f'.//{ns}TablixColumn')) if tablix is not None else 0
        
        return {
            'report_summary': {
                'datasets': len(datasets),
                'parameters': param_count,
                'table_columns': column_count
            },
            'datasets': datasets,
            'filepath': filepath
        }
    
    def get_rdl_datasets(self, filepath: str) -> Dict[str, Any]:
        """Get detailed dataset information"""
        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)
        
        datasets = []
        for dataset in root.findall(f'.//{ns}DataSet'):
            name = dataset.get('Name')
            query = dataset.find(f'{ns}Query')
            
            # Query info
            command_type = query.find(f'{ns}CommandType').text if query.find(f'{ns}CommandType') is not None else 'Unknown'
            command_text = query.find(f'{ns}CommandText').text if query.find(f'{ns}CommandText') is not None else ''
            datasource = query.find(f'{ns}DataSourceName').text if query.find(f'{ns}DataSourceName') is not None else ''
            
            # Query parameters
            query_params = []
            for qparam in query.findall(f'.//{ns}QueryParameter'):
                query_params.append({
                    'name': qparam.get('Name'),
                    'value': qparam.find(f'{ns}Value').text if qparam.find(f'{ns}Value') is not None else ''
                })
            
            # Fields
            fields = []
            for field in dataset.findall(f'.//{ns}Field'):
                field_name = field.get('Name')
                data_field = field.find(f'{ns}DataField').text if field.find(f'{ns}DataField') is not None else ''
                # Look for TypeName in the rd namespace
                rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'
                type_name_elem = field.find(f'.//{rd_ns}TypeName')
                type_name = type_name_elem.text if type_name_elem is not None else 'Unknown'
                
                fields.append({
                    'name': field_name,
                    'data_field': data_field,
                    'type': type_name
                })
            
            datasets.append({
                'name': name,
                'datasource': datasource,
                'command_type': command_type,
                'command_text': command_text,
                'query_parameters': query_params,
                'fields': fields
            })
        
        return {'datasets': datasets}
    
    def get_rdl_parameters(self, filepath: str) -> Dict[str, Any]:
        """Get report parameters"""
        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)
        
        parameters = []
        for param in root.findall(f'.//{ns}ReportParameter'):
            name = param.get('Name')
            data_type = param.find(f'{ns}DataType').text if param.find(f'{ns}DataType') is not None else 'String'
            prompt = param.find(f'{ns}Prompt').text if param.find(f'{ns}Prompt') is not None else ''
            
            # Default value
            default_elem = param.find(f'{ns}DefaultValue/{ns}Values/{ns}Value')
            default_value = default_elem.text if default_elem is not None else None
            
            # Valid values
            valid_values = []
            
            # Check for static parameter values
            for pv in param.findall(f'.//{ns}ParameterValue'):
                value = pv.find(f'{ns}Value').text if pv.find(f'{ns}Value') is not None else ''
                label = pv.find(f'{ns}Label').text if pv.find(f'{ns}Label') is not None else value
                valid_values.append({'value': value, 'label': label})
            
            # Check for dataset reference
            dataset_ref = param.find(f'{ns}ValidValues/{ns}DataSetReference')
            if dataset_ref is not None:
                valid_values.append({
                    'type': 'dataset_reference',
                    'dataset': dataset_ref.find(f'{ns}DataSetName').text if dataset_ref.find(f'{ns}DataSetName') is not None else '',
                    'value_field': dataset_ref.find(f'{ns}ValueField').text if dataset_ref.find(f'{ns}ValueField') is not None else '',
                    'label_field': dataset_ref.find(f'{ns}LabelField').text if dataset_ref.find(f'{ns}LabelField') is not None else ''
                })
            
            parameters.append({
                'name': name,
                'data_type': data_type,
                'prompt': prompt,
                'default_value': default_value,
                'valid_values': valid_values
            })
        
        return {'parameters': parameters}
    
    def get_rdl_columns(self, filepath: str) -> Dict[str, Any]:
        """Get table column information"""
        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)
        
        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            return {'error': 'No Tablix (table) found in report'}
        
        # Get column widths
        widths = []
        for col in tablix.findall(f'.//{ns}TablixColumn'):
            width = col.find(f'{ns}Width').text if col.find(f'{ns}Width') is not None else 'Unknown'
            widths.append(width)
        
        # Get header row (usually the first or second row with header text)
        columns = []
        header_rows = tablix.findall(f'.//{ns}TablixRow')
        
        # Find the header row (usually has bold text and "header" style content)
        header_cells = []
        for row in header_rows:
            cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
            if cells:
                # Check if this looks like a header row (has TextRun values that don't start with =)
                first_cell = cells[0] if cells else None
                if first_cell is not None:
                    textrun = first_cell.find(f'.//{ns}TextRun/{ns}Value')
                    if textrun is not None and textrun.text and not textrun.text.startswith('='):
                        header_cells = cells
                        break
        
        # Extract header information
        for idx, cell in enumerate(header_cells):
            textbox = cell.find(f'.//{ns}Textbox')
            textbox_name = textbox.get('Name') if textbox is not None else f'Unknown_{idx}'
            
            # Get header text
            textrun = cell.find(f'.//{ns}TextRun/{ns}Value')
            header_text = textrun.text if textrun is not None and textrun.text else 'Unknown'
            
            # Skip if it's a data binding (starts with =)
            if header_text.startswith('='):
                continue
            
            width = widths[idx] if idx < len(widths) else 'Unknown'
            
            columns.append({
                'index': idx,
                'header': header_text,
                'width': width,
                'textbox_name': textbox_name
            })
        
        return {'columns': columns}
    
    def update_column_header(self, filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
        """Update a column header text"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        
        found = False
        # Find all TextRun Value elements
        for value_elem in root.findall(f'.//{ns}TextRun/{ns}Value'):
            if value_elem.text == old_header:
                value_elem.text = new_header
                found = True
        
        if found:
            # Write back to file with proper formatting
            self._write_xml(tree, filepath)
            return {'success': True, 'message': f'Updated header from "{old_header}" to "{new_header}"'}
        else:
            return {'success': False, 'message': f'Header "{old_header}" not found'}
    
    def update_column_width(self, filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
        """Update a column width"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        
        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            return {'success': False, 'message': 'No Tablix found'}
        
        columns = tablix.findall(f'.//{ns}TablixColumn')
        if column_index >= len(columns):
            return {'success': False, 'message': f'Column index {column_index} out of range (max: {len(columns)-1})'}
        
        width_elem = columns[column_index].find(f'{ns}Width')
        if width_elem is not None:
            old_width = width_elem.text
            width_elem.text = new_width
            self._write_xml(tree, filepath)
            return {'success': True, 'message': f'Updated column {column_index} width from {old_width} to {new_width}'}
        
        return {'success': False, 'message': 'Width element not found'}
    
    def update_stored_procedure(self, filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
        """Update stored procedure name for a dataset"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        
        # Find the dataset
        for dataset in root.findall(f'.//{ns}DataSet'):
            if dataset.get('Name') == dataset_name:
                query = dataset.find(f'{ns}Query')
                if query is not None:
                    command_text = query.find(f'{ns}CommandText')
                    if command_text is not None:
                        old_sproc = command_text.text
                        command_text.text = new_sproc
                        self._write_xml(tree, filepath)
                        return {'success': True, 'message': f'Updated stored procedure from "{old_sproc}" to "{new_sproc}"'}
        
        return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}
    
    def add_parameter(self, filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
        """Add a new report parameter"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        
        # Find ReportParameters element
        report_params = root.find(f'{ns}ReportParameters')
        if report_params is None:
            # Create if doesn't exist
            report_params = ET.SubElement(root, f'{ns}ReportParameters')
        
        # Create new parameter
        new_param = ET.SubElement(report_params, f'{ns}ReportParameter')
        new_param.set('Name', name)
        
        # Add data type
        dt = ET.SubElement(new_param, f'{ns}DataType')
        dt.text = data_type
        
        # Add prompt
        p = ET.SubElement(new_param, f'{ns}Prompt')
        p.text = prompt
        
        self._write_xml(tree, filepath)
        return {'success': True, 'message': f'Added parameter "{name}" with type {data_type}'}
    
    def update_parameter(self, filepath: str, name: str, prompt: Optional[str] = None, 
                        default_value: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing parameter"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        
        # Find the parameter
        for param in root.findall(f'.//{ns}ReportParameter'):
            if param.get('Name') == name:
                changes = []
                
                if prompt is not None:
                    prompt_elem = param.find(f'{ns}Prompt')
                    if prompt_elem is not None:
                        prompt_elem.text = prompt
                        changes.append(f'prompt to "{prompt}"')
                
                if default_value is not None:
                    # Find or create DefaultValue structure
                    default_elem = param.find(f'{ns}DefaultValue')
                    if default_elem is None:
                        default_elem = ET.SubElement(param, f'{ns}DefaultValue')
                    
                    values_elem = default_elem.find(f'{ns}Values')
                    if values_elem is None:
                        values_elem = ET.SubElement(default_elem, f'{ns}Values')
                    
                    value_elem = values_elem.find(f'{ns}Value')
                    if value_elem is None:
                        value_elem = ET.SubElement(values_elem, f'{ns}Value')
                    
                    value_elem.text = default_value
                    changes.append(f'default value to "{default_value}"')
                
                if changes:
                    self._write_xml(tree, filepath)
                    return {'success': True, 'message': f'Updated parameter "{name}": {", ".join(changes)}'}
                else:
                    return {'success': False, 'message': 'No changes specified'}
        
        return {'success': False, 'message': f'Parameter "{name}" not found'}
    
    def validate_rdl(self, filepath: str) -> Dict[str, Any]:
        """Validate RDL XML structure"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            ns = self._get_namespace(root)
            
            issues = []
            
            # Check for datasets
            datasets = root.findall(f'.//{ns}DataSet')
            if not datasets:
                issues.append('No datasets found')
            
            # Check each dataset has a query
            for dataset in datasets:
                name = dataset.get('Name', 'Unknown')
                query = dataset.find(f'{ns}Query')
                if query is None:
                    issues.append(f'Dataset "{name}" has no Query element')
            
            # Check for at least one Tablix
            tablix = root.find(f'.//{ns}Tablix')
            if tablix is None:
                issues.append('No Tablix (table) found')
            
            if issues:
                return {
                    'valid': False,
                    'issues': issues
                }
            else:
                return {
                    'valid': True,
                    'message': 'RDL structure is valid'
                }
        
        except ET.ParseError as e:
            return {
                'valid': False,
                'issues': [f'XML Parse Error: {str(e)}']
            }
        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Error: {str(e)}']
            }
    
    def _write_xml(self, tree: ET.ElementTree, filepath: str):
        """Write XML tree back to file with proper formatting"""
        # Convert to string
        xml_str = ET.tostring(tree.getroot(), encoding='utf-8')
        
        # Pretty print using minidom
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
        
        # Remove extra blank lines
        lines = [line for line in pretty_xml.decode('utf-8').split('\n') if line.strip()]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def main():
    """Main entry point for MCP server"""
    server = MCPServer()
    
    # Read from stdin, write to stdout (MCP protocol)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON"}
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
