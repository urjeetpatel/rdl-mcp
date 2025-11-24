#!/usr/bin/env python3
"""
MCP Server for RDL (Report Definition Language) Report Editing
Provides high-level tools for reading and modifying SSRS/RDL reports

This is a backward-compatible entry point that imports from the rdl_mcp package.
"""

import json
import logging
import os
import sys

# Configure logging
def setup_logging():
    """Configure logging for the RDL MCP Server"""
    log_level = os.environ.get('RDL_MCP_LOG_LEVEL', 'INFO').upper()
    log_file = os.environ.get('RDL_MCP_LOG_FILE')

    logger = logging.getLogger('rdl_mcp_server')
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (stderr to avoid interfering with MCP protocol on stdout)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if log file specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")

    return logger

# Initialize logger
logger = setup_logging()

# Import from package
from rdl_mcp import MCPServer


def main():
    """Main entry point for the MCP server."""
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


if __name__ == '__main__':
    main()
