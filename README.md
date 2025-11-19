# RDL MCP Server

A Model Context Protocol (MCP) server that provides high-level tools for reading and modifying Microsoft RDL (Report Definition Language) files used in SQL Server Reporting Services (SSRS).

## Overview

RDL files are verbose XML documents that are difficult to edit manually. This MCP server provides a simplified interface with specific tools for common editing operations, making it much easier for coding assistants (like Claude, Copilot, etc.) to help you modify reports.

## Features

### Reading Tools
- **describe_rdl_report**: Get high-level summary of report structure
- **get_rdl_datasets**: Get detailed dataset information including fields and stored procedures
- **get_rdl_parameters**: Get all report parameters with their configurations
- **get_rdl_columns**: Get table column headers, widths, and field bindings

### Editing Tools
- **update_column_header**: Change column header text
- **update_column_width**: Modify column widths
- **update_stored_procedure**: Change stored procedure names
- **add_parameter**: Add new report parameters
- **update_parameter**: Modify existing parameters

### Validation
- **validate_rdl**: Validate XML structure after modifications

## Installation

### Prerequisites
- Python 3.8+
- No external dependencies (uses only standard library)

### Setup

1. **Save the MCP server file**:
   ```bash
   # Save rdl_mcp_server.py to a location on your system
   mkdir -p ~/mcp-servers
   cp rdl_mcp_server.py ~/mcp-servers/
   chmod +x ~/mcp-servers/rdl_mcp_server.py
   ```

2. **Configure your MCP client** (Claude Desktop, Continue.dev, etc.):

   For **Claude Desktop**, add to your config file:
   
   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "rdl-editor": {
         "command": "python3",
         "args": ["/path/to/your/rdl_mcp_server.py"]
       }
     }
   }
   ```

   For **Continue.dev**, add to `.continue/config.json`:
   ```json
   {
     "mcpServers": {
       "rdl-editor": {
         "command": "python3",
         "args": ["/path/to/your/rdl_mcp_server.py"]
       }
     }
   }
   ```

3. **Restart your coding assistant** to load the new MCP server

## Usage Examples

### Example 1: Understanding Report Structure

**User**: "What datasets does this report use?"

**Assistant workflow**:
```
1. Calls: describe_rdl_report(filepath="report.rdl")
2. Calls: get_rdl_datasets(filepath="report.rdl")
3. Presents dataset information to user
```

### Example 2: Modifying Column Width

**User**: "Make the Account Number column 2 inches wide"

**Assistant workflow**:
```
1. Calls: get_rdl_columns(filepath="report.rdl")
2. Finds "Account Number" column index
3. Calls: update_column_width(filepath="report.rdl", column_index=3, new_width="2in")
4. Calls: validate_rdl(filepath="report.rdl")
5. Confirms changes to user
```

### Example 3: Updating Stored Procedure

**User**: "Update the main dataset to use the V2 stored procedure"

**Assistant workflow**:
```
1. Calls: get_rdl_datasets(filepath="report.rdl")
2. Identifies main dataset name
3. Calls: update_stored_procedure(
     filepath="report.rdl",
     dataset_name="Report_Data", 
     new_sproc="Report.001_Get_TransactionDetails_V2"
   )
4. Calls: validate_rdl(filepath="report.rdl")
5. Confirms update to user
```

### Example 4: Adding New Parameter

**User**: "Add a Year parameter to filter the report"

**Assistant workflow**:
```
1. Calls: add_parameter(
     filepath="report.rdl",
     name="FilterYear",
     data_type="Integer",
     prompt="Select Year"
   )
2. Calls: validate_rdl(filepath="report.rdl")
3. Calls: get_rdl_parameters(filepath="report.rdl") to confirm
4. Shows user the new parameter configuration
```

## Tool Reference

### describe_rdl_report
Get a high-level summary of the report structure.

**Parameters**:
- `filepath` (string, required): Path to the RDL file

**Returns**:
```json
{
  "report_summary": {
    "datasets": 2,
    "parameters": 5,
    "table_columns": 9
  },
  "datasets": [
    {
      "name": "Report_Data",
      "command_type": "StoredProcedure",
      "command": "Report.001_Get_TransactionDetails",
      "field_count": 13
    }
  ]
}
```

### get_rdl_datasets
Get detailed information about all datasets in the report.

**Parameters**:
- `filepath` (string, required): Path to the RDL file

**Returns**: Detailed dataset information including fields, queries, and parameters

### get_rdl_parameters
Get all report parameters with their configurations.

**Parameters**:
- `filepath` (string, required): Path to the RDL file

**Returns**: List of parameters with types, prompts, default values, and valid values

### get_rdl_columns
Get table column information including headers and widths.

**Parameters**:
- `filepath` (string, required): Path to the RDL file

**Returns**: List of columns with indices, headers, widths, and textbox names

### update_column_header
Change a column header text.

**Parameters**:
- `filepath` (string, required): Path to the RDL file
- `old_header` (string, required): Current header text to find
- `new_header` (string, required): New header text

**Returns**: Success status and message

### update_column_width
Modify a column width.

**Parameters**:
- `filepath` (string, required): Path to the RDL file
- `column_index` (integer, required): Zero-based column index
- `new_width` (string, required): New width (e.g., "2.5in", "3cm")

**Returns**: Success status and message

### update_stored_procedure
Change the stored procedure name for a dataset.

**Parameters**:
- `filepath` (string, required): Path to the RDL file
- `dataset_name` (string, required): Name of the dataset to update
- `new_sproc` (string, required): New stored procedure name

**Returns**: Success status and message

### add_parameter
Add a new report parameter.

**Parameters**:
- `filepath` (string, required): Path to the RDL file
- `name` (string, required): Parameter name
- `data_type` (string, required): Data type (String, Integer, DateTime, Boolean)
- `prompt` (string, required): User-facing prompt text

**Returns**: Success status and message

### update_parameter
Update an existing report parameter.

**Parameters**:
- `filepath` (string, required): Path to the RDL file
- `name` (string, required): Parameter name
- `prompt` (string, optional): New prompt text
- `default_value` (string, optional): New default value

**Returns**: Success status and message

### validate_rdl
Validate the RDL XML structure.

**Parameters**:
- `filepath` (string, required): Path to the RDL file

**Returns**: Validation status and any issues found

## Testing

Run the included test scripts to verify functionality:

```bash
# Basic functionality test
python3 test_rdl_server.py

# Comprehensive demo
python3 demo_rdl_server.py
```

## Advantages Over Direct XML Editing

1. **Simplified Interface**: No need to navigate complex XML structures
2. **Type Safety**: Tools validate inputs and provide clear error messages
3. **Abstraction**: Hide XML namespace complexities from the coding assistant
4. **Validation**: Automatic validation after changes
5. **Focused Operations**: Tools designed for specific, common tasks

## How It Helps Coding Assistants

When you ask a coding assistant to modify an RDL file:

**Without MCP Tools**:
- Assistant sees 2000+ lines of verbose XML
- Must manually parse and understand XML namespaces
- Error-prone string manipulation
- Hard to validate changes

**With MCP Tools**:
- Assistant gets clean, structured JSON responses
- Uses high-level operations like "update_column_width"
- Automatic validation
- Clear success/failure feedback

## Extending the Server

To add new tools:

1. Add the tool method to the `MCPServer` class
2. Register it in the `register_tools()` method
3. Add tool description to the `tools/list` handler
4. Test with the test scripts

Example:
```python
def add_new_column(self, filepath: str, column_name: str, 
                   data_type: str, position: int) -> Dict[str, Any]:
    """Add a new column to the report"""
    # Implementation here
    pass
```

## Limitations

- Currently handles Tablix (table) controls only
- Does not support Matrix or Chart controls
- Column detection works best with standard report layouts
- Some complex RDL features may require manual XML editing

## Future Enhancements

Potential additions:
- Support for Matrix and Chart controls
- Column reordering tools
- Grouping and sorting configuration
- Expression builder helpers
- Dataset field addition/removal
- Report deployment tools

## License

MIT License - Feel free to modify and extend for your needs

## Support

For issues or questions:
1. Check the test scripts for usage examples
2. Review the tool reference documentation
3. Examine the source code comments
4. Test with your specific RDL files

## Contributing

Contributions welcome! Focus areas:
- Better column detection algorithms
- Support for more RDL control types
- Additional editing operations
- Improved validation logic
- Performance optimizations
