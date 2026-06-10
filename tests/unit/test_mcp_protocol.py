"""
Unit tests for MCP protocol handling in MarkItDown MCP Server
"""

import io
import json
from unittest.mock import patch

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest, MCPResponse
from tests.helpers.assertions import (
    assert_mcp_error_response,
    assert_mcp_success_response,
    assert_valid_json_rpc_response,
)


class TestMCPRequestResponse:
    """Test MCP request and response data structures."""

    @pytest.mark.unit
    def test_mcp_request_creation(self):
        """Test MCPRequest creation with valid data."""
        request = MCPRequest(id="test-1", method="initialize", params={"key": "value"})

        assert request.id == "test-1"
        assert request.method == "initialize"
        assert request.params == {"key": "value"}

    @pytest.mark.unit
    def test_mcp_response_success_creation(self):
        """Test MCPResponse creation for success case."""
        response = MCPResponse(id="test-1", result={"status": "ok"})

        assert response.id == "test-1"
        assert response.result == {"status": "ok"}
        assert response.error is None

    @pytest.mark.unit
    def test_mcp_response_error_creation(self):
        """Test MCPResponse creation for error case."""
        response = MCPResponse(id="test-1", error={"code": -32601, "message": "Method not found"})

        assert response.id == "test-1"
        assert response.error == {"code": -32601, "message": "Method not found"}
        assert response.result is None


class TestMCPServerInitialization:
    """Test MCP server initialization and basic functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_server_creation(self):
        """Test that MCP server can be created."""
        server = MarkItDownMCPServer()
        assert server is not None
        assert hasattr(server, "markitdown")
        assert hasattr(server, "supported_extensions")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_initialize_method(self, mcp_server, mcp_initialize_request):
        """Test the initialize method."""
        response = await mcp_server.handle_request(mcp_initialize_request)

        assert_mcp_success_response(response, "init-test")

        result = response.result
        assert "protocolVersion" in result
        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "markitdown-server"
        assert result["serverInfo"]["version"] == "1.0.0"


class TestToolsListMethod:
    """Test the tools/list MCP method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tools_list_method(self, mcp_server, mcp_tools_list_request):
        """Test the tools/list method returns correct tools."""
        response = await mcp_server.handle_request(mcp_tools_list_request)

        assert_mcp_success_response(response, "tools-test")

        result = response.result
        assert "tools" in result
        tools = result["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 3  # Should have 3 tools

        # Check tool names
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["convert_file", "list_supported_formats", "convert_directory"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

        # Validate tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert isinstance(tool["inputSchema"], dict)
            assert "type" in tool["inputSchema"]
            assert tool["inputSchema"]["type"] == "object"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_file_schema_avoids_top_level_composition(self, mcp_server):
        """Anthropic MCP clients reject anyOf/oneOf/allOf at the inputSchema top level."""
        response = await mcp_server.handle_request(MCPRequest(id="tools-test", method="tools/list", params={}))

        convert_file_tool = next(
            tool for tool in response.result["tools"] if tool["name"] == "convert_file"
        )

        assert "anyOf" not in convert_file_tool["inputSchema"]
        assert "oneOf" not in convert_file_tool["inputSchema"]
        assert "allOf" not in convert_file_tool["inputSchema"]


class TestUnknownMethods:
    """Test handling of unknown MCP methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_method(self, mcp_server):
        """Test that unknown methods return proper error."""
        request = MCPRequest(id="unknown-test", method="unknown/method", params={})

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32601, "unknown-test")
        assert "unknown method" in response.error["message"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_method(self, mcp_server):
        """Test request with missing method field."""
        # This would typically be handled by request validation
        request = MCPRequest(id="missing-method-test", method=None, params={})

        response = await mcp_server.handle_request(request)

        # Should return an error
        assert response.error is not None


class TestRequestValidation:
    """Test MCP request validation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_request_id(self, mcp_server):
        """Test request with missing ID."""
        request = MCPRequest(id=None, method="initialize", params={})

        # Server should handle this gracefully
        response = await mcp_server.handle_request(request)
        assert response is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_params(self, mcp_server):
        """Test request with empty params."""
        request = MCPRequest(id="empty-params-test", method="initialize", params={})

        response = await mcp_server.handle_request(request)
        assert_mcp_success_response(response, "empty-params-test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_none_params(self, mcp_server):
        """Test request with None params."""
        request = MCPRequest(id="none-params-test", method="initialize", params=None)

        # Server should handle this gracefully
        response = await mcp_server.handle_request(request)
        assert response is not None


class TestErrorHandling:
    """Test MCP protocol error handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_internal_error_handling(self, mcp_server):
        """Test that internal errors are properly wrapped."""
        # Mock the markitdown instance to raise an exception
        with patch.object(mcp_server, "convert_file_tool") as mock_convert:
            mock_convert.side_effect = Exception("Internal error")

            request = MCPRequest(
                id="error-test",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": "/test/path"}},
            )

            response = await mcp_server.handle_request(request)

            assert_mcp_error_response(response, -32603, "error-test")
            assert "internal error" in response.error["message"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_not_found_error(self, mcp_server):
        """Test error when calling non-existent tool."""
        request = MCPRequest(
            id="tool-not-found-test",
            method="tools/call",
            params={"name": "nonexistent_tool", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32601, "tool-not-found-test")
        assert "unknown tool" in response.error["message"].lower()


class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 protocol compliance."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_response_structure_compliance(self, mcp_server):
        """Test that responses comply with JSON-RPC 2.0 structure."""
        request = MCPRequest(id="compliance-test", method="initialize", params={})

        response = await mcp_server.handle_request(request)

        # Convert to JSON and back to simulate real usage
        response_dict = {"jsonrpc": "2.0", "id": response.id}

        if response.result is not None:
            response_dict["result"] = response.result
        if response.error is not None:
            response_dict["error"] = response.error

        # Should be valid JSON-RPC 2.0
        json_str = json.dumps(response_dict)
        parsed = assert_valid_json_rpc_response(json_str)

        assert parsed["id"] == "compliance-test"
        assert "result" in parsed

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_server_does_not_reply_to_notifications(self, monkeypatch):
        """JSON-RPC notifications do not have an id and must not receive responses."""
        server = MarkItDownMCPServer()
        stdin = io.StringIO(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                }
            )
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            + "\n"
        )
        stdout = io.StringIO()
        monkeypatch.setattr("sys.stdin", stdin)
        monkeypatch.setattr("sys.stdout", stdout)

        await server.run()

        responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
        assert len(responses) == 1
        assert responses[0]["id"] == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_code_compliance(self, mcp_server):
        """Test that error codes follow JSON-RPC 2.0 standards."""
        # Test various error scenarios
        test_cases = [
            {
                "request": MCPRequest(id="method-not-found", method="invalid/method", params={}),
                "expected_code": -32601,  # Method not found
            },
            {
                "request": MCPRequest(
                    id="invalid-params", method="tools/call", params={"invalid": "structure"}
                ),
                "expected_code": -32602,  # Invalid params
            },
        ]

        for test_case in test_cases:
            response = await mcp_server.handle_request(test_case["request"])
            assert_mcp_error_response(response, test_case["expected_code"])


class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_initialize_requests(self, mcp_server):
        """Test multiple concurrent initialize requests."""
        import asyncio

        requests = [
            MCPRequest(id=f"concurrent-{i}", method="initialize", params={}) for i in range(5)
        ]

        # Send all requests concurrently
        responses = await asyncio.gather(*[mcp_server.handle_request(req) for req in requests])

        # All should succeed
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"concurrent-{i}")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_tools_list_requests(self, mcp_server):
        """Test multiple concurrent tools/list requests."""
        import asyncio

        requests = [
            MCPRequest(id=f"tools-concurrent-{i}", method="tools/list", params={}) for i in range(3)
        ]

        responses = await asyncio.gather(*[mcp_server.handle_request(req) for req in requests])

        # All should succeed with same result
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"tools-concurrent-{i}")
            assert len(response.result["tools"]) == 3


class TestRequestResponseIntegrity:
    """Test request-response integrity and matching."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_id_preservation(self, mcp_server):
        """Test that request IDs are preserved in responses."""
        test_ids = ["test-123", "uuid-abc-def", "42", "special@id#123"]

        for test_id in test_ids:
            request = MCPRequest(id=test_id, method="initialize", params={})

            response = await mcp_server.handle_request(request)
            assert response.id == test_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_response_consistency(self, mcp_server):
        """Test that identical requests produce identical responses."""
        request = MCPRequest(id="consistency-test", method="tools/list", params={})

        # Send same request multiple times
        response1 = await mcp_server.handle_request(request)
        response2 = await mcp_server.handle_request(request)

        # Results should be identical (excluding ID which may be used)
        assert response1.result == response2.result
        assert response1.error == response2.error
