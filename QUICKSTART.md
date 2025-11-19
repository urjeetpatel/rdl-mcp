# Quick Start Guide - RDL MCP Server

## 5-Minute Setup for Claude Desktop

### Step 1: Save the Server File

Create a directory and save the server:
```bash
mkdir -p ~/mcp-servers
# Copy rdl_mcp_server.py to ~/mcp-servers/
```

### Step 2: Make it Executable

```bash
chmod +x ~/mcp-servers/rdl_mcp_server.py
```

### Step 3: Configure Claude Desktop

**On macOS:**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**On Windows:**
```bash
notepad %APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration:
```json
{
  "mcpServers": {
    "rdl-editor": {
      "command": "python3",
      "args": ["<FULL_PATH_TO>/rdl_mcp_server.py"]
    }
  }
}
```

Replace `<FULL_PATH_TO>` with your actual path (e.g., `/Users/yourname/mcp-servers/rdl_mcp_server.py`)

### Step 4: Restart Claude Desktop

Quit and reopen Claude Desktop to load the new server.

### Step 5: Test It!

Open a chat with Claude and try:

```
I have an RDL report at /path/to/report.rdl. 
Can you tell me what datasets it uses?
```

Claude will use the `describe_rdl_report` and `get_rdl_datasets` tools automatically!

## Verification

Check if the server is loaded:

1. In Claude Desktop, you should see an indicator showing MCP servers are active
2. Try asking Claude: "What RDL tools do you have available?"
3. Claude should list the 10 RDL editing tools

## Common Issues

### "python3: command not found"
- Use `python` instead of `python3` in the config
- Or install Python 3.8+

### "Permission denied"
- Make sure the file is executable: `chmod +x rdl_mcp_server.py`

### Server not loading
- Check the path in the config is absolute (no ~, use full path)
- Look at Claude Desktop logs for errors

### Tools not appearing
- Restart Claude Desktop after config changes
- Verify JSON syntax in config file

## Example Conversation

**You**: "I need to update my Transaction Details report. The stored procedure changed to V2."

**Claude**: 
1. Calls `describe_rdl_report()` to understand the report
2. Calls `get_rdl_datasets()` to find the current stored procedure
3. Calls `update_stored_procedure()` to change it
4. Calls `validate_rdl()` to ensure it's still valid
5. Reports back: "I've updated Report_Data to use Report.001_Get_TransactionDetails_V2"

## Next Steps

- See README.md for complete documentation
- Run demo_rdl_server.py to see all capabilities
- Check test_rdl_server.py for testing examples

## Tips for Best Results

1. **Always provide file paths**: Tell Claude the exact path to your RDL file
2. **Be specific**: "Change the Account Number column width to 2 inches" is clearer than "make it wider"
3. **Ask for validation**: Request Claude validate after changes
4. **Iterate**: Start with simple changes, then ask for more complex modifications

## Alternative: Continue.dev Setup

For Continue.dev in VS Code:

1. Open `.continue/config.json`
2. Add:
```json
{
  "mcpServers": {
    "rdl-editor": {
      "command": "python3",
      "args": ["/full/path/to/rdl_mcp_server.py"]
    }
  }
}
```
3. Reload VS Code

## Alternative: Standalone Usage

You can also use the tools directly without MCP:

```python
from rdl_mcp_server import MCPServer

server = MCPServer()
result = server.describe_rdl_report(filepath="report.rdl")
print(result)
```

This is useful for:
- Testing
- Scripting
- Integration into your own tools
