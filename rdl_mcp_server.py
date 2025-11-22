#!/usr/bin/env python3
"""
MCP Server for RDL (Report Definition Language) Report Editing
Provides high-level tools for reading and modifying SSRS/RDL reports
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# Configure logging
def setup_logging():
    """Configure logging for the RDL MCP Server"""
    # Get log level from environment variable, default to INFO
    log_level = os.environ.get('RDL_MCP_LOG_LEVEL', 'INFO').upper()
    log_file = os.environ.get('RDL_MCP_LOG_FILE')

    # Create logger
    logger = logging.getLogger('rdl_mcp_server')
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (stderr to avoid interfering with MCP protocol on stdout)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log file specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)  # All logs to file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")

    return logger

# Initialize logger
logger = setup_logging()

# MCP Protocol implementation
class MCPServer:
    def __init__(self):
        logger.info("Initializing RDL MCP Server")
        self.tools = {}
        self.register_tools()
        logger.info(f"Registered {len(self.tools)} tools")

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
            "add_column": self.add_column,
            "remove_column": self.remove_column,
            "update_column_format": self.update_column_format,
            "add_dataset_field": self.add_dataset_field,
            "remove_dataset_field": self.remove_dataset_field,
            "validate_rdl": self.validate_rdl,
        }
        logger.debug(f"Registered tools: {', '.join(self.tools.keys())}")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.debug(f"Received request: method={method}, id={request_id}")

        if method == "initialize":
            logger.info("Processing initialize request")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "rdl-mcp-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }

        elif method == "tools/list":
            logger.info("Processing tools/list request")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
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
                        "description": "Get all datasets in the report with their fields, queries, and stored procedures. By default returns only field counts; use field_limit to get field details.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "field_limit": {
                                    "type": "integer",
                                    "description": "Number of fields to return per dataset: 0 = no field details (only count, default), -1 = all fields, positive number = limit to that many fields",
                                    "default": 0
                                },
                                "field_pattern": {
                                    "type": "string",
                                    "description": "Optional regex pattern to filter field names (case-insensitive)"
                                }
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
                        "name": "add_column",
                        "description": "Add a new column to the report table at a specified position",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "column_index": {"type": "integer", "description": "Position to insert column (0-based, -1 for end)"},
                                "header_text": {"type": "string", "description": "Header text for the column"},
                                "field_binding": {"type": "string", "description": "Field binding expression (e.g., '=Fields!Amount.Value')"},
                                "width": {"type": "string", "description": "Column width (e.g., '1.5in', '3cm'). Defaults to '1in'"},
                                "format_string": {"type": "string", "description": "Optional format string (e.g., '#,0.00' for numbers or 'dd/MM/yyyy' for dates)"},
                                "footer_expression": {"type": "string", "description": "Optional expression for footer/total row. Examples: '=Sum(Fields!Amount.Value)', '=Count(Fields!ID.Value)', 'Total:', or leave empty for blank footer"}
                            },
                            "required": ["filepath", "column_index", "header_text", "field_binding"]
                        }
                    },
                    {
                        "name": "remove_column",
                        "description": "Remove a column from the report table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "column_index": {"type": "integer", "description": "Zero-based column index to remove"}
                            },
                            "required": ["filepath", "column_index"]
                        }
                    },
                    {
                        "name": "update_column_format",
                        "description": "Update the format string for a column (e.g., date format, number format)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "column_index": {"type": "integer", "description": "Zero-based column index"},
                                "format_string": {"type": "string", "description": "Format string (e.g., '#,0.00' for numbers, 'dd/MM/yyyy' for dates, 'C2' for currency)"}
                            },
                            "required": ["filepath", "column_index", "format_string"]
                        }
                    },
                    {
                        "name": "add_dataset_field",
                        "description": "Add a new field to a dataset (useful when stored procedure returns new columns)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "dataset_name": {"type": "string", "description": "Name of the dataset to modify"},
                                "field_name": {"type": "string", "description": "Name of the field (how it appears in expressions)"},
                                "data_field": {"type": "string", "description": "Name of the column from the data source"},
                                "type_name": {"type": "string", "description": "Data type (e.g., 'System.String', 'System.Int32', 'System.Decimal', 'System.DateTime')"}
                            },
                            "required": ["filepath", "dataset_name", "field_name", "data_field", "type_name"]
                        }
                    },
                    {
                        "name": "remove_dataset_field",
                        "description": "Remove a field from a dataset",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {"type": "string", "description": "Path to the RDL file"},
                                "dataset_name": {"type": "string", "description": "Name of the dataset to modify"},
                                "field_name": {"type": "string", "description": "Name of the field to remove"}
                            },
                            "required": ["filepath", "dataset_name", "field_name"]
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
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            logger.info(f"Tool call: {tool_name}")
            logger.debug(f"Tool arguments: {tool_args}")

            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**tool_args)
                    logger.info(f"Tool {tool_name} completed successfully")
                    logger.debug(f"Tool result: {result}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32000,
                            "message": f"Error: {str(e)}"
                        }
                    }
            else:
                logger.warning(f"Tool not found: {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }

        logger.warning(f"Unknown method: {method}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        }
    
    # ===== RDL Tool Implementations =====
    
    def _parse_rdl(self, filepath: str) -> ET.Element:
        """Parse RDL XML file and return root element"""
        logger.debug(f"Parsing RDL file: {filepath}")
        try:
            # Register namespaces before parsing to preserve prefixes
            self._register_namespaces(filepath)
            tree = ET.parse(filepath)
            root = tree.getroot()
            logger.debug(f"Successfully parsed RDL file: {filepath}")
            return root
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parse error in {filepath}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing {filepath}: {str(e)}")
            raise

    def _register_namespaces(self, filepath: str):
        """Register XML namespaces to preserve prefixes when writing"""
        import re
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Read first 2000 chars to find namespaces

            # Find all namespace declarations like xmlns:prefix="uri"
            ns_pattern = r'xmlns:([a-zA-Z0-9_]+)="([^"]+)"'
            matches = re.findall(ns_pattern, content)

            for prefix, uri in matches:
                logger.debug(f"Registering namespace: {prefix} -> {uri}")
                ET.register_namespace(prefix, uri)

            # Check for default namespace (xmlns="uri")
            default_ns_pattern = r'xmlns="([^"]+)"'
            default_matches = re.findall(default_ns_pattern, content)
            if default_matches:
                # Register with empty prefix for default namespace
                logger.debug(f"Registering default namespace: {default_matches[0]}")
                ET.register_namespace('', default_matches[0])

        except Exception as e:
            logger.warning(f"Failed to register namespaces from {filepath}: {str(e)}")

    def _parse_rdl_tree(self, filepath: str) -> ET.ElementTree:
        """Parse RDL XML file and return ElementTree (for methods that need to write)"""
        logger.debug(f"Parsing RDL tree for modification: {filepath}")
        try:
            # Register namespaces before parsing to preserve prefixes
            self._register_namespaces(filepath)
            tree = ET.parse(filepath)
            logger.debug(f"Successfully parsed RDL tree: {filepath}")
            return tree
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parse error in {filepath}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing {filepath}: {str(e)}")
            raise
    
    def _get_namespace(self, root: ET.Element) -> str:
        """Extract the namespace from the root element"""
        # RDL namespace is typically http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition
        if root.tag.startswith('{'):
            return root.tag.split('}')[0] + '}'
        return ''
    
    def describe_rdl_report(self, filepath: str) -> Dict[str, Any]:
        """Get high-level report structure summary"""
        logger.info(f"Describing RDL report: {filepath}")
        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)
        
        # Get datasets
        datasets = []
        for dataset in root.findall(f'.//{ns}DataSet'):
            name = dataset.get('Name')
            query = dataset.find(f'{ns}Query')

            # Handle datasets without Query elements (e.g., embedded datasets)
            if query is not None:
                command_type = query.find(f'{ns}CommandType').text if query.find(f'{ns}CommandType') is not None else 'Unknown'
                command_text = query.find(f'{ns}CommandText').text if query.find(f'{ns}CommandText') is not None else 'N/A'
            else:
                command_type = 'Embedded'
                command_text = 'N/A'
                logger.debug(f"Dataset '{name}' has no Query element (embedded dataset)")

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

        logger.info(f"Report summary: {len(datasets)} datasets, {param_count} parameters, {column_count} columns")

        return {
            'report_summary': {
                'datasets': len(datasets),
                'parameters': param_count,
                'table_columns': column_count
            },
            'datasets': datasets,
            'filepath': filepath
        }
    
    def get_rdl_datasets(self, filepath: str, field_limit: int = 0, field_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed dataset information

        Args:
            filepath: Path to the RDL file
            field_limit: Number of fields to return per dataset.
                        0 = no field details (only count),
                        -1 = all fields,
                        positive number = limit to that many fields
            field_pattern: Optional regex pattern to filter field names
        """
        import re

        root = self._parse_rdl(filepath)
        ns = self._get_namespace(root)

        datasets = []
        for dataset in root.findall(f'.//{ns}DataSet'):
            name = dataset.get('Name')
            query = dataset.find(f'{ns}Query')

            # Query info - handle embedded datasets without Query elements
            if query is not None:
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
            else:
                # Embedded dataset
                command_type = 'Embedded'
                command_text = ''
                datasource = ''
                query_params = []
                logger.debug(f"Dataset '{name}' has no Query element (embedded dataset)")

            # Fields - get all field elements first
            all_fields = []
            for field in dataset.findall(f'.//{ns}Field'):
                field_name = field.get('Name')
                data_field = field.find(f'{ns}DataField').text if field.find(f'{ns}DataField') is not None else ''
                # Look for TypeName in the rd namespace
                rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'
                type_name_elem = field.find(f'.//{rd_ns}TypeName')
                type_name = type_name_elem.text if type_name_elem is not None else 'Unknown'

                all_fields.append({
                    'name': field_name,
                    'data_field': data_field,
                    'type': type_name
                })

            # Apply filtering if pattern is provided
            if field_pattern:
                try:
                    pattern_re = re.compile(field_pattern, re.IGNORECASE)
                    filtered_fields = [f for f in all_fields if pattern_re.search(f['name'])]
                except re.error as e:
                    logger.warning(f"Invalid field_pattern regex: {field_pattern}, error: {e}")
                    filtered_fields = all_fields
            else:
                filtered_fields = all_fields

            # Build dataset info
            dataset_info = {
                'name': name,
                'datasource': datasource,
                'command_type': command_type,
                'command_text': command_text,
                'query_parameters': query_params,
                'field_count': len(all_fields)
            }

            # Apply field limit
            if field_limit != 0:
                if field_limit == -1:
                    # Return all filtered fields
                    dataset_info['fields'] = filtered_fields
                    dataset_info['fields_truncated'] = False
                else:
                    # Return limited number of fields
                    dataset_info['fields'] = filtered_fields[:field_limit]
                    dataset_info['fields_truncated'] = len(filtered_fields) > field_limit

            datasets.append(dataset_info)

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

        # Get all rows
        all_rows = tablix.findall(f'.//{ns}TablixRow')

        # Find the actual column header row and data row
        # We look for:
        # 1. A row with static text (headers) - but prefer one with multiple headers
        # 2. A row with data bindings (=Fields!...)
        header_row = None
        data_row = None
        best_header_count = 0

        for row_idx, row in enumerate(all_rows):
            cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
            if not cells:
                continue

            # Count how many cells have static text (potential headers)
            static_text_count = 0
            data_binding_count = 0

            for cell in cells:
                textrun = cell.find(f'.//{ns}TextRun/{ns}Value')
                if textrun is not None and textrun.text:
                    text = textrun.text.strip()
                    if text.startswith('='):
                        data_binding_count += 1
                    elif text:  # Non-empty static text
                        static_text_count += 1

            # If this row has more static headers than previous best, it's likely the real header row
            if static_text_count > best_header_count and static_text_count >= len(cells) * 0.5:
                header_row = row
                best_header_count = static_text_count

            # Data row is the one with mostly data bindings
            if data_binding_count >= len(cells) * 0.5 and data_row is None:
                data_row = row

        # If we didn't find a clear header row, fall back to first row with static text
        if header_row is None:
            for row in all_rows:
                cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
                if cells:
                    first_cell = cells[0]
                    textrun = first_cell.find(f'.//{ns}TextRun/{ns}Value')
                    if textrun is not None and textrun.text and not textrun.text.startswith('='):
                        header_row = row
                        break

        # Extract column information
        columns = []

        if header_row is not None:
            header_cells = header_row.findall(f'{ns}TablixCells/{ns}TablixCell')
            data_cells = data_row.findall(f'{ns}TablixCells/{ns}TablixCell') if data_row is not None else []

            for idx, cell in enumerate(header_cells):
                textbox = cell.find(f'.//{ns}Textbox')
                textbox_name = textbox.get('Name') if textbox is not None else f'Unknown_{idx}'

                # Get header text
                textrun = cell.find(f'.//{ns}TextRun/{ns}Value')
                header_text = textrun.text if textrun is not None and textrun.text else ''
                header_text = header_text.strip()

                # Parse dynamic headers (expressions starting with =)
                if header_text.startswith('='):
                    # Try to extract field name from expression like =Fields!Tag_Name.Value
                    if 'Fields!' in header_text:
                        try:
                            # Extract field name between 'Fields!' and the next '.' or ')'
                            field_name_extracted = header_text.split('Fields!')[1].split('.')[0].split(')')[0]
                            header_text = field_name_extracted
                        except:
                            header_text = '(Dynamic Header)'
                    else:
                        header_text = '(Dynamic Header)'

                # Get field binding from data row if available
                field_binding = None
                field_name = None
                format_string = None

                if idx < len(data_cells):
                    data_cell = data_cells[idx]
                    data_textrun = data_cell.find(f'.//{ns}TextRun/{ns}Value')
                    if data_textrun is not None and data_textrun.text:
                        binding = data_textrun.text.strip()
                        if binding.startswith('='):
                            field_binding = binding
                            # Extract field name from =Fields!FieldName.Value pattern
                            if 'Fields!' in binding:
                                try:
                                    field_name = binding.split('Fields!')[1].split('.')[0]
                                except:
                                    pass

                    # Get format string
                    format_elem = data_cell.find(f'.//{ns}TextRun/{ns}Style/{ns}Format')
                    if format_elem is not None and format_elem.text:
                        format_string = format_elem.text

                width = widths[idx] if idx < len(widths) else 'Unknown'

                column_info = {
                    'index': idx,
                    'header': header_text if header_text else '(Empty)',
                    'width': width,
                    'textbox_name': textbox_name
                }

                if field_binding:
                    column_info['field_binding'] = field_binding
                if field_name:
                    column_info['field_name'] = field_name
                if format_string:
                    column_info['format'] = format_string

                columns.append(column_info)

        return {'columns': columns}

    def add_column(self, filepath: str, column_index: int, header_text: str,
                   field_binding: str, width: str = "1in",
                   format_string: Optional[str] = None,
                   footer_expression: Optional[str] = None) -> Dict[str, Any]:
        """Add a new column to the report table at specified position"""
        logger.info(f"Adding column to {filepath}: header='{header_text}', index={column_index}, binding='{field_binding}'")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        # Find the Tablix
        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            logger.error(f"No Tablix found in {filepath}")
            return {'success': False, 'message': 'No Tablix (table) found in report'}

        # Get current columns
        tablix_body = tablix.find(f'{ns}TablixBody')
        tablix_columns = tablix_body.find(f'{ns}TablixColumns')
        current_column_count = len(tablix_columns.findall(f'{ns}TablixColumn'))

        logger.debug(f"Current column count: {current_column_count}")

        # Validate and normalize column_index
        if column_index == -1:
            column_index = current_column_count  # Append at end
            logger.debug(f"Appending column at end (index {column_index})")
        elif column_index < 0 or column_index > current_column_count:
            logger.error(f"Invalid column index: {column_index}, valid range: 0-{current_column_count}")
            return {'success': False, 'message': f'Invalid column_index: {column_index}. Valid range: 0-{current_column_count} or -1'}

        # Generate unique textbox name
        import time
        timestamp = int(time.time() * 1000) % 100000
        textbox_name_base = f"Textbox_Col_{timestamp}"

        # Step 1: Add TablixColumn with width
        new_tablix_column = ET.Element(f'{ns}TablixColumn')
        width_elem = ET.SubElement(new_tablix_column, f'{ns}Width')
        width_elem.text = width

        # Insert at the right position
        tablix_columns.insert(column_index, new_tablix_column)

        # Step 2: Add cells to each row
        tablix_rows = tablix_body.find(f'{ns}TablixRows')
        all_rows = tablix_rows.findall(f'{ns}TablixRow')

        for row_idx, row in enumerate(all_rows):
            tablix_cells = row.find(f'{ns}TablixCells')
            if tablix_cells is None:
                continue

            # Detect row type
            cells = tablix_cells.findall(f'{ns}TablixCell')
            row_type = self._detect_row_type(cells, ns)

            # Create appropriate cell based on row type
            new_cell = self._create_table_cell(
                ns, row_type, row_idx, column_index,
                header_text, field_binding, format_string, textbox_name_base, footer_expression
            )

            # Insert at the right position
            tablix_cells.insert(column_index, new_cell)

        # Step 3: Add TablixMember to TablixColumnHierarchy
        column_hierarchy = tablix.find(f'{ns}TablixColumnHierarchy')
        if column_hierarchy is not None:
            tablix_members = column_hierarchy.find(f'{ns}TablixMembers')
            if tablix_members is not None:
                new_member = ET.Element(f'{ns}TablixMember')
                tablix_members.insert(column_index, new_member)

        # Step 4: Update total width
        self._update_tablix_width(tablix, ns)

        # Write back to file
        self._write_xml(tree, filepath)

        logger.info(f"Successfully added column '{header_text}' at position {column_index}, new total: {current_column_count + 1}")

        return {
            'success': True,
            'message': f'Added column "{header_text}" at position {column_index}',
            'details': {
                'column_index': column_index,
                'header_text': header_text,
                'field_binding': field_binding,
                'width': width,
                'total_columns': current_column_count + 1
            }
        }

    def _detect_row_type(self, cells: List[ET.Element], ns: str) -> str:
        """Detect the type of row (header, data, footer, etc.)"""
        if not cells:
            return 'empty'

        # Count different types of content
        static_text_count = 0
        data_binding_count = 0
        aggregate_count = 0
        empty_count = 0

        for cell in cells:
            textrun = cell.find(f'.//{ns}TextRun/{ns}Value')
            if textrun is not None and textrun.text:
                text = textrun.text.strip()
                if not text:
                    empty_count += 1
                elif text.startswith('='):
                    # Check if it's an aggregate function
                    if any(func in text for func in ['Sum(', 'Count(', 'Avg(', 'Min(', 'Max(', 'First(']):
                        aggregate_count += 1
                    else:
                        data_binding_count += 1
                else:
                    static_text_count += 1
            else:
                empty_count += 1

        total_cells = len(cells)

        # Determine row type based on content
        if static_text_count >= total_cells * 0.5:
            return 'header'
        elif data_binding_count >= total_cells * 0.5:
            return 'data'
        elif aggregate_count >= 1:
            return 'footer'
        else:
            return 'empty'

    def _create_table_cell(self, ns: str, row_type: str, row_idx: int,
                          col_idx: int, header_text: str, field_binding: str,
                          format_string: Optional[str], textbox_name_base: str,
                          footer_expression: Optional[str] = None) -> ET.Element:
        """Create a new TablixCell based on row type"""
        cell = ET.Element(f'{ns}TablixCell')
        cell_contents = ET.SubElement(cell, f'{ns}CellContents')

        # Generate unique textbox name
        textbox_name = f"{textbox_name_base}_{row_idx}"
        textbox = ET.SubElement(cell_contents, f'{ns}Textbox')
        textbox.set('Name', textbox_name)

        # Add textbox properties
        can_grow = ET.SubElement(textbox, f'{ns}CanGrow')
        can_grow.text = 'true'
        keep_together = ET.SubElement(textbox, f'{ns}KeepTogether')
        keep_together.text = 'true'

        # Create paragraphs
        paragraphs = ET.SubElement(textbox, f'{ns}Paragraphs')
        paragraph = ET.SubElement(paragraphs, f'{ns}Paragraph')
        text_runs = ET.SubElement(paragraph, f'{ns}TextRuns')
        text_run = ET.SubElement(text_runs, f'{ns}TextRun')
        value = ET.SubElement(text_run, f'{ns}Value')

        # Set content based on row type
        if row_type == 'header':
            value.text = header_text
            # Style for header
            style = ET.SubElement(text_run, f'{ns}Style')
            font_family = ET.SubElement(style, f'{ns}FontFamily')
            font_family.text = 'Arial Narrow'
            font_size = ET.SubElement(style, f'{ns}FontSize')
            font_size.text = '11pt'
            font_weight = ET.SubElement(style, f'{ns}FontWeight')
            font_weight.text = 'Bold'
        elif row_type == 'data':
            value.text = field_binding
            # Style for data
            style = ET.SubElement(text_run, f'{ns}Style')
            font_family = ET.SubElement(style, f'{ns}FontFamily')
            font_family.text = 'Arial Narrow'
            if format_string:
                format_elem = ET.SubElement(style, f'{ns}Format')
                format_elem.text = format_string
            color = ET.SubElement(style, f'{ns}Color')
            color.text = '#333333'
        elif row_type == 'footer':
            # Use the footer_expression if provided, otherwise leave empty
            if footer_expression:
                # If expression doesn't start with '=', add it (for static text)
                if not footer_expression.startswith('=') and not footer_expression.strip() == '':
                    # Static text - use as is
                    value.text = footer_expression
                else:
                    # Expression - use as provided
                    value.text = footer_expression
            else:
                # No footer expression provided - leave empty
                value.text = ''
            # Style for footer
            style = ET.SubElement(text_run, f'{ns}Style')
            font_family = ET.SubElement(style, f'{ns}FontFamily')
            font_family.text = 'Arial Narrow'
            font_weight = ET.SubElement(style, f'{ns}FontWeight')
            font_weight.text = 'Bold'
            if format_string:
                format_elem = ET.SubElement(style, f'{ns}Format')
                format_elem.text = format_string
            color = ET.SubElement(style, f'{ns}Color')
            color.text = '#333333'
        else:  # empty or unknown
            value.text = ''
            style = ET.SubElement(text_run, f'{ns}Style')
            font_family = ET.SubElement(style, f'{ns}FontFamily')
            font_family.text = 'Arial Narrow'
            color = ET.SubElement(style, f'{ns}Color')
            color.text = '#333333'

        # Add paragraph style
        para_style = ET.SubElement(paragraph, f'{ns}Style')

        # Add default name
        rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'
        default_name = ET.SubElement(textbox, f'{rd_ns}DefaultName')
        default_name.text = textbox_name

        # Add textbox style with borders and padding
        textbox_style = ET.SubElement(textbox, f'{ns}Style')
        border = ET.SubElement(textbox_style, f'{ns}Border')
        border_color = ET.SubElement(border, f'{ns}Color')
        border_color.text = 'LightGrey'
        bottom_border = ET.SubElement(textbox_style, f'{ns}BottomBorder')
        bottom_style = ET.SubElement(bottom_border, f'{ns}Style')
        bottom_style.text = 'Solid'

        # Add padding
        for padding in ['PaddingLeft', 'PaddingRight', 'PaddingTop', 'PaddingBottom']:
            pad = ET.SubElement(textbox_style, f'{ns}{padding}')
            pad.text = '2pt'

        return cell

    def _update_tablix_width(self, tablix: ET.Element, ns: str):
        """Update the total width of the Tablix based on column widths"""
        tablix_body = tablix.find(f'{ns}TablixBody')
        tablix_columns = tablix_body.find(f'{ns}TablixColumns')

        total_width = 0.0
        for col in tablix_columns.findall(f'{ns}TablixColumn'):
            width_elem = col.find(f'{ns}Width')
            if width_elem is not None and width_elem.text:
                # Parse width (assuming 'in' units for simplicity)
                width_str = width_elem.text.strip()
                if width_str.endswith('in'):
                    total_width += float(width_str[:-2])
                elif width_str.endswith('cm'):
                    # Convert cm to inches (1 inch = 2.54 cm)
                    total_width += float(width_str[:-2]) / 2.54

        # Update width element
        width_elem = tablix.find(f'{ns}Width')
        if width_elem is not None:
            width_elem.text = f'{total_width:.1f}in'

    def remove_column(self, filepath: str, column_index: int) -> Dict[str, Any]:
        """Remove a column from the report table"""
        logger.info(f"Removing column from {filepath}: index={column_index}")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        # Find the Tablix
        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            logger.error(f"No Tablix found in {filepath}")
            return {'success': False, 'message': 'No Tablix (table) found in report'}

        # Get current columns
        tablix_body = tablix.find(f'{ns}TablixBody')
        tablix_columns = tablix_body.find(f'{ns}TablixColumns')
        columns = tablix_columns.findall(f'{ns}TablixColumn')

        if column_index < 0 or column_index >= len(columns):
            logger.error(f"Invalid column index: {column_index}, valid range: 0-{len(columns)-1}")
            return {'success': False, 'message': f'Invalid column_index: {column_index}. Valid range: 0-{len(columns)-1}'}

        logger.debug(f"Removing column {column_index} of {len(columns)} total columns")

        # Step 1: Remove TablixColumn
        tablix_columns.remove(columns[column_index])

        # Step 2: Remove cells from each row
        tablix_rows = tablix_body.find(f'{ns}TablixRows')
        all_rows = tablix_rows.findall(f'{ns}TablixRow')

        for row in all_rows:
            tablix_cells = row.find(f'{ns}TablixCells')
            if tablix_cells is not None:
                cells = tablix_cells.findall(f'{ns}TablixCell')
                if column_index < len(cells):
                    tablix_cells.remove(cells[column_index])

        # Step 3: Remove TablixMember from TablixColumnHierarchy
        column_hierarchy = tablix.find(f'{ns}TablixColumnHierarchy')
        if column_hierarchy is not None:
            tablix_members = column_hierarchy.find(f'{ns}TablixMembers')
            if tablix_members is not None:
                members = tablix_members.findall(f'{ns}TablixMember')
                if column_index < len(members):
                    tablix_members.remove(members[column_index])

        # Step 4: Update total width
        self._update_tablix_width(tablix, ns)

        # Write back to file
        self._write_xml(tree, filepath)

        logger.info(f"Successfully removed column at index {column_index}, new total: {len(columns) - 1}")

        return {
            'success': True,
            'message': f'Removed column at index {column_index}',
            'details': {
                'column_index': column_index,
                'total_columns': len(columns) - 1
            }
        }

    def update_column_format(self, filepath: str, column_index: int, format_string: str) -> Dict[str, Any]:
        """Update the format string for a column"""
        logger.info(f"Updating column format in {filepath}: column {column_index} -> '{format_string}'")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            logger.error(f"No Tablix found in {filepath}")
            return {'success': False, 'message': 'No Tablix (table) found in report'}

        # Get all rows
        tablix_body = tablix.find(f'{ns}TablixBody')
        tablix_rows = tablix_body.find(f'{ns}TablixRows')
        all_rows = tablix_rows.findall(f'{ns}TablixRow')

        # Find data row (row with field bindings)
        data_row = None
        for row in all_rows:
            cells = row.findall(f'{ns}TablixCells/{ns}TablixCell')
            if not cells:
                continue

            # Check if this row has data bindings
            data_binding_count = 0
            for cell in cells:
                textrun = cell.find(f'.//{ns}TextRun/{ns}Value')
                if textrun is not None and textrun.text and textrun.text.strip().startswith('='):
                    if 'Fields!' in textrun.text:
                        data_binding_count += 1

            if data_binding_count >= len(cells) * 0.5:
                data_row = row
                break

        if data_row is None:
            logger.warning(f"No data row found in {filepath}")
            return {'success': False, 'message': 'No data row found in report table'}

        # Get the cell at the specified column index
        cells = data_row.findall(f'{ns}TablixCells/{ns}TablixCell')
        if column_index >= len(cells):
            logger.error(f"Column index {column_index} out of range (max: {len(cells)-1})")
            return {'success': False, 'message': f'Column index {column_index} out of range (max: {len(cells)-1})'}

        cell = cells[column_index]

        # Find or create the Style/Format element in the TextRun
        textrun = cell.find(f'.//{ns}TextRun')
        if textrun is None:
            logger.error(f"No TextRun found in column {column_index}")
            return {'success': False, 'message': f'No TextRun found in column {column_index}'}

        # Find or create Style element
        style = textrun.find(f'{ns}Style')
        if style is None:
            style = ET.Element(f'{ns}Style')
            # Insert Style after Value element
            value_elem = textrun.find(f'{ns}Value')
            if value_elem is not None:
                value_index = list(textrun).index(value_elem)
                textrun.insert(value_index + 1, style)
            else:
                textrun.append(style)

        # Find or create Format element
        format_elem = style.find(f'{ns}Format')
        if format_elem is None:
            format_elem = ET.SubElement(style, f'{ns}Format')

        old_format = format_elem.text
        format_elem.text = format_string

        # Write back to file
        self._write_xml(tree, filepath)

        logger.info(f"Successfully updated column {column_index} format from '{old_format}' to '{format_string}'")

        return {
            'success': True,
            'message': f'Updated column {column_index} format to "{format_string}"',
            'details': {
                'column_index': column_index,
                'old_format': old_format,
                'new_format': format_string
            }
        }

    def update_column_header(self, filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
        """Update a column header text"""
        logger.info(f"Updating column header in {filepath}: '{old_header}' -> '{new_header}'")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        found = False
        # Find all TextRun Value elements
        for value_elem in root.findall(f'.//{ns}TextRun/{ns}Value'):
            if value_elem.text == old_header:
                value_elem.text = new_header
                found = True
                logger.debug(f"Found and updated header element")

        if found:
            # Write back to file with proper formatting
            self._write_xml(tree, filepath)
            logger.info(f"Successfully updated header from '{old_header}' to '{new_header}'")
            return {'success': True, 'message': f'Updated header from "{old_header}" to "{new_header}"'}
        else:
            logger.warning(f"Header '{old_header}' not found in {filepath}")
            return {'success': False, 'message': f'Header "{old_header}" not found'}
    
    def update_column_width(self, filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
        """Update a column width"""
        logger.info(f"Updating column width in {filepath}: column {column_index} -> {new_width}")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            logger.error(f"No Tablix found in {filepath}")
            return {'success': False, 'message': 'No Tablix found'}

        columns = tablix.findall(f'.//{ns}TablixColumn')
        if column_index >= len(columns):
            logger.error(f"Column index {column_index} out of range (max: {len(columns)-1})")
            return {'success': False, 'message': f'Column index {column_index} out of range (max: {len(columns)-1})'}

        width_elem = columns[column_index].find(f'{ns}Width')
        if width_elem is not None:
            old_width = width_elem.text
            width_elem.text = new_width
            self._write_xml(tree, filepath)
            logger.info(f"Successfully updated column {column_index} width from {old_width} to {new_width}")
            return {'success': True, 'message': f'Updated column {column_index} width from {old_width} to {new_width}'}

        logger.error(f"Width element not found for column {column_index}")
        return {'success': False, 'message': 'Width element not found'}
    
    def update_stored_procedure(self, filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
        """Update stored procedure name for a dataset"""
        logger.info(f"Updating stored procedure in {filepath}: dataset '{dataset_name}' -> '{new_sproc}'")
        tree = self._parse_rdl_tree(filepath)
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
                        logger.info(f"Successfully updated stored procedure from '{old_sproc}' to '{new_sproc}'")
                        return {'success': True, 'message': f'Updated stored procedure from "{old_sproc}" to "{new_sproc}"'}

        logger.warning(f"Dataset '{dataset_name}' not found in {filepath}")
        return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}

    def add_dataset_field(self, filepath: str, dataset_name: str, field_name: str,
                         data_field: str, type_name: str) -> Dict[str, Any]:
        """Add a new field to a dataset"""
        logger.info(f"Adding field to dataset '{dataset_name}' in {filepath}: {field_name} ({type_name})")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)
        rd_ns = '{http://schemas.microsoft.com/SQLServer/reporting/reportdesigner}'

        # Find the dataset
        dataset = None
        for ds in root.findall(f'.//{ns}DataSet'):
            if ds.get('Name') == dataset_name:
                dataset = ds
                break

        if dataset is None:
            logger.warning(f"Dataset '{dataset_name}' not found in {filepath}")
            return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}

        # Find or create Fields element
        fields_elem = dataset.find(f'{ns}Fields')
        if fields_elem is None:
            logger.debug(f"Creating Fields element for dataset '{dataset_name}'")
            fields_elem = ET.Element(f'{ns}Fields')
            # Insert Fields after Query element if it exists, otherwise at the beginning
            query_elem = dataset.find(f'{ns}Query')
            if query_elem is not None:
                query_index = list(dataset).index(query_elem)
                dataset.insert(query_index + 1, fields_elem)
            else:
                dataset.insert(0, fields_elem)

        # Check if field already exists
        for field in fields_elem.findall(f'{ns}Field'):
            if field.get('Name') == field_name:
                logger.warning(f"Field '{field_name}' already exists in dataset '{dataset_name}'")
                return {'success': False, 'message': f'Field "{field_name}" already exists in dataset "{dataset_name}"'}

        # Create new field
        new_field = ET.Element(f'{ns}Field')
        new_field.set('Name', field_name)

        # Add DataField
        data_field_elem = ET.SubElement(new_field, f'{ns}DataField')
        data_field_elem.text = data_field

        # Add TypeName (in rd namespace)
        type_name_elem = ET.SubElement(new_field, f'{rd_ns}TypeName')
        type_name_elem.text = type_name

        # Add the field to the dataset
        fields_elem.append(new_field)

        # Write back to file
        self._write_xml(tree, filepath)

        logger.info(f"Successfully added field '{field_name}' to dataset '{dataset_name}'")

        return {
            'success': True,
            'message': f'Added field "{field_name}" to dataset "{dataset_name}"',
            'details': {
                'dataset_name': dataset_name,
                'field_name': field_name,
                'data_field': data_field,
                'type_name': type_name
            }
        }

    def remove_dataset_field(self, filepath: str, dataset_name: str, field_name: str) -> Dict[str, Any]:
        """Remove a field from a dataset"""
        logger.info(f"Removing field '{field_name}' from dataset '{dataset_name}' in {filepath}")
        tree = self._parse_rdl_tree(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        # Find the dataset
        dataset = None
        for ds in root.findall(f'.//{ns}DataSet'):
            if ds.get('Name') == dataset_name:
                dataset = ds
                break

        if dataset is None:
            logger.warning(f"Dataset '{dataset_name}' not found in {filepath}")
            return {'success': False, 'message': f'Dataset "{dataset_name}" not found'}

        # Find Fields element
        fields_elem = dataset.find(f'{ns}Fields')
        if fields_elem is None:
            logger.warning(f"No fields found in dataset '{dataset_name}'")
            return {'success': False, 'message': f'No fields found in dataset "{dataset_name}"'}

        # Find and remove the field
        field_found = False
        for field in fields_elem.findall(f'{ns}Field'):
            if field.get('Name') == field_name:
                fields_elem.remove(field)
                field_found = True
                logger.debug(f"Removed field '{field_name}' from dataset '{dataset_name}'")
                break

        if not field_found:
            logger.warning(f"Field '{field_name}' not found in dataset '{dataset_name}'")
            return {'success': False, 'message': f'Field "{field_name}" not found in dataset "{dataset_name}"'}

        # Write back to file
        self._write_xml(tree, filepath)

        logger.info(f"Successfully removed field '{field_name}' from dataset '{dataset_name}'")

        return {
            'success': True,
            'message': f'Removed field "{field_name}" from dataset "{dataset_name}"',
            'details': {
                'dataset_name': dataset_name,
                'field_name': field_name
            }
        }
    
    def add_parameter(self, filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
        """Add a new report parameter"""
        tree = self._parse_rdl_tree(filepath)
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
        tree = self._parse_rdl_tree(filepath)
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

            # Check each dataset has a query or is embedded
            for dataset in datasets:
                name = dataset.get('Name', 'Unknown')
                query = dataset.find(f'{ns}Query')
                # Embedded datasets (like parameter lookup tables) don't need Query elements
                # They're valid as long as they have fields
                if query is None:
                    fields = dataset.findall(f'.//{ns}Field')
                    if not fields:
                        issues.append(f'Dataset "{name}" has no Query element and no Fields')
            
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
    
    def _indent_xml(self, elem, level=0):
        """Add indentation to XML elements for pretty printing without changing namespace structure"""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def _write_xml(self, tree: ET.ElementTree, filepath: str):
        """Write XML tree back to file with proper formatting"""
        logger.debug(f"Writing XML to file: {filepath}")
        try:
            # Use ElementTree with custom indentation (avoids minidom which reorganizes namespaces)
            root = tree.getroot()
            self._indent_xml(root)

            tree.write(
                filepath,
                encoding='utf-8',
                xml_declaration=True,
                method='xml'
            )

            logger.info(f"Successfully wrote XML to {filepath}")
        except Exception as e:
            logger.error(f"Failed to write XML to {filepath}: {str(e)}", exc_info=True)
            raise


def main():
    """Main entry point for MCP server"""
    logger.info("Starting RDL MCP Server")
    logger.info(f"Log level: {logger.level}")
    logger.info(f"Python version: {sys.version}")

    server = MCPServer()

    logger.info("Server ready, listening for requests on stdin")

    # Read from stdin, write to stdout (MCP protocol)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}", exc_info=True)
            error_response = {"error": "Invalid JSON"}
            print(json.dumps(error_response))
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {str(e)}", exc_info=True)
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
