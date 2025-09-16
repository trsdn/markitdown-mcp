"""
MCP Protocol Smoke Tests.

These tests verify that the server correctly implements the MCP protocol
and can communicate with MCP clients without breaking wire protocol compatibility.
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest


class MCPProtocolTester:
    """Test MCP protocol compliance and basic functionality."""

    def __init__(self):
        self.server = MarkItDownMCPServer()

    async def test_initialization(self) -> Dict[str, Any]:
        """Test MCP initialization handshake."""
        request = MCPRequest(
            id="init-test",
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": False},
                    "sampling": {},
                },
                "clientInfo": {"name": "mcp-smoke-test", "version": "1.0.0"},
            },
        )

        response = await self.server.handle_request(request)

        assert response.id == "init-test"
        assert response.result is not None
        assert "protocolVersion" in response.result
        assert "capabilities" in response.result
        assert "serverInfo" in response.result

        return response.result

    async def test_tools_list(self) -> List[Dict[str, Any]]:
        """Test tools/list endpoint."""
        request = MCPRequest(id="tools-list", method="tools/list", params={})

        response = await self.server.handle_request(request)

        assert response.id == "tools-list"
        assert response.result is not None
        assert "tools" in response.result
        assert isinstance(response.result["tools"], list)

        tools = response.result["tools"]
        assert len(tools) > 0, "Server should expose at least one tool"

        # Verify each tool has required MCP schema
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert isinstance(tool["inputSchema"], dict)

        return tools

    async def test_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Test calling a specific tool."""
        request = MCPRequest(
            id=f"tool-call-{tool_name}",
            method="tools/call",
            params={"name": tool_name, "arguments": arguments},
        )

        response = await self.server.handle_request(request)

        assert response.id == f"tool-call-{tool_name}"

        # Tool calls can succeed or fail, but should follow MCP response format
        if response.result:
            assert "content" in response.result
            assert isinstance(response.result["content"], list)
            if response.result["content"]:
                content_item = response.result["content"][0]
                assert "type" in content_item
                assert content_item["type"] in ["text", "image", "resource"]
        elif response.error:
            assert "code" in response.error
            assert "message" in response.error

        return response.result or response.error

    async def test_resources_list(self) -> Optional[List[Dict[str, Any]]]:
        """Test resources/list endpoint (if supported)."""
        request = MCPRequest(id="resources-list", method="resources/list", params={})

        response = await self.server.handle_request(request)

        # Resources are optional in MCP, so this might return an error
        if response.result:
            assert "resources" in response.result
            return response.result["resources"]
        elif response.error:
            # This is acceptable - not all servers implement resources
            return None

    async def test_invalid_method(self) -> Dict[str, Any]:
        """Test handling of invalid methods."""
        request = MCPRequest(id="invalid-method", method="invalid/method", params={})

        response = await self.server.handle_request(request)

        assert response.id == "invalid-method"
        assert response.error is not None
        assert response.error["code"] == -32601  # Method not found
        assert "message" in response.error

        return response.error


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_protocol_smoke_test(self):
        """Comprehensive MCP protocol smoke test."""
        tester = MCPProtocolTester()

        # Test 1: Initialization
        init_result = await tester.test_initialization()
        assert init_result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in init_result
        assert init_result["serverInfo"]["name"] == "markitdown-server"

        # Test 2: Tools discovery
        tools = await tester.test_tools_list()
        assert len(tools) >= 3, "Should have at least 3 tools: convert_file, list_supported_formats, convert_directory"

        tool_names = {tool["name"] for tool in tools}
        expected_tools = {"convert_file", "list_supported_formats", "convert_directory"}
        assert expected_tools.issubset(tool_names), f"Missing required tools: {expected_tools - tool_names}"

        # Test 3: Tool call with list_supported_formats (safest test)
        list_formats_result = await tester.test_tool_call("list_supported_formats", {})
        assert list_formats_result is not None
        if "content" in list_formats_result:
            assert len(list_formats_result["content"]) > 0

        # Test 4: Resources (optional)
        resources = await tester.test_resources_list()
        # Resources are optional, so we just verify the response format if present

        # Test 5: Error handling
        error_result = await tester.test_invalid_method()
        assert error_result["code"] == -32601

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_convert_file_tool_mcp_compliance(self, temp_dir):
        """Test convert_file tool MCP compliance with actual file."""
        tester = MCPProtocolTester()

        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, MCP protocol test!")

        # Test tool call
        result = await tester.test_tool_call("convert_file", {"file_path": str(test_file)})

        # Should return successful response
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"
        assert "Hello, MCP protocol test!" in result["content"][0]["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_convert_directory_tool_mcp_compliance(self, temp_dir):
        """Test convert_directory tool MCP compliance."""
        tester = MCPProtocolTester()

        # Create test directory structure
        source_dir = Path(temp_dir) / "source"
        output_dir = Path(temp_dir) / "output"
        source_dir.mkdir()

        # Create test files
        (source_dir / "file1.txt").write_text("Content 1")
        (source_dir / "file2.txt").write_text("Content 2")

        # Test tool call
        result = await tester.test_tool_call(
            "convert_directory",
            {"input_directory": str(source_dir), "output_directory": str(output_dir)},
        )

        # Should return successful response
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"


class TestMCPWireProtocol:
    """Test MCP wire protocol using subprocess (closer to real client usage)."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_mcp_server_subprocess_communication(self):
        """Test MCP server communication via subprocess (simulates real client)."""
        # Start the MCP server as subprocess
        proc = None
        try:
            proc = subprocess.Popen(
                ["markitdown-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                    "clientInfo": {"name": "subprocess-test", "version": "1.0.0"},
                },
            }

            stdout, stderr = proc.communicate(input=json.dumps(init_request) + "\n", timeout=10)

            assert proc.returncode == 0 or proc.returncode is None
            assert stdout, f"No stdout received. stderr: {stderr}"

            # Parse response
            response = json.loads(stdout.strip())
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert "protocolVersion" in response["result"]

        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
            pytest.fail("MCP server subprocess timed out")
        except Exception as e:
            if proc and proc.poll() is None:
                proc.kill()
            pytest.fail(f"MCP server subprocess communication failed: {e}")
        finally:
            if proc and proc.poll() is None:
                proc.terminate()

    @pytest.mark.integration
    def test_mcp_tools_list_subprocess(self):
        """Test tools/list via subprocess."""
        proc = None
        try:
            proc = subprocess.Popen(
                ["markitdown-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send tools/list request
            tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

            stdout, stderr = proc.communicate(input=json.dumps(tools_request) + "\n", timeout=10)

            if proc.returncode != 0:
                pytest.fail(f"Server failed with return code {proc.returncode}. stderr: {stderr}")

            assert stdout, f"No stdout received. stderr: {stderr}"

            # Parse response
            response = json.loads(stdout.strip())
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 2
            assert "result" in response
            assert "tools" in response["result"]
            assert len(response["result"]["tools"]) >= 3

        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
            pytest.fail("MCP server subprocess timed out during tools/list")
        except Exception as e:
            if proc and proc.poll() is None:
                proc.kill()
            pytest.fail(f"MCP tools/list subprocess test failed: {e}")
        finally:
            if proc and proc.poll() is None:
                proc.terminate()


class TestMCPSchemaValidation:
    """Test MCP schema compliance for tools and responses."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_schema_compliance(self):
        """Test that all tools follow MCP schema requirements."""
        tester = MCPProtocolTester()
        tools = await tester.test_tools_list()

        for tool in tools:
            # Required fields per MCP spec
            assert "name" in tool, f"Tool missing required 'name' field: {tool}"
            assert "description" in tool, f"Tool missing required 'description' field: {tool}"
            assert "inputSchema" in tool, f"Tool missing required 'inputSchema' field: {tool}"

            # Name should be valid identifier
            assert isinstance(tool["name"], str), f"Tool name must be string: {tool['name']}"
            assert len(tool["name"]) > 0, f"Tool name cannot be empty: {tool}"

            # Description should be meaningful
            assert isinstance(tool["description"], str), f"Tool description must be string: {tool['description']}"
            assert len(tool["description"]) > 10, f"Tool description too short: {tool['description']}"

            # Input schema should be valid JSON Schema
            schema = tool["inputSchema"]
            assert isinstance(schema, dict), f"inputSchema must be object: {schema}"
            assert "type" in schema, f"inputSchema missing type: {schema}"

            # If properties exist, they should be properly structured
            if "properties" in schema:
                assert isinstance(schema["properties"], dict), f"properties must be object: {schema['properties']}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_response_schema_compliance(self, temp_dir):
        """Test that tool responses follow MCP content schema."""
        tester = MCPProtocolTester()

        # Test with a simple file conversion
        test_file = Path(temp_dir) / "schema_test.txt"
        test_file.write_text("Schema compliance test content")

        result = await tester.test_tool_call("convert_file", {"file_path": str(test_file)})

        # Verify response structure
        assert "content" in result, "Tool response must include 'content'"
        assert isinstance(result["content"], list), "Content must be array"
        assert len(result["content"]) > 0, "Content array cannot be empty"

        # Verify content item structure
        content_item = result["content"][0]
        assert "type" in content_item, "Content item must have 'type'"
        assert content_item["type"] in ["text", "image", "resource"], f"Invalid content type: {content_item['type']}"

        if content_item["type"] == "text":
            assert "text" in content_item, "Text content must have 'text' field"
            assert isinstance(content_item["text"], str), "Text field must be string"