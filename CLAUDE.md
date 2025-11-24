# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RDL MCP Server is a Model Context Protocol (MCP) server that enables AI assistants to read and modify SSRS (SQL Server Reporting Services) RDL files. It provides simple JSON-based tools instead of requiring direct XML manipulation of complex RDL structures.

## Build and Test Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_rdl_mcp_server.py -v

# Run a specific test class
python3 -m pytest tests/test_rdl_mcp_server.py::TestColumnOperations -v

# Run a specific test
python3 -m pytest tests/test_rdl_mcp_server.py::TestColumnOperations::test_update_column_header -v

# Run the server directly (for testing)
python3 rdl_mcp_server.py

# Install with uv (preferred)
uvx rdl-mcp
```

## Architecture

The codebase follows a modular design with the main MCP server delegating to specialized modules:

- **`rdl_mcp_server.py`** - Entry point with logging setup, imports `MCPServer` from package
- **`rdl_mcp/server.py`** - Core `MCPServer` class handling JSON-RPC protocol, tool registration, and request routing
- **`rdl_mcp/reader.py`** - Read-only operations: `describe_rdl_report`, `get_rdl_datasets`, `get_rdl_parameters`, `get_rdl_columns`
- **`rdl_mcp/columns.py`** - Column modifications: add/remove/update header/width/format
- **`rdl_mcp/datasets.py`** - Dataset operations: add/remove fields, update stored procedures
- **`rdl_mcp/parameters.py`** - Parameter operations: add/update report parameters
- **`rdl_mcp/validation.py`** - RDL validation and field reference extraction
- **`rdl_mcp/xml_utils.py`** - Shared XML parsing utilities and namespace handling

## Key Constraints

- **Python standard library only** - No external dependencies beyond pytest for testing
- **Python 3.8+ compatibility** required
- **Tablix controls only** - Currently supports table-based reports, not Matrix or Chart controls
- **RDL 2016 namespace** - Uses `http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition`

## MCP Protocol

The server uses JSON-RPC 2.0 over stdin/stdout. Key methods:
- `initialize` - Returns server capabilities
- `tools/list` - Returns available tools with JSON schemas
- `tools/call` - Executes a tool with arguments

## Testing

Tests use pytest with fixtures that create temporary RDL files. The `_create_sample_report()` function in tests generates valid minimal RDL documents for testing.

**Requirements:**
- Write tests before implementing any changes
- All tests must pass after making changes (`python3 -m pytest tests/ -v`)

## Logging

Configure via environment variables:
- `RDL_MCP_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `RDL_MCP_LOG_FILE`: Path to log file
