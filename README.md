# RDL MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

Edit SSRS reports using AI assistants instead of wrestling with 2000+ lines of XML. This [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server gives Claude, Copilot, and other AI tools simple commands to read and modify RDL files.

## What It Does

**Read reports:**
- `describe_rdl_report` - Get report structure overview
- `get_rdl_datasets` - View datasets, fields, and stored procedures
- `get_rdl_parameters` - List all report parameters
- `get_rdl_columns` - See column headers, widths, and bindings

**Modify reports:**
- `update_column_header` / `update_column_width` - Change columns
- `add_column` / `remove_column` - Add or remove columns
- `update_column_format` - Change number/date formatting
- `update_stored_procedure` - Swap stored procedures
- `add_dataset_field` / `remove_dataset_field` - Manage dataset fields
- `add_parameter` / `update_parameter` - Manage parameters
- `validate_rdl` - Validate XML after changes

**Why it's better than editing XML:**
- AI sees clean JSON instead of verbose XML namespaces
- One-line commands instead of error-prone string manipulation
- Automatic validation catches errors before they break reports
- No dependencies - just Python 3.8+ standard library

## Installation

**1. Get the server:**
```bash
git clone https://github.com/yourusername/rdl-mcp.git
cd rdl-mcp
```

**2. Configure your MCP client:**

<details>
<summary><b>Claude Desktop</b></summary>

Edit config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/.config/Claude/claude_desktop_config.json` on Linux):

```json
{
  "mcpServers": {
    "rdl-mcp": {
      "command": "python3",
      "args": ["/absolute/path/to/rdl_mcp_server.py"]
    }
  }
}
```
</details>

<details>
<summary><b>GitHub Copilot (VSCode)</b></summary>

Add to VSCode settings (`.vscode/settings.json` in your workspace or user settings):

```json
{
  "github.copilot.chat.mcp.servers": {
    "rdl-mcp": {
      "command": "python3",
      "args": ["/absolute/path/to/rdl_mcp_server.py"]
    }
  }
}
```

**Note:** MCP support in GitHub Copilot requires VSCode with Copilot Chat extension installed.
</details>

**3. Restart your AI assistant** and try: `"Describe the structure of my report.rdl file"`

**Requirements:** Python 3.8+ (no other dependencies)

<details>
<summary>Optional: Enable debug logging</summary>

Set environment variables:
- `RDL_MCP_LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`
- `RDL_MCP_LOG_FILE`: Path to log file
</details>

## Usage

Just ask your AI assistant in natural language:

- "What datasets does this report use?"
- "Make the Account Number column 2 inches wide"
- "Format the Amount column as currency with 2 decimals"
- "Update the main dataset to use the V2 stored procedure and add the TaxAmount field"
- "Remove the obsolete Status column"
- "Add a Year parameter to filter the report"

The AI assistant will use the appropriate MCP tools automatically.

## Example: Editing vs. XML

**Without MCP** (manually editing XML):
```xml
<!-- Find this in 2000+ lines -->
<TablixCell><CellContents><Textbox><Paragraphs>
  <Paragraph><TextRuns><TextRun>
    <Value>Old Header</Value>
  </TextRun></TextRuns></Paragraph>
</Paragraphs></Textbox></CellContents></TablixCell>
```

**With MCP** (one command):
```python
update_column_header(filepath="report.rdl",
                     old_header="Old Header",
                     new_header="New Header")
```

## API Reference

<details>
<summary>View all available tools</summary>

### Reading Tools

- **`describe_rdl_report(filepath)`** - Report structure summary
- **`get_rdl_datasets(filepath)`** - Datasets with fields and stored procedures
- **`get_rdl_parameters(filepath)`** - All parameters with configurations
- **`get_rdl_columns(filepath)`** - Column headers, widths, bindings

### Editing Tools

- **`update_column_header(filepath, old_header, new_header)`** - Change column text
- **`update_column_width(filepath, column_index, new_width)`** - Modify width (e.g. "2.5in")
- **`update_column_format(filepath, column_index, format_string)`** - Change format (e.g. "#,0.00", "dd/MM/yyyy", "C2")
- **`add_column(filepath, column_index, header_text, field_binding, width?, format_string?)`** - Add column
- **`remove_column(filepath, column_index)`** - Remove column
- **`update_stored_procedure(filepath, dataset_name, new_sproc)`** - Change dataset sproc
- **`add_dataset_field(filepath, dataset_name, field_name, data_field, type_name)`** - Add field to dataset
- **`remove_dataset_field(filepath, dataset_name, field_name)`** - Remove field from dataset
- **`add_parameter(filepath, name, data_type, prompt)`** - Add new parameter
- **`update_parameter(filepath, name, prompt?, default_value?)`** - Update parameter
- **`validate_rdl(filepath)`** - Validate XML structure

All tools return `{success: bool, message?: string, error?: string}` or structured data.

</details>

## Limitations & Roadmap

**Current limitations:**
- Tablix (table) controls only - no Matrix or Chart support yet
- Works best with standard report layouts
- Some complex RDL features may still need manual XML editing

**Planned features:**
- Column reordering, grouping, and sorting configuration
- Expression builder helpers
- Dataset field management

## Troubleshooting

**Server not appearing?**
- Check absolute path in config is correct
- Verify Python 3.8+: `python3 --version`
- Restart your MCP client

**Permission errors?**
- Make script executable: `chmod +x rdl_mcp_server.py`
- Check RDL file read/write permissions



## Contributing

PRs welcome! Priority areas:
- Better column detection for complex layouts
- More editing operations (reordering, grouping, etc.)

Requirements: Python standard library only

1. Fork repo
2. Create feature branch
3. Make changes + tests
4. Submit PR

## License

MIT License - see [LICENSE](LICENSE) file for details.

This means you're free to use, modify, and distribute this software for any purpose, commercial or non-commercial.
