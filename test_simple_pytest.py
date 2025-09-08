#!/usr/bin/env python3
"""Simple pytest test to verify MCP server functionality."""

import pytest
import tempfile
from pathlib import Path

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that MCP server can be created and initialized."""
    server = MarkItDownMCPServer()
    assert server is not None
    
    # Test initialize
    request = MCPRequest(id="test-init", method="initialize", params={})
    response = await server.handle_request(request)
    
    assert response.result is not None
    assert response.error is None
    assert response.result["serverInfo"]["name"] == "markitdown-server"


@pytest.mark.asyncio
async def test_tools_list():
    """Test tools list functionality."""
    server = MarkItDownMCPServer()
    
    request = MCPRequest(id="test-tools", method="tools/list", params={})
    response = await server.handle_request(request)
    
    assert response.result is not None
    assert response.error is None
    assert len(response.result["tools"]) == 3
    
    tool_names = {tool["name"] for tool in response.result["tools"]}
    expected_tools = {"convert_file", "list_supported_formats", "convert_directory"}
    assert tool_names == expected_tools


@pytest.mark.asyncio
async def test_file_conversion():
    """Test basic file conversion functionality."""
    server = MarkItDownMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, MarkItDown MCP!")
        
        request = MCPRequest(
            id="test-convert",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": str(test_file)}
            }
        )
        
        response = await server.handle_request(request)
        
        assert response.result is not None
        assert response.error is None
        assert "content" in response.result
        assert len(response.result["content"]) > 0
        
        content = response.result["content"][0]["text"]
        assert "Hello, MarkItDown MCP!" in content


@pytest.mark.asyncio
async def test_supported_formats():
    """Test supported formats listing."""
    server = MarkItDownMCPServer()
    
    request = MCPRequest(
        id="test-formats",
        method="tools/call",
        params={
            "name": "list_supported_formats",
            "arguments": {}
        }
    )
    
    response = await server.handle_request(request)
    
    assert response.result is not None
    assert response.error is None
    
    content = response.result["content"][0]["text"]
    # Should contain common formats
    assert ".txt" in content
    assert ".json" in content
    assert ".csv" in content
    assert ".pdf" in content