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
            "add_column": self.add_column,
            "validate_rdl": self.validate_rdl,
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
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
                                "format_string": {"type": "string", "description": "Optional format string (e.g., '#,0.00' for numbers or 'dd/MM/yyyy' for dates)"}
                            },
                            "required": ["filepath", "column_index", "header_text", "field_binding"]
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
            
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**tool_args)
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
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32000,
                            "message": f"Error: {str(e)}"
                        }
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }

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
                   format_string: Optional[str] = None) -> Dict[str, Any]:
        """Add a new column to the report table at specified position"""
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = self._get_namespace(root)

        # Find the Tablix
        tablix = root.find(f'.//{ns}Tablix')
        if tablix is None:
            return {'success': False, 'message': 'No Tablix (table) found in report'}

        # Get current columns
        tablix_body = tablix.find(f'{ns}TablixBody')
        tablix_columns = tablix_body.find(f'{ns}TablixColumns')
        current_column_count = len(tablix_columns.findall(f'{ns}TablixColumn'))

        # Validate and normalize column_index
        if column_index == -1:
            column_index = current_column_count  # Append at end
        elif column_index < 0 or column_index > current_column_count:
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
                header_text, field_binding, format_string, textbox_name_base
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
                          format_string: Optional[str], textbox_name_base: str) -> ET.Element:
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
            # Try to create an aggregate if field_binding contains a field reference
            if 'Fields!' in field_binding:
                # Extract field name and create Sum
                value.text = field_binding.replace('=Fields!', '=Sum(Fields!').replace('.Value', '.Value)')
            else:
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
