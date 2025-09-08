"""
Custom assertions and validation helpers for MarkItDown MCP Server tests
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from markitdown_mcp.server import MCPRequest, MCPResponse


def assert_valid_mcp_response(response: MCPResponse, expected_id: str = None) -> None:
    """Assert that an MCP response is valid."""
    assert response is not None, "Response should not be None"

    if expected_id is not None:
        assert response.id == expected_id, f"Response ID should be {expected_id}, got {response.id}"

    # Response should have either result or error, but not both
    has_result = response.result is not None
    has_error = response.error is not None

    assert has_result or has_error, "Response must have either result or error"
    assert not (has_result and has_error), "Response cannot have both result and error"


def assert_valid_mcp_request(request: MCPRequest) -> None:
    """Assert that an MCP request is valid."""
    assert request is not None, "Request should not be None"
    assert request.id is not None, "Request must have an ID"
    assert request.method is not None, "Request must have a method"
    assert request.params is not None, "Request must have params (can be empty dict)"


def assert_mcp_success_response(response: MCPResponse, expected_id: str = None) -> None:
    """Assert that an MCP response indicates success."""
    assert_valid_mcp_response(response, expected_id)
    assert response.error is None, f"Response should not have error, got: {response.error}"
    assert response.result is not None, "Success response must have result"


def assert_mcp_error_response(
    response: MCPResponse, expected_code: int = None, expected_id: str = None
) -> None:
    """Assert that an MCP response indicates an error."""
    assert_valid_mcp_response(response, expected_id)
    assert response.result is None, f"Error response should not have result, got: {response.result}"
    assert response.error is not None, "Error response must have error"

    assert "code" in response.error, "Error must have code"
    assert "message" in response.error, "Error must have message"

    if expected_code is not None:
        assert (
            response.error["code"] == expected_code
        ), f"Expected error code {expected_code}, got {response.error['code']}"


def assert_valid_tool_response(response: MCPResponse, expected_id: str = None) -> None:
    """Assert that a tool call response is valid."""
    assert_mcp_success_response(response, expected_id)

    result = response.result
    assert "content" in result, "Tool response must have content"
    assert isinstance(result["content"], list), "Content must be a list"
    assert len(result["content"]) > 0, "Content list must not be empty"

    # Validate content structure
    for item in result["content"]:
        assert isinstance(item, dict), "Content item must be a dictionary"
        assert "type" in item, "Content item must have type"
        assert "text" in item, "Content item must have text"
        assert isinstance(item["text"], str), "Content text must be a string"


def assert_convert_file_response(
    response: MCPResponse, expected_content: str = None, expected_filename: str = None
) -> None:
    """Assert that a convert_file tool response is valid."""
    assert_valid_tool_response(response)

    content_text = response.result["content"][0]["text"]

    if expected_content is not None:
        assert (
            expected_content in content_text
        ), f"Expected '{expected_content}' in response, got: {content_text[:200]}..."

    if expected_filename is not None:
        assert (
            expected_filename in content_text
        ), f"Expected filename '{expected_filename}' in response"


def assert_list_formats_response(response: MCPResponse) -> None:
    """Assert that a list_supported_formats response is valid."""
    assert_valid_tool_response(response)

    content_text = response.result["content"][0]["text"]

    # Should contain major format categories
    expected_categories = ["Office", "Images", "Audio", "Web", "Text"]
    for category in expected_categories:
        assert (
            category.lower() in content_text.lower()
        ), f"Format list should contain '{category}' category"

    # Should contain common extensions
    common_extensions = [".pdf", ".docx", ".xlsx", ".png", ".jpg", ".mp3", ".txt", ".json"]
    for ext in common_extensions:
        assert ext in content_text, f"Format list should contain '{ext}' extension"


def assert_convert_directory_response(
    response: MCPResponse, expected_success_count: int = None, expected_failure_count: int = None
) -> None:
    """Assert that a convert_directory response is valid."""
    assert_valid_tool_response(response)

    content_text = response.result["content"][0]["text"]

    # Should contain conversion summary
    assert (
        "conversion completed" in content_text.lower()
    ), "Directory conversion response should contain completion message"

    if expected_success_count is not None:
        success_pattern = rf"successfully converted:\s*{expected_success_count}"
        assert re.search(
            success_pattern, content_text, re.IGNORECASE
        ), f"Expected {expected_success_count} successful conversions in: {content_text}"

    if expected_failure_count is not None:
        failure_pattern = rf"failed conversions:\s*{expected_failure_count}"
        assert re.search(
            failure_pattern, content_text, re.IGNORECASE
        ), f"Expected {expected_failure_count} failed conversions in: {content_text}"


def assert_file_converted_to_markdown(file_path: str, expected_content: List[str] = None) -> None:
    """Assert that a file was successfully converted to markdown."""
    path = Path(file_path)
    assert path.exists(), f"Converted file should exist: {file_path}"
    assert path.suffix.lower() == ".md", f"Converted file should be .md, got: {path.suffix}"

    content = path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "Converted markdown should not be empty"

    if expected_content:
        for expected in expected_content:
            assert (
                expected in content
            ), f"Expected '{expected}' in converted markdown: {content[:200]}..."


def assert_valid_json_rpc_response(response_text: str) -> Dict[str, Any]:
    """Assert that response text is valid JSON-RPC and return parsed response."""
    try:
        response = json.loads(response_text)
    except json.JSONDecodeError as e:
        assert False, f"Response is not valid JSON: {e}\nResponse: {response_text}"

    assert "jsonrpc" in response, "Response must have jsonrpc field"
    assert response["jsonrpc"] == "2.0", "Response must be JSON-RPC 2.0"
    assert "id" in response, "Response must have id field"

    # Must have either result or error
    has_result = "result" in response
    has_error = "error" in response
    assert has_result or has_error, "Response must have either result or error"
    assert not (has_result and has_error), "Response cannot have both result and error"

    return response


def assert_performance_within_limits(
    execution_time: float, max_seconds: float, operation_name: str = "Operation"
) -> None:
    """Assert that an operation completed within performance limits."""
    assert (
        execution_time <= max_seconds
    ), f"{operation_name} took {execution_time:.2f}s, expected <= {max_seconds}s"


def assert_memory_usage_reasonable(
    memory_usage_mb: float, max_mb: float, operation_name: str = "Operation"
) -> None:
    """Assert that memory usage is within reasonable limits."""
    assert (
        memory_usage_mb <= max_mb
    ), f"{operation_name} used {memory_usage_mb:.1f}MB, expected <= {max_mb}MB"


def assert_file_path_safe(file_path: str) -> None:
    """Assert that a file path is safe (no path traversal attempts)."""
    path = Path(file_path)

    # Check for path traversal patterns
    path_str = str(path)
    dangerous_patterns = [
        "..",
        "/etc/",
        "/proc/",
        "/sys/",
        "/dev/",
        "\\windows\\",
        "\\system32\\",
        "file://",
        "\\\\",
        "/root/",
        "/home/",
    ]

    for pattern in dangerous_patterns:
        assert (
            pattern.lower() not in path_str.lower()
        ), f"File path contains dangerous pattern '{pattern}': {file_path}"


def assert_no_sensitive_info_leaked(response_text: str) -> None:
    """Assert that response doesn't contain sensitive information."""
    response_lower = response_text.lower()

    # Check for common sensitive patterns
    sensitive_patterns = [
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "/etc/passwd",
        "/etc/shadow",
        "config.json",
        "database",
        "connection",
        "credential",
    ]

    for pattern in sensitive_patterns:
        assert (
            pattern not in response_lower
        ), f"Response may contain sensitive information: '{pattern}'"


def assert_unicode_handling_correct(text: str, expected_unicode_chars: List[str] = None) -> None:
    """Assert that unicode characters are handled correctly."""
    # Text should be valid unicode
    assert isinstance(text, str), "Text should be a string"

    # Should be encodable/decodable
    try:
        encoded = text.encode("utf-8")
        decoded = encoded.decode("utf-8")
        assert decoded == text, "Text should survive utf-8 encoding/decoding"
    except UnicodeError as e:
        assert False, f"Unicode handling error: {e}"

    if expected_unicode_chars:
        for char in expected_unicode_chars:
            assert char in text, f"Expected unicode character '{char}' in text"


def assert_markdown_structure_valid(markdown_text: str) -> None:
    """Assert that markdown text has valid basic structure."""
    lines = markdown_text.split("\n")

    # Should have some content
    non_empty_lines = [line for line in lines if line.strip()]
    assert len(non_empty_lines) > 0, "Markdown should have some content"

    # Check for common markdown elements (at least one should be present)
    has_headers = any(line.strip().startswith("#") for line in lines)
    has_text = any(line.strip() and not line.strip().startswith("#") for line in lines)

    assert has_headers or has_text, "Markdown should have headers or text content"


def assert_error_message_helpful(error_message: str) -> None:
    """Assert that error message is helpful to users."""
    assert len(error_message) > 10, "Error message should be descriptive"
    assert not error_message.isupper(), "Error message should not be all caps"

    # Should not contain internal system details
    internal_patterns = ["traceback", "exception", "stack trace", "__", "0x"]
    message_lower = error_message.lower()

    for pattern in internal_patterns:
        assert (
            pattern not in message_lower
        ), f"Error message should not contain internal details: '{pattern}'"
