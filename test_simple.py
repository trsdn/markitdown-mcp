#!/usr/bin/env python3
"""Simple test to verify MCP server functionality."""

import asyncio
import tempfile
from pathlib import Path

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest

async def test_basic_functionality():
    """Test basic MCP server functionality."""
    print("Testing MarkItDown MCP Server...")
    
    # Create server
    server = MarkItDownMCPServer()
    print("✓ Server created")
    
    # Test initialize
    init_request = MCPRequest(id="test-1", method="initialize", params={})
    init_response = await server.handle_request(init_request)
    
    if init_response.result:
        print("✓ Initialize successful")
        print(f"  Server: {init_response.result['serverInfo']['name']}")
        print(f"  Version: {init_response.result['serverInfo']['version']}")
    else:
        print(f"✗ Initialize failed: {init_response.error}")
        return False
    
    # Test tools list
    tools_request = MCPRequest(id="test-2", method="tools/list", params={})
    tools_response = await server.handle_request(tools_request)
    
    if tools_response.result:
        print("✓ Tools list successful")
        tools = tools_response.result["tools"]
        print(f"  Found {len(tools)} tools:")
        for tool in tools:
            print(f"    - {tool['name']}")
    else:
        print(f"✗ Tools list failed: {tools_response.error}")
        return False
    
    # Test file conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, MarkItDown MCP!")
        
        convert_request = MCPRequest(
            id="test-3",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": str(test_file)}
            }
        )
        
        convert_response = await server.handle_request(convert_request)
        
        if convert_response.result:
            print("✓ File conversion successful")
            content = convert_response.result["content"][0]["text"]
            print(f"  Content: {content[:50]}{'...' if len(content) > 50 else ''}")
        else:
            print(f"✗ File conversion failed: {convert_response.error}")
            return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    exit(0 if success else 1)