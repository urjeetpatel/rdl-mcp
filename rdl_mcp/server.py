"""MCP Server for RDL file operations."""

import json
import sys
import logging
from typing import Dict, Any, Optional

from . import reader
from . import columns
from . import datasets
from . import parameters
from . import validation

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server that handles RDL file operations."""

    def __init__(self):
        logger.info("Initializing RDL MCP Server")
        self.tools = {}
        self.register_tools()
        logger.info(f"Registered {len(self.tools)} tools")

    def register_tools(self):
        """Register all available tools."""
        self.tools = {
            'describe_rdl_report': {
                'function': self.describe_rdl_report,
                'description': 'Get a high-level summary of the RDL report structure'
            },
            'get_rdl_datasets': {
                'function': self.get_rdl_datasets,
                'description': 'Get all datasets with their fields, queries, and stored procedures'
            },
            'get_rdl_parameters': {
                'function': self.get_rdl_parameters,
                'description': 'Get all report parameters with their types and values'
            },
            'get_rdl_columns': {
                'function': self.get_rdl_columns,
                'description': 'Get table columns with headers, widths, and bindings'
            },
            'validate_rdl': {
                'function': self.validate_rdl,
                'description': 'Validate RDL XML structure and field references'
            },
            'update_column_header': {
                'function': self.update_column_header,
                'description': 'Update a column header text'
            },
            'update_column_width': {
                'function': self.update_column_width,
                'description': 'Update a column width'
            },
            'update_column_format': {
                'function': self.update_column_format,
                'description': 'Update the format string for a column'
            },
            'update_column_colors': {
                'function': self.update_column_colors,
                'description': 'Update text and background colors for a column\'s data and/or header cells'
            },
            'add_column': {
                'function': self.add_column,
                'description': 'Add a new column to the report table'
            },
            'remove_column': {
                'function': self.remove_column,
                'description': 'Remove a column from the report table'
            },
            'update_stored_procedure': {
                'function': self.update_stored_procedure,
                'description': 'Update the stored procedure for a dataset'
            },
            'add_dataset_field': {
                'function': self.add_dataset_field,
                'description': 'Add a new field to a dataset'
            },
            'remove_dataset_field': {
                'function': self.remove_dataset_field,
                'description': 'Remove a field from a dataset'
            },
            'add_parameter': {
                'function': self.add_parameter,
                'description': 'Add a new report parameter'
            },
            'update_parameter': {
                'function': self.update_parameter,
                'description': 'Update an existing report parameter'
            }
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        method = request.get('method', '')
        params = request.get('params', {})
        request_id = request.get('id')

        logger.debug(f"Handling request: {method}")

        if method == 'initialize':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': '2024-11-05',
                    'serverInfo': {
                        'name': 'rdl-mcp-server',
                        'version': '1.0.0'
                    },
                    'capabilities': {
                        'tools': {}
                    }
                }
            }

        elif method == 'tools/list':
            tools_list = []
            for name, info in self.tools.items():
                tools_list.append({
                    'name': name,
                    'description': info['description'],
                    'inputSchema': self._get_tool_schema(name)
                })
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {'tools': tools_list}
            }

        elif method == 'tools/call':
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})

            if tool_name not in self.tools:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Unknown tool: {tool_name}'
                    }
                }

            try:
                result = self.tools[tool_name]['function'](**tool_args)
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]
                    }
                }
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32000,
                        'message': str(e)
                    }
                }

        elif method == 'notifications/initialized':
            return None

        else:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }

    def _get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the JSON schema for a tool's parameters."""
        schemas = {
            'describe_rdl_report': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string', 'description': 'Path to the RDL file'}
                },
                'required': ['filepath']
            },
            'get_rdl_datasets': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string', 'description': 'Path to the RDL file'},
                    'field_limit': {'type': 'integer', 'description': 'Number of fields to return (0=none, -1=all)', 'default': 0},
                    'field_pattern': {'type': 'string', 'description': 'Regex pattern to filter fields'}
                },
                'required': ['filepath']
            },
            'get_rdl_parameters': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string', 'description': 'Path to the RDL file'}
                },
                'required': ['filepath']
            },
            'get_rdl_columns': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string', 'description': 'Path to the RDL file'}
                },
                'required': ['filepath']
            },
            'validate_rdl': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string', 'description': 'Path to the RDL file'}
                },
                'required': ['filepath']
            },
            'update_column_header': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'old_header': {'type': 'string'},
                    'new_header': {'type': 'string'}
                },
                'required': ['filepath', 'old_header', 'new_header']
            },
            'update_column_width': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'column_index': {'type': 'integer'},
                    'new_width': {'type': 'string'}
                },
                'required': ['filepath', 'column_index', 'new_width']
            },
            'update_column_format': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'column_index': {'type': 'integer'},
                    'format_string': {'type': 'string'}
                },
                'required': ['filepath', 'column_index', 'format_string']
            },
            'update_column_colors': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'column_index': {'type': 'integer'},
                    'text_color': {'type': 'string', 'description': 'Text color for data cells (e.g., "Red", "#FF0000")'},
                    'background_color': {'type': 'string', 'description': 'Background color for data cells'},
                    'header_text_color': {'type': 'string', 'description': 'Text color for header cell'},
                    'header_background_color': {'type': 'string', 'description': 'Background color for header cell'}
                },
                'required': ['filepath', 'column_index']
            },
            'add_column': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'column_index': {'type': 'integer'},
                    'header_text': {'type': 'string'},
                    'field_binding': {'type': 'string'},
                    'width': {'type': 'string', 'default': '1in'},
                    'format_string': {'type': 'string'},
                    'footer_expression': {'type': 'string'}
                },
                'required': ['filepath', 'column_index', 'header_text', 'field_binding']
            },
            'remove_column': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'column_index': {'type': 'integer'},
                    'auto_adjust_page_width': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'If true, shrink page width to fit remaining columns plus margins'
                    }
                },
                'required': ['filepath', 'column_index']
            },
            'update_stored_procedure': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'dataset_name': {'type': 'string'},
                    'new_sproc': {'type': 'string'}
                },
                'required': ['filepath', 'dataset_name', 'new_sproc']
            },
            'add_dataset_field': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'dataset_name': {'type': 'string'},
                    'field_name': {'type': 'string'},
                    'data_field': {'type': 'string'},
                    'type_name': {'type': 'string'}
                },
                'required': ['filepath', 'dataset_name', 'field_name', 'data_field', 'type_name']
            },
            'remove_dataset_field': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'dataset_name': {'type': 'string'},
                    'field_name': {'type': 'string'}
                },
                'required': ['filepath', 'dataset_name', 'field_name']
            },
            'add_parameter': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'name': {'type': 'string'},
                    'data_type': {'type': 'string'},
                    'prompt': {'type': 'string'}
                },
                'required': ['filepath', 'name', 'data_type', 'prompt']
            },
            'update_parameter': {
                'type': 'object',
                'properties': {
                    'filepath': {'type': 'string'},
                    'name': {'type': 'string'},
                    'prompt': {'type': 'string'},
                    'default_value': {'type': 'string'}
                },
                'required': ['filepath', 'name']
            }
        }
        return schemas.get(tool_name, {'type': 'object', 'properties': {}})

    # Delegate methods to modules

    def describe_rdl_report(self, filepath: str) -> Dict[str, Any]:
        return reader.describe_rdl_report(filepath)

    def get_rdl_datasets(self, filepath: str, field_limit: int = 0,
                         field_pattern: Optional[str] = None) -> Dict[str, Any]:
        return reader.get_rdl_datasets(filepath, field_limit, field_pattern)

    def get_rdl_parameters(self, filepath: str) -> Dict[str, Any]:
        return reader.get_rdl_parameters(filepath)

    def get_rdl_columns(self, filepath: str) -> Dict[str, Any]:
        return reader.get_rdl_columns(filepath)

    def validate_rdl(self, filepath: str) -> Dict[str, Any]:
        return validation.validate_rdl(filepath)

    def update_column_header(self, filepath: str, old_header: str, new_header: str) -> Dict[str, Any]:
        return columns.update_column_header(filepath, old_header, new_header)

    def update_column_width(self, filepath: str, column_index: int, new_width: str) -> Dict[str, Any]:
        return columns.update_column_width(filepath, column_index, new_width)

    def update_column_format(self, filepath: str, column_index: int, format_string: str) -> Dict[str, Any]:
        return columns.update_column_format(filepath, column_index, format_string)

    def update_column_colors(self, filepath: str, column_index: int,
                             text_color: Optional[str] = None,
                             background_color: Optional[str] = None,
                             header_text_color: Optional[str] = None,
                             header_background_color: Optional[str] = None) -> Dict[str, Any]:
        return columns.update_column_colors(filepath, column_index, text_color, background_color,
                                            header_text_color, header_background_color)

    def add_column(self, filepath: str, column_index: int, header_text: str,
                   field_binding: str, width: str = "1in",
                   format_string: Optional[str] = None,
                   footer_expression: Optional[str] = None) -> Dict[str, Any]:
        return columns.add_column(filepath, column_index, header_text, field_binding,
                                  width, format_string, footer_expression)

    def remove_column(self, filepath: str, column_index: int,
                      auto_adjust_page_width: bool = True) -> Dict[str, Any]:
        return columns.remove_column(filepath, column_index, auto_adjust_page_width)

    def update_stored_procedure(self, filepath: str, dataset_name: str, new_sproc: str) -> Dict[str, Any]:
        return datasets.update_stored_procedure(filepath, dataset_name, new_sproc)

    def add_dataset_field(self, filepath: str, dataset_name: str, field_name: str,
                          data_field: str, type_name: str) -> Dict[str, Any]:
        return datasets.add_dataset_field(filepath, dataset_name, field_name, data_field, type_name)

    def remove_dataset_field(self, filepath: str, dataset_name: str, field_name: str) -> Dict[str, Any]:
        return datasets.remove_dataset_field(filepath, dataset_name, field_name)

    def add_parameter(self, filepath: str, name: str, data_type: str, prompt: str) -> Dict[str, Any]:
        return parameters.add_parameter(filepath, name, data_type, prompt)

    def update_parameter(self, filepath: str, name: str, prompt: Optional[str] = None,
                         default_value: Optional[str] = None) -> Dict[str, Any]:
        return parameters.update_parameter(filepath, name, prompt, default_value)

    # Expression parsing methods (exposed for testing)
    def _extract_field_references_with_context(self, expression: str, default_dataset: str) -> Dict[str, Any]:
        return validation.extract_field_references_with_context(expression, default_dataset)

    def _extract_field_references(self, expression: str):
        return validation.extract_field_references(expression)


def run_server():
    """Run the MCP server."""
    server = MCPServer()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = server.handle_request(request)
            if response:
                print(json.dumps(response))
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            print(json.dumps({
                'jsonrpc': '2.0',
                'id': None,
                'error': {'code': -32700, 'message': 'Parse error'}
            }))
            sys.stdout.flush()
