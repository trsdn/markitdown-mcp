"""
pytest configuration and shared fixtures for MarkItDown MCP Server tests
"""

import pytest
import pytest_asyncio
import tempfile
import shutil
import json
import base64
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any
import asyncio

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest, MCPResponse


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mcp_server():
    """Create a fresh MCP server instance for each test."""
    server = MarkItDownMCPServer()
    yield server
    # Cleanup if needed


@pytest.fixture
def temp_dir():
    """Create a temporary directory that's cleaned up after the test."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = Path(temp_dir) / "sample.txt"
    content = "Hello, World!\nThis is a test file.\nWith multiple lines."
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing."""
    file_path = Path(temp_dir) / "sample.json"
    content = {
        "name": "Test Document",
        "type": "test",
        "data": [1, 2, 3, 4, 5],
        "metadata": {"created": "2024-01-01", "author": "Test Suite"},
    }
    file_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_csv_file(temp_dir):
    """Create a sample CSV file for testing."""
    file_path = Path(temp_dir) / "sample.csv"
    content = """Name,Age,City,Country
John Doe,25,New York,USA
Jane Smith,30,London,UK
Bob Johnson,35,Toronto,Canada
Alice Brown,28,Sydney,Australia"""
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_html_file(temp_dir):
    """Create a sample HTML file for testing."""
    file_path = Path(temp_dir) / "sample.html"
    content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
        <li>List item 3</li>
    </ul>
    <table>
        <tr><th>Name</th><th>Value</th></tr>
        <tr><td>Alpha</td><td>1</td></tr>
        <tr><td>Beta</td><td>2</td></tr>
    </table>
</body>
</html>"""
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def sample_directory(temp_dir):
    """Create a directory with multiple test files."""
    base_path = Path(temp_dir) / "sample_docs"
    base_path.mkdir()

    # Create various file types
    files = {
        "document1.txt": "First document content",
        "document2.txt": "Second document content",
        "data.json": '{"test": "data", "numbers": [1, 2, 3]}',
        "info.csv": "Name,Value\nTest,123\nDemo,456",
        "page.html": "<html><body><h1>Test Page</h1><p>Content</p></body></html>",
        "readme.md": "# Test Readme\n\nThis is a test markdown file.",
    }

    created_files = []
    for filename, content in files.items():
        file_path = base_path / filename
        file_path.write_text(content, encoding="utf-8")
        created_files.append(str(file_path))

    return {"directory": str(base_path), "files": created_files, "count": len(files)}


@pytest.fixture
def empty_file(temp_dir):
    """Create an empty file for testing edge cases."""
    file_path = Path(temp_dir) / "empty.txt"
    file_path.touch()
    return str(file_path)


@pytest.fixture
def large_text_file(temp_dir):
    """Create a large text file for performance testing."""
    file_path = Path(temp_dir) / "large.txt"
    # Create 1MB of text content
    content = "This is a line of text for testing large file handling.\n" * 50000
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def unicode_filename_file(temp_dir):
    """Create a file with unicode characters in the name."""
    file_path = Path(temp_dir) / "测试文件_🚀_test.txt"
    content = "Unicode filename test content"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def malicious_path_attempts():
    """Provide common malicious path patterns for security testing."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow",
        "C:\\Windows\\System32\\config\\SAM",
        "../../../../../../etc/hosts",
        "\\\\server\\share\\file.txt",
        "/dev/null",
        "/proc/version",
        "file:///etc/passwd",
        "\\x2e\\x2e/\\x2e\\x2e/etc/passwd",
    ]


@pytest.fixture
def sample_base64_content():
    """Provide sample content encoded as base64."""
    content = "This is test content for base64 encoding tests.\nSecond line of content."
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return {"original": content, "encoded": encoded, "filename": "test.txt"}


@pytest.fixture
def mcp_initialize_request():
    """Standard MCP initialize request."""
    return MCPRequest(id="init-test", method="initialize", params={})


@pytest.fixture
def mcp_tools_list_request():
    """Standard MCP tools/list request."""
    return MCPRequest(id="tools-test", method="tools/list", params={})


def create_mcp_tool_request(
    tool_name: str, arguments: Dict[str, Any], request_id: str = "tool-test"
) -> MCPRequest:
    """Helper to create MCP tool call requests."""
    return MCPRequest(
        id=request_id, method="tools/call", params={"name": tool_name, "arguments": arguments}
    )


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests - fast, isolated")
    config.addinivalue_line("markers", "integration: Integration tests - component interaction")
    config.addinivalue_line("markers", "performance: Performance tests - resource intensive")
    config.addinivalue_line("markers", "security: Security tests - vulnerability testing")
    config.addinivalue_line("markers", "compatibility: Cross-platform compatibility tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 10 seconds")
    config.addinivalue_line(
        "markers", "requires_dependencies: Tests requiring optional dependencies"
    )


# Test utilities
class MCPTestClient:
    """Mock MCP client for testing server responses."""

    def __init__(self, server: MarkItDownMCPServer):
        self.server = server
        self.request_id_counter = 1

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> MCPResponse:
        """Send a request to the server and return the response."""
        request = MCPRequest(id=str(self.request_id_counter), method=method, params=params or {})
        self.request_id_counter += 1
        return await self.server.handle_request(request)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Call a specific tool and return the response."""
        return await self.send_request("tools/call", {"name": tool_name, "arguments": arguments})


@pytest_asyncio.fixture
async def mcp_test_client(mcp_server):
    """Create a test client for easier server interaction."""
    return MCPTestClient(mcp_server)


# Mock fixtures for external dependencies
@pytest.fixture
def mock_markitdown():
    """Mock MarkItDown instance for unit testing."""
    mock = Mock()
    mock.convert.return_value = Mock(text_content="Mocked conversion result")
    return mock
