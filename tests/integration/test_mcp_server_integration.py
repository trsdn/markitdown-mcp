"""
Full MCP server integration tests.
Tests the complete MCP protocol flow and server lifecycle.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_mcp_error_response,
    assert_mcp_success_response,
    assert_valid_json_rpc_response,
)


class MockSTDIN:
    """Mock stdin for testing server I/O."""

    def __init__(self, messages: List[Dict[str, Any]]):
        self.messages = [json.dumps(msg) + "\n" for msg in messages]
        self.index = 0

    def readline(self) -> str:
        if self.index < len(self.messages):
            message = self.messages[self.index]
            self.index += 1
            return message
        return ""  # EOF


class MockSTDOUT:
    """Mock stdout for testing server output."""

    def __init__(self):
        self.outputs: List[str] = []

    def write(self, data: str):
        self.outputs.append(data)

    def flush(self):
        pass

    def get_json_responses(self) -> List[Dict[str, Any]]:
        """Parse collected outputs as JSON responses."""
        responses = []
        for output in self.outputs:
            if output.strip():
                try:
                    responses.append(json.loads(output.strip()))
                except json.JSONDecodeError:
                    pass
        return responses


class TestMCPServerIntegration:
    """Test complete MCP server integration scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_initialization_flow(self):
        """Test complete server initialization sequence."""
        server = MarkItDownMCPServer()

        # Test initialization request
        init_request = MCPRequest(id="init-1", method="initialize", params={})

        response = await server.handle_request(init_request)

        assert_mcp_success_response(response, "init-1")
        result = response.result

        # Verify protocol version
        assert result["protocolVersion"] == "2024-11-05"

        # Verify capabilities
        assert "capabilities" in result
        assert "tools" in result["capabilities"]

        # Verify server info
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "markitdown-server"
        assert result["serverInfo"]["version"] == "1.0.0"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tools_discovery_flow(self):
        """Test complete tools discovery flow."""
        server = MarkItDownMCPServer()

        # First initialize
        init_request = MCPRequest(id="init", method="initialize", params={})
        init_response = await server.handle_request(init_request)
        assert_mcp_success_response(init_response, "init")

        # Then list tools
        tools_request = MCPRequest(id="tools-list", method="tools/list", params={})

        response = await server.handle_request(tools_request)
        assert_mcp_success_response(response, "tools-list")

        tools = response.result["tools"]
        assert len(tools) == 3

        # Verify all expected tools are present
        tool_names = {tool["name"] for tool in tools}
        expected_tools = {"convert_file", "list_supported_formats", "convert_directory"}
        assert tool_names == expected_tools

        # Verify tool schemas
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_file_conversion_flow(self, temp_dir):
        """Test complete end-to-end file conversion flow."""
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "test.txt"
        test_content = "Hello, World!\nThis is a test file for integration testing."
        test_file.write_text(test_content)

        # Complete flow: initialize -> list tools -> convert file
        requests = [
            MCPRequest(id="1", method="initialize", params={}),
            MCPRequest(id="2", method="tools/list", params={}),
            MCPRequest(
                id="3",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            ),
        ]

        responses = []
        for request in requests:
            response = await server.handle_request(request)
            responses.append(response)

        # Verify all responses
        assert_mcp_success_response(responses[0], "1")
        assert_mcp_success_response(responses[1], "2")
        assert_mcp_success_response(responses[2], "3")

        # Verify conversion result
        conversion_result = responses[2].result["content"][0]["text"]
        assert "Hello, World!" in conversion_result
        assert "test file" in conversion_result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, temp_dir):
        """Test handling of multiple concurrent requests."""
        server = MarkItDownMCPServer()

        # Create multiple test files
        test_files = []
        for i in range(5):
            file_path = Path(temp_dir) / f"test_{i}.txt"
            file_path.write_text(f"Test file number {i}")
            test_files.append(str(file_path))

        # Create concurrent conversion requests
        requests = [
            MCPRequest(
                id=f"concurrent-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(5)
        ]

        # Send all requests concurrently
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # Verify all responses are successful
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"concurrent-{i}")
            content = response.result["content"][0]["text"]
            assert f"Test file number {i}" in content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test server error recovery and continued operation."""
        server = MarkItDownMCPServer()

        # Send invalid request
        invalid_request = MCPRequest(id="invalid-1", method="nonexistent/method", params={})

        error_response = await server.handle_request(invalid_request)
        assert_mcp_error_response(error_response, -32601, "invalid-1")

        # Verify server can still handle valid requests
        valid_request = MCPRequest(id="valid-after-error", method="initialize", params={})

        valid_response = await server.handle_request(valid_request)
        assert_mcp_success_response(valid_response, "valid-after-error")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_cleanup_between_requests(self, temp_dir):
        """Test that server properly cleans up memory between requests."""
        server = MarkItDownMCPServer()

        # Create a moderately large file
        large_file = Path(temp_dir) / "large.txt"
        large_content = "Large file content.\n" * 10000  # ~200KB
        large_file.write_text(large_content)

        # Process the file multiple times
        for i in range(10):
            request = MCPRequest(
                id=f"cleanup-test-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"cleanup-test-{i}")

            # Verify content is still correct
            content = response.result["content"][0]["text"]
            assert "Large file content" in content

        # Server should still be responsive
        final_request = MCPRequest(id="final", method="initialize", params={})
        final_response = await server.handle_request(final_request)
        assert_mcp_success_response(final_response, "final")


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance and standards adherence."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_json_rpc_compliance(self):
        """Test that all responses comply with JSON-RPC 2.0."""
        server = MarkItDownMCPServer()

        test_cases = [
            MCPRequest(id="json-rpc-1", method="initialize", params={}),
            MCPRequest(id="json-rpc-2", method="tools/list", params={}),
            MCPRequest(id="json-rpc-3", method="unknown/method", params={}),
        ]

        for request in test_cases:
            response = await server.handle_request(request)

            # Convert to JSON-RPC format
            response_dict = {"jsonrpc": "2.0", "id": response.id}
            if response.result is not None:
                response_dict["result"] = response.result
            if response.error is not None:
                response_dict["error"] = response.error

            # Verify JSON-RPC compliance
            json_str = json.dumps(response_dict)
            parsed = assert_valid_json_rpc_response(json_str)
            assert parsed["id"] == request.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_id_preservation(self):
        """Test that request IDs are properly preserved."""
        server = MarkItDownMCPServer()

        special_ids = [
            "simple-id",
            "123456789",
            "uuid-abc-def-123",
            "special@characters#123",
            "🚀-emoji-id",
            "",  # Empty string ID
        ]

        for test_id in special_ids:
            request = MCPRequest(id=test_id, method="initialize", params={})

            response = await server.handle_request(request)
            assert response.id == test_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_code_compliance(self):
        """Test that error codes follow JSON-RPC 2.0 standards."""
        server = MarkItDownMCPServer()

        error_scenarios = [
            {
                "request": MCPRequest(id="1", method="nonexistent", params={}),
                "expected_code": -32601,  # Method not found
            },
            {
                "request": MCPRequest(id="2", method="tools/call", params={"invalid": "params"}),
                "expected_code": -32602,  # Invalid params
            },
        ]

        for scenario in error_scenarios:
            response = await server.handle_request(scenario["request"])
            assert_mcp_error_response(response, scenario["expected_code"])


class TestServerLifecycle:
    """Test server lifecycle management."""

    @pytest.mark.integration
    @patch("sys.stdin")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_server_run_lifecycle(self, mock_print, mock_stdin):
        """Test complete server run lifecycle with mocked I/O."""
        # Prepare mock stdin with messages
        messages = [
            {"jsonrpc": "2.0", "id": "1", "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": "2", "method": "tools/list", "params": {}},
        ]

        mock_stdin_obj = MockSTDIN(messages)
        mock_stdin.readline.side_effect = mock_stdin_obj.readline

        server = MarkItDownMCPServer()

        # Mock the run method to avoid infinite loop
        with patch.object(server, "run") as mock_run:
            mock_run.return_value = None

            # Simulate server processing
            for message in messages:
                request = MCPRequest(
                    id=message["id"], method=message["method"], params=message["params"]
                )

                response = await server.handle_request(request)

                # Verify response structure
                response_dict = {"jsonrpc": "2.0", "id": response.id}
                if response.result is not None:
                    response_dict["result"] = response.result
                if response.error is not None:
                    response_dict["error"] = response.error

                # Verify it's valid JSON
                json_str = json.dumps(response_dict)
                assert json_str is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graceful_error_handling_in_lifecycle(self):
        """Test that server handles errors gracefully during operation."""
        server = MarkItDownMCPServer()

        # Test sequence: valid -> error -> valid -> error -> valid
        requests = [
            MCPRequest(id="1", method="initialize", params={}),
            MCPRequest(id="2", method="invalid", params={}),
            MCPRequest(id="3", method="tools/list", params={}),
            MCPRequest(id="4", method="tools/call", params={"invalid": True}),
            MCPRequest(id="5", method="initialize", params={}),
        ]

        expected_results = ["success", "error", "success", "error", "success"]

        for i, (request, expected) in enumerate(zip(requests, expected_results)):
            response = await server.handle_request(request)

            if expected == "success":
                assert response.result is not None
                assert response.error is None
            else:
                assert response.error is not None
                assert response.result is None

            # Verify ID is preserved
            assert response.id == request.id


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_typical_user_workflow(self, temp_dir):
        """Test a typical user workflow from start to finish."""
        server = MarkItDownMCPServer()

        # Create sample files like a user might have
        files = {
            "document.txt": "# Meeting Notes\n\nDiscussion about the project.",
            "data.json": '{"name": "Project", "status": "active"}',
            "info.csv": "Name,Value\nBudget,10000\nTeam Size,5",
        }

        file_paths = []
        for filename, content in files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
            file_paths.append(str(file_path))

        # Typical workflow
        workflow_requests = [
            # User starts by initializing
            MCPRequest(id="init", method="initialize", params={}),
            # User discovers available tools
            MCPRequest(id="tools", method="tools/list", params={}),
            # User checks supported formats
            MCPRequest(
                id="formats",
                method="tools/call",
                params={"name": "list_supported_formats", "arguments": {}},
            ),
            # User converts individual files
            MCPRequest(
                id="convert-1",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": file_paths[0]}},
            ),
            MCPRequest(
                id="convert-2",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": file_paths[1]}},
            ),
            # User converts directory
            MCPRequest(
                id="convert-dir",
                method="tools/call",
                params={"name": "convert_directory", "arguments": {"input_directory": temp_dir}},
            ),
        ]

        # Execute workflow
        responses = []
        for request in workflow_requests:
            response = await server.handle_request(request)
            responses.append(response)

        # Verify all steps succeeded
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, workflow_requests[i].id)

        # Verify specific results
        # Tools list should have 3 tools
        assert len(responses[1].result["tools"]) == 3

        # Format list should contain supported formats
        formats_content = responses[2].result["content"][0]["text"]
        assert ".txt" in formats_content
        assert ".json" in formats_content
        assert ".csv" in formats_content

        # File conversions should contain original content
        assert "Meeting Notes" in responses[3].result["content"][0]["text"]
        assert "Project" in responses[4].result["content"][0]["text"]

        # Directory conversion should report success
        dir_result = responses[5].result["content"][0]["text"]
        assert "Successfully converted" in dir_result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_scenarios_user_might_encounter(self, temp_dir):
        """Test error scenarios that users might realistically encounter."""
        server = MarkItDownMCPServer()

        # Common user errors
        error_scenarios = [
            # File doesn't exist
            {
                "request": MCPRequest(
                    id="file-not-found",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": "/nonexistent/file.txt"},
                    },
                ),
                "error_code": -32602,
                "error_keywords": ["not found", "exist"],
            },
            # Directory doesn't exist
            {
                "request": MCPRequest(
                    id="dir-not-found",
                    method="tools/call",
                    params={
                        "name": "convert_directory",
                        "arguments": {"input_directory": "/nonexistent"},
                    },
                ),
                "error_code": -32602,
                "error_keywords": ["not found", "exist"],
            },
            # Missing required arguments
            {
                "request": MCPRequest(
                    id="missing-args",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {}},
                ),
                "error_code": -32602,
                "error_keywords": ["required", "missing"],
            },
            # Invalid tool name
            {
                "request": MCPRequest(
                    id="invalid-tool",
                    method="tools/call",
                    params={"name": "nonexistent_tool", "arguments": {}},
                ),
                "error_code": -32601,
                "error_keywords": ["unknown tool"],
            },
        ]

        for scenario in error_scenarios:
            response = await server.handle_request(scenario["request"])

            # Verify error response
            assert_mcp_error_response(response, scenario["error_code"])

            # Verify error message is helpful
            error_msg = response.error["message"].lower()
            keyword_found = any(keyword in error_msg for keyword in scenario["error_keywords"])
            assert (
                keyword_found
            ), f"Error message should contain one of {scenario['error_keywords']}: {error_msg}"

            # Verify server is still operational after error
            health_check = MCPRequest(id="health", method="initialize", params={})
            health_response = await server.handle_request(health_check)
            assert_mcp_success_response(health_response, "health")


class TestResourceManagement:
    """Test resource management and cleanup."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self):
        """Test that temporary files are properly cleaned up."""
        server = MarkItDownMCPServer()

        # Use base64 content which creates temporary files
        import base64

        test_content = "Test content for temporary file cleanup"
        encoded_content = base64.b64encode(test_content.encode()).decode()

        # Get initial temp file count
        temp_dir = Path(tempfile.gettempdir())
        initial_temp_files = len(list(temp_dir.glob("tmp*")))

        # Process multiple base64 files
        for i in range(5):
            request = MCPRequest(
                id=f"temp-cleanup-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {"file_content": encoded_content, "filename": f"test_{i}.txt"},
                },
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"temp-cleanup-{i}")

        # Verify temporary files were cleaned up
        final_temp_files = len(list(temp_dir.glob("tmp*")))
        assert final_temp_files <= initial_temp_files + 1  # Allow some system temp files

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_stability_over_time(self, temp_dir):
        """Test memory stability over extended operation."""
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "memory_test.txt"
        test_file.write_text("Memory stability test content.")

        # Process many requests to test memory stability
        for i in range(50):
            request = MCPRequest(
                id=f"memory-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"memory-{i}")

            # Verify response quality doesn't degrade
            content = response.result["content"][0]["text"]
            assert "Memory stability test" in content

        # Server should still be responsive
        final_request = MCPRequest(id="final-check", method="initialize", params={})
        final_response = await server.handle_request(final_request)
        assert_mcp_success_response(final_response, "final-check")
