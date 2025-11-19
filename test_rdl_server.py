#!/usr/bin/env python3
"""
Test script for RDL MCP Server
Demonstrates the functionality without needing full MCP protocol setup
"""

import sys
sys.path.insert(0, '/home/claude')

from rdl_mcp_server import MCPServer
import json

def test_rdl_tools():
    """Test the RDL tools with the uploaded file"""
    server = MCPServer()
    filepath = "/mnt/user-data/uploads/001_-_Transaction_Details.rdl"
    
    print("=" * 80)
    print("RDL MCP Server - Test Results")
    print("=" * 80)
    print()
    
    # Test 1: Describe Report
    print("1. DESCRIBE REPORT")
    print("-" * 80)
    result = server.describe_rdl_report(filepath=filepath)
    print(json.dumps(result, indent=2))
    print()
    
    # Test 2: Get Datasets
    print("2. GET DATASETS")
    print("-" * 80)
    result = server.get_rdl_datasets(filepath=filepath)
    print(json.dumps(result, indent=2))
    print()
    
    # Test 3: Get Parameters
    print("3. GET PARAMETERS")
    print("-" * 80)
    result = server.get_rdl_parameters(filepath=filepath)
    print(json.dumps(result, indent=2))
    print()
    
    # Test 4: Get Columns
    print("4. GET COLUMNS")
    print("-" * 80)
    result = server.get_rdl_columns(filepath=filepath)
    print(json.dumps(result, indent=2))
    print()
    
    # Test 5: Validate RDL
    print("5. VALIDATE RDL")
    print("-" * 80)
    result = server.validate_rdl(filepath=filepath)
    print(json.dumps(result, indent=2))
    print()

if __name__ == "__main__":
    test_rdl_tools()
