"""
Claude Desktop integration tests.
Tests MCP server integration with Claude Desktop environment.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_mcp_success_response,
)


class ClaudeDesktopSimulator:
    """Simulates Claude Desktop MCP client interactions."""

    def __init__(self):
        self.server = MarkItDownMCPServer()
        self.initialized = False
        self.available_tools = []

    async def initialize_connection(self) -> Dict[str, Any]:
        """Simulate Claude Desktop initialization sequence."""
        request = MCPRequest(id="claude-init", method="initialize", params={})

        response = await self.server.handle_request(request)

        if response.result:
            self.initialized = True
            return {
                "success": True,
                "server_info": response.result.get("serverInfo", {}),
                "capabilities": response.result.get("capabilities", {}),
                "protocol_version": response.result.get("protocolVersion", "unknown"),
            }
        else:
            return {"success": False, "error": response.error}

    async def discover_tools(self) -> Dict[str, Any]:
        """Simulate Claude Desktop tool discovery."""
        if not self.initialized:
            raise RuntimeError("Must initialize connection first")

        request = MCPRequest(id="claude-tools", method="tools/list", params={})

        response = await self.server.handle_request(request)

        if response.result:
            self.available_tools = response.result.get("tools", [])
            return {
                "success": True,
                "tools": self.available_tools,
                "count": len(self.available_tools),
            }
        else:
            return {"success": False, "error": response.error}

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Claude Desktop tool call."""
        if not self.initialized:
            raise RuntimeError("Must initialize connection first")

        request = MCPRequest(
            id=f"claude-call-{tool_name}",
            method="tools/call",
            params={"name": tool_name, "arguments": arguments},
        )

        response = await self.server.handle_request(request)

        return {
            "success": response.result is not None,
            "result": response.result,
            "error": response.error,
            "tool_name": tool_name,
            "arguments_used": arguments,
        }

    async def simulate_user_workflow(
        self, workflow_steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simulate a complete user workflow in Claude Desktop."""
        results = []

        for step in workflow_steps:
            if step["action"] == "initialize":
                result = await self.initialize_connection()
            elif step["action"] == "discover_tools":
                result = await self.discover_tools()
            elif step["action"] == "call_tool":
                result = await self.call_tool(step["tool_name"], step["arguments"])
            else:
                result = {"success": False, "error": f"Unknown action: {step['action']}"}

            results.append({"step": step, "result": result})

        return results


class TestClaudeDesktopIntegration:
    """Test integration with Claude Desktop patterns."""

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_initialization_sequence(self):
        """Test the typical Claude Desktop initialization sequence."""
        simulator = ClaudeDesktopSimulator()

        # Initialize connection
        init_result = await simulator.initialize_connection()

        assert init_result["success"] is True
        assert init_result["server_info"]["name"] == "markitdown-server"
        assert init_result["server_info"]["version"] == "1.0.0"
        assert init_result["protocol_version"] == "2024-11-05"
        assert "tools" in init_result["capabilities"]

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_tool_discovery_flow(self):
        """Test Claude Desktop tool discovery flow."""
        simulator = ClaudeDesktopSimulator()

        # Initialize first
        init_result = await simulator.initialize_connection()
        assert init_result["success"] is True

        # Discover tools
        discovery_result = await simulator.discover_tools()

        assert discovery_result["success"] is True
        assert discovery_result["count"] == 3

        # Verify expected tools are available
        tool_names = {tool["name"] for tool in discovery_result["tools"]}
        expected_tools = {"convert_file", "list_supported_formats", "convert_directory"}
        assert tool_names == expected_tools

        # Verify tool schemas are Claude-compatible
        for tool in discovery_result["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_typical_user_session(self, temp_dir):
        """Test a typical user session in Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        # Create test file for user
        user_document = Path(temp_dir) / "user_document.txt"
        user_content = """Meeting Notes - Q1 Planning

Attendees:
- Alice Johnson (PM)
- Bob Smith (Engineer)
- Carol Davis (Designer)

Key Discussion Points:
1. Product roadmap review
2. Resource allocation
3. Timeline adjustments

Action Items:
- Alice: Update project timeline by Friday
- Bob: Review technical requirements
- Carol: Prepare UI mockups

Next Meeting: January 15th, 2024
"""
        user_document.write_text(user_content)

        # Simulate typical user workflow
        workflow = [
            {"action": "initialize"},
            {"action": "discover_tools"},
            {"action": "call_tool", "tool_name": "list_supported_formats", "arguments": {}},
            {
                "action": "call_tool",
                "tool_name": "convert_file",
                "arguments": {"file_path": str(user_document)},
            },
        ]

        results = await simulator.simulate_user_workflow(workflow)

        # Verify each step succeeded
        for i, result in enumerate(results):
            assert result["result"]["success"] is True, f"Step {i} failed: {result}"

        # Verify final conversion result
        conversion_result = results[-1]["result"]["result"]
        converted_text = conversion_result["content"][0]["text"]

        assert "Meeting Notes - Q1 Planning" in converted_text
        assert "Alice Johnson" in converted_text
        assert "Action Items" in converted_text
        assert "January 15th, 2024" in converted_text

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_batch_processing_workflow(self, temp_dir):
        """Test batch processing workflow in Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        # Create multiple files for batch processing
        documents_dir = Path(temp_dir) / "user_documents"
        documents_dir.mkdir()

        files = {
            "project_plan.txt": "# Project Plan\n\nPhase 1: Research\nPhase 2: Development\nPhase 3: Testing",
            "meeting_notes.md": "## Weekly Meeting\n\n- Status updates\n- Blockers discussion\n- Next steps",
            "requirements.json": '{"features": ["auth", "dashboard", "reports"], "deadline": "2024-03-01"}',
            "contacts.csv": "Name,Email,Role\nJohn,john@company.com,Manager\nSarah,sarah@company.com,Developer",
        }

        for filename, content in files.items():
            (documents_dir / filename).write_text(content)

        # Simulate batch processing workflow
        workflow = [
            {"action": "initialize"},
            {"action": "discover_tools"},
            {
                "action": "call_tool",
                "tool_name": "convert_directory",
                "arguments": {
                    "input_directory": str(documents_dir),
                    "output_directory": str(temp_dir) + "/converted",
                },
            },
        ]

        results = await simulator.simulate_user_workflow(workflow)

        # Verify workflow succeeded
        for result in results:
            assert result["result"]["success"] is True

        # Verify batch processing result
        batch_result = results[-1]["result"]["result"]
        result_text = batch_result["content"][0]["text"]

        assert "Successfully converted: 4" in result_text
        assert "Failed conversions: 0" in result_text

        # Verify output files were created
        output_dir = Path(temp_dir) / "converted"
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 4

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_error_handling_experience(self):
        """Test error handling from Claude Desktop user perspective."""
        simulator = ClaudeDesktopSimulator()

        # Initialize first
        await simulator.initialize_connection()
        await simulator.discover_tools()

        # Test various error scenarios users might encounter
        error_scenarios = [
            {
                "description": "File not found",
                "tool_name": "convert_file",
                "arguments": {"file_path": "/nonexistent/file.txt"},
                "expected_error_keywords": ["not found", "exist"],
            },
            {
                "description": "Missing required arguments",
                "tool_name": "convert_file",
                "arguments": {},
                "expected_error_keywords": ["required", "missing", "arguments"],
            },
            {
                "description": "Invalid tool name",
                "tool_name": "nonexistent_tool",
                "arguments": {},
                "expected_error_keywords": ["unknown tool", "not found"],
            },
            {
                "description": "Directory not found",
                "tool_name": "convert_directory",
                "arguments": {"input_directory": "/nonexistent/directory"},
                "expected_error_keywords": ["not found", "exist", "directory"],
            },
        ]

        for scenario in error_scenarios:
            result = await simulator.call_tool(scenario["tool_name"], scenario["arguments"])

            # Should fail gracefully
            assert result["success"] is False
            assert result["error"] is not None

            # Error message should be user-friendly
            error_msg = result["error"]["message"].lower()
            keyword_found = any(
                keyword in error_msg for keyword in scenario["expected_error_keywords"]
            )
            assert keyword_found, f"Error message should contain helpful keywords: {error_msg}"

            # Error should not expose system internals
            assert "traceback" not in error_msg
            assert "exception" not in error_msg
            assert "internal" not in error_msg


class TestClaudeDesktopCompatibility:
    """Test compatibility with Claude Desktop expectations."""

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_tool_schema_claude_compatibility(self):
        """Test that tool schemas are compatible with Claude Desktop."""
        server = MarkItDownMCPServer()

        # Get tools list
        request = MCPRequest(id="schema-test", method="tools/list", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "schema-test")
        tools = response.result["tools"]

        # Verify each tool schema is Claude-compatible
        for tool in tools:
            # Required fields
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

            # Schema structure
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema

            # Verify specific tool schemas
            if tool["name"] == "convert_file":
                properties = schema["properties"]
                assert "file_path" in properties
                assert "file_content" in properties
                assert "filename" in properties

                # Claude/Anthropic clients reject top-level anyOf/oneOf/allOf.
                assert "anyOf" not in schema
                assert "oneOf" not in schema
                assert "allOf" not in schema

            elif tool["name"] == "list_supported_formats":
                # Should accept empty arguments
                # May have empty properties for this tool
                pass

            elif tool["name"] == "convert_directory":
                properties = schema["properties"]
                assert "input_directory" in properties
                assert "output_directory" in properties
                assert "required" in schema
                assert "input_directory" in schema["required"]

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_response_format_claude_compatibility(self, temp_dir):
        """Test that responses are formatted for Claude Desktop consumption."""
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "claude_test.txt"
        test_file.write_text("Test content for Claude Desktop compatibility")

        # Test convert_file response format
        request = MCPRequest(
            id="claude-response-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "claude-response-test")

        # Verify response structure is Claude-compatible
        result = response.result
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0

        content_item = result["content"][0]
        assert "type" in content_item
        assert content_item["type"] == "text"
        assert "text" in content_item
        assert isinstance(content_item["text"], str)

        # Verify content is properly formatted for Claude
        text_content = content_item["text"]
        assert "Successfully converted" in text_content
        assert test_file.name in text_content
        assert "Test content" in text_content

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_concurrent_claude_requests(self, temp_dir):
        """Test handling concurrent requests from Claude Desktop."""
        server = MarkItDownMCPServer()

        # Create multiple test files
        test_files = []
        for i in range(3):
            file_path = Path(temp_dir) / f"claude_concurrent_{i}.txt"
            file_path.write_text(f"Content for concurrent test {i}")
            test_files.append(str(file_path))

        # Simulate concurrent requests from Claude
        requests = [
            MCPRequest(
                id=f"claude-concurrent-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(3)
        ]

        # Process concurrently
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # Verify all responses are successful and properly formatted
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"claude-concurrent-{i}")

            content = response.result["content"][0]["text"]
            assert f"concurrent test {i}" in content


class TestClaudeDesktopErrorScenarios:
    """Test error scenarios specific to Claude Desktop integration."""

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_connection_recovery(self):
        """Test recovery from connection issues in Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        # Simulate connection failure during initialization
        with patch.object(
            simulator.server, "handle_request", side_effect=Exception("Connection error")
        ):
            try:
                await simulator.initialize_connection()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Connection error" in str(e)

        # Verify server can recover
        init_result = await simulator.initialize_connection()
        assert init_result["success"] is True

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_malformed_request_handling(self):
        """Test handling of malformed requests from Claude Desktop."""
        server = MarkItDownMCPServer()

        # Test various malformed request scenarios
        malformed_scenarios = [
            # Missing required fields
            {"id": None, "method": "initialize", "params": {}},
            {"id": "test", "method": None, "params": {}},
            # Invalid method names
            {"id": "test", "method": "", "params": {}},
            {"id": "test", "method": "invalid/method/name", "params": {}},
            # Invalid params
            {"id": "test", "method": "tools/call", "params": None},
            {"id": "test", "method": "tools/call", "params": "not-a-dict"},
        ]

        for scenario in malformed_scenarios:
            try:
                request = MCPRequest(
                    id=scenario.get("id", "test"),
                    method=scenario.get("method", "test"),
                    params=scenario.get("params", {}),
                )

                response = await server.handle_request(request)

                # Should handle gracefully with appropriate error
                if response.error:
                    assert response.error["code"] in [-32600, -32601, -32602, -32603]

            except (TypeError, ValueError):
                # Some scenarios might raise exceptions during request creation
                # This is acceptable for truly malformed requests
                pass

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_resource_exhaustion_handling(self, temp_dir):
        """Test handling of resource exhaustion scenarios in Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        await simulator.initialize_connection()
        await simulator.discover_tools()

        # Create a very large file that might cause resource issues
        large_file = Path(temp_dir) / "resource_test.txt"
        large_content = "Resource exhaustion test.\n" * 100000  # ~2MB
        large_file.write_text(large_content)

        # Simulate multiple concurrent large file requests
        concurrent_requests = 5
        tasks = []

        for i in range(concurrent_requests):
            task = simulator.call_tool("convert_file", {"file_path": str(large_file)})
            tasks.append(task)

        # Process concurrently and handle potential resource issues
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify that either all succeed or fail gracefully
        successful = 0
        failed = 0

        for result in results:
            if isinstance(result, Exception):
                failed += 1
            elif result["success"]:
                successful += 1
            else:
                failed += 1

        # At least some should complete (either success or graceful failure)
        assert successful + failed == concurrent_requests

        # If there were failures, they should be graceful
        for result in results:
            if not isinstance(result, Exception) and not result["success"]:
                error_msg = result["error"]["message"].lower()
                # Should be resource-related error, not a crash
                acceptable_errors = ["memory", "resource", "timeout", "processing", "large"]
                assert any(term in error_msg for term in acceptable_errors)


class TestClaudeDesktopUserExperience:
    """Test user experience aspects specific to Claude Desktop."""

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_tool_descriptions_clarity(self):
        """Test that tool descriptions are clear for Claude Desktop users."""
        server = MarkItDownMCPServer()

        request = MCPRequest(id="desc-test", method="tools/list", params={})
        response = await server.handle_request(request)

        tools = response.result["tools"]

        for tool in tools:
            description = tool["description"]

            # Descriptions should be clear and helpful
            assert len(description) > 20, f"Description too short for {tool['name']}"
            assert len(description) < 200, f"Description too long for {tool['name']}"

            # Should contain action words
            action_words = ["convert", "list", "process", "transform"]
            has_action = any(word in description.lower() for word in action_words)
            assert has_action, f"Description should contain action word: {description}"

            # Should not contain technical jargon
            jargon_words = ["async", "await", "thread", "process", "buffer"]
            has_jargon = any(word in description.lower() for word in jargon_words)
            assert not has_jargon, f"Description should avoid technical jargon: {description}"

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_success_message_formatting(self, temp_dir):
        """Test that success messages are well-formatted for Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        await simulator.initialize_connection()

        # Create test file
        test_file = Path(temp_dir) / "format_test.txt"
        test_file.write_text("Formatting test content")

        # Test conversion
        result = await simulator.call_tool("convert_file", {"file_path": str(test_file)})

        assert result["success"] is True

        content_text = result["result"]["content"][0]["text"]

        # Should have clear success indication
        assert "Successfully converted" in content_text

        # Should include filename for context
        assert "format_test.txt" in content_text

        # Should include the converted content
        assert "Formatting test content" in content_text

        # Should be well-structured (not just dumped content)
        lines = content_text.split("\n")
        assert len(lines) > 1  # Multiple lines with structure

    @pytest.mark.integration
    @pytest.mark.claude
    @pytest.mark.asyncio
    async def test_claude_progress_indication(self, temp_dir):
        """Test progress indication for long-running operations in Claude Desktop."""
        simulator = ClaudeDesktopSimulator()

        await simulator.initialize_connection()

        # Create directory with multiple files for batch processing
        batch_dir = Path(temp_dir) / "batch_test"
        batch_dir.mkdir()

        # Create several files
        for i in range(10):
            file_path = batch_dir / f"file_{i:02d}.txt"
            file_path.write_text(f"Content of file number {i}")

        # Test directory conversion (longer operation) - specify output directory to avoid conflicts
        output_dir = Path(temp_dir) / "converted_output"
        result = await simulator.call_tool(
            "convert_directory",
            {"input_directory": str(batch_dir), "output_directory": str(output_dir)},
        )

        assert result["success"] is True

        result_text = result["result"]["content"][0]["text"]

        # Should provide clear progress information - expect exactly 10 files
        assert "Successfully converted: 10" in result_text
        assert "Failed conversions: 0" in result_text

        # Should indicate output location
        assert "Output directory:" in result_text

        # Should be informative about what was processed
        assert "files" in result_text.lower()
