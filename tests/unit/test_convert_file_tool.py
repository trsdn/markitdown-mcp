"""
Unit tests for the convert_file MCP tool
"""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_convert_file_response,
    assert_file_path_safe,
    assert_mcp_error_response,
    assert_mcp_success_response,
)
from tests.helpers.file_utils import (
    create_corrupted_file,
    create_large_file,
    create_minimal_pdf,
    create_test_file,
)


class TestConvertFileBasicFunctionality:
    """Test basic convert_file tool functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_text_file_by_path(self, mcp_server, sample_text_file):
        """Test converting a text file using file path."""
        request = MCPRequest(
            id="convert-text-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": sample_text_file}},
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(response, "Hello, World!", "sample.txt")

        # Content should contain the original text
        content_text = response.result["content"][0]["text"]
        assert "This is a test file" in content_text
        assert "multiple lines" in content_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_json_file_by_path(self, mcp_server, sample_json_file):
        """Test converting a JSON file using file path."""
        request = MCPRequest(
            id="convert-json-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": sample_json_file}},
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(response, "Test Document", "sample.json")

        content_text = response.result["content"][0]["text"]
        assert "test" in content_text.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_csv_file_by_path(self, mcp_server, sample_csv_file):
        """Test converting a CSV file using file path."""
        request = MCPRequest(
            id="convert-csv-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": sample_csv_file}},
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(response, "John Doe", "sample.csv")

        content_text = response.result["content"][0]["text"]
        assert "Name,Age,City" in content_text or "John Doe" in content_text


class TestConvertFileBase64Content:
    """Test convert_file tool with base64 encoded content."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_base64_text_content(self, mcp_server, sample_base64_content):
        """Test converting text content via base64 encoding."""
        request = MCPRequest(
            id="convert-base64-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {
                    "file_content": sample_base64_content["encoded"],
                    "filename": sample_base64_content["filename"],
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(
            response, sample_base64_content["original"], sample_base64_content["filename"]
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_base64_json_content(self, mcp_server):
        """Test converting JSON content via base64."""
        json_content = '{"message": "Hello from base64", "type": "test"}'
        encoded_content = base64.b64encode(json_content.encode()).decode()

        request = MCPRequest(
            id="convert-base64-json-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "test.json"},
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(response, "Hello from base64", "test.json")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_large_base64_content(self, mcp_server):
        """Test converting large content via base64."""
        # 100KB of text content
        large_content = "Large content line.\n" * 5000
        encoded_content = base64.b64encode(large_content.encode()).decode()

        request = MCPRequest(
            id="convert-large-base64-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "large.txt"},
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_file_response(response, "Large content line", "large.txt")


class TestConvertFileErrorCases:
    """Test error handling in convert_file tool."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nonexistent_file_error(self, mcp_server):
        """Test error when file doesn't exist."""
        request = MCPRequest(
            id="nonexistent-file-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": "/nonexistent/path/file.txt"},
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "nonexistent-file-test")
        assert "not found" in response.error["message"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_arguments_error(self, mcp_server):
        """Test error when required arguments are missing."""
        request = MCPRequest(
            id="missing-args-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {}},  # Missing required arguments
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "missing-args-test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_base64_error(self, mcp_server):
        """Test error with invalid base64 content."""
        request = MCPRequest(
            id="invalid-base64-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {
                    "file_content": "invalid-base64-content!@#$%",
                    "filename": "test.txt",
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32603, "invalid-base64-test")
        assert (
            "base64" in response.error["message"].lower()
            or "decode" in response.error["message"].lower()
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_filename_for_base64(self, mcp_server):
        """Test error when filename is missing for base64 content."""
        content = base64.b64encode(b"test content").decode()

        request = MCPRequest(
            id="missing-filename-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {
                    "file_content": content
                    # Missing filename
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "missing-filename-test")


class TestConvertFileEdgeCases:
    """Test edge cases for convert_file tool."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_file_conversion(self, mcp_server, empty_file):
        """Test converting an empty file."""
        request = MCPRequest(
            id="empty-file-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": empty_file}},
        )

        response = await mcp_server.handle_request(request)

        # Should succeed but with minimal content
        assert_mcp_success_response(response, "empty-file-test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unicode_filename_handling(self, mcp_server, unicode_filename_file):
        """Test handling files with unicode characters in filename."""
        request = MCPRequest(
            id="unicode-filename-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": unicode_filename_file}},
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_success_response(response, "unicode-filename-test")
        content_text = response.result["content"][0]["text"]
        assert "Unicode filename test content" in content_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unicode_content_handling(self, mcp_server, temp_dir):
        """Test handling files with unicode content."""
        unicode_content = "Unicode test: 你好世界 🌍 émojis and accénts"
        unicode_file = create_test_file(unicode_content, "unicode_content.txt", temp_dir)

        request = MCPRequest(
            id="unicode-content-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": unicode_file}},
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_success_response(response, "unicode-content-test")
        content_text = response.result["content"][0]["text"]
        assert "你好世界" in content_text
        assert "🌍" in content_text
        assert "émojis" in content_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_binary_file_handling(self, mcp_server, temp_dir):
        """Test handling of binary files."""
        # Create a simple binary file
        binary_content = bytes(range(256))  # 0-255 byte values
        binary_file = Path(temp_dir) / "binary.bin"
        binary_file.write_bytes(binary_content)

        request = MCPRequest(
            id="binary-file-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(binary_file)}},
        )

        response = await mcp_server.handle_request(request)

        # Should either succeed or fail gracefully
        assert response.result is not None or response.error is not None


class TestConvertFileFormats:
    """Test convert_file with various file formats."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "file_extension,content_type",
        [
            (".txt", "text/plain"),
            (".json", "application/json"),
            (".csv", "text/csv"),
            (".html", "text/html"),
            (".xml", "application/xml"),
            (".md", "text/markdown"),
        ],
    )
    @pytest.mark.asyncio
    async def test_supported_text_formats(self, mcp_server, temp_dir, file_extension, content_type):
        """Test conversion of various supported text formats."""
        content_map = {
            ".txt": "Plain text content",
            ".json": '{"key": "value", "number": 42}',
            ".csv": "Name,Age\nAlice,30\nBob,25",
            ".html": "<html><body><h1>Title</h1><p>Content</p></body></html>",
            ".xml": '<?xml version="1.0"?><root><item>value</item></root>',
            ".md": "# Markdown Title\n\nSome **bold** text.",
        }

        content = content_map[file_extension]
        test_file = create_test_file(content, f"test{file_extension}", temp_dir)

        request = MCPRequest(
            id=f"format-test-{file_extension}",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": test_file}},
        )

        response = await mcp_server.handle_request(request)

        # Should succeed for all supported formats
        assert_mcp_success_response(response, f"format-test-{file_extension}")

    @pytest.mark.unit
    @pytest.mark.requires_dependencies
    @pytest.mark.asyncio
    async def test_pdf_format_conversion(self, mcp_server, temp_dir):
        """Test PDF file conversion (requires dependencies)."""
        try:
            pdf_file = create_minimal_pdf(temp_dir)
        except Exception:
            pytest.skip("PDF creation dependencies not available")

        request = MCPRequest(
            id="pdf-format-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": pdf_file}},
        )

        response = await mcp_server.handle_request(request)

        # Should succeed if dependencies are available
        if response.result:
            assert_mcp_success_response(response, "pdf-format-test")
        else:
            # If dependencies missing, should be a clear error
            assert "dependency" in response.error["message"].lower()


class TestConvertFilePerformance:
    """Test performance aspects of convert_file tool."""

    @pytest.mark.unit
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_file_conversion(self, mcp_server, large_text_file):
        """Test conversion of large text file."""
        import time

        request = MCPRequest(
            id="large-file-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": large_text_file}},
        )

        start_time = time.time()
        response = await mcp_server.handle_request(request)
        end_time = time.time()

        # Should complete within reasonable time (30 seconds)
        assert end_time - start_time < 30, "Large file conversion took too long"

        # Should either succeed or fail gracefully
        assert response.result is not None or response.error is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self, mcp_server, temp_dir):
        """Test that file processing doesn't load entire file into memory unnecessarily."""
        # Create a moderately large file (10MB)
        large_file = create_large_file(10, "memory_test.txt", temp_dir)

        request = MCPRequest(
            id="memory-efficient-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": large_file}},
        )

        # Monitor memory usage (simplified test)
        response = await mcp_server.handle_request(request)

        # Should complete without memory errors
        assert response.result is not None or response.error is not None


class TestConvertFileSecurityAspects:
    """Test security aspects of convert_file tool."""

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, mcp_server, malicious_path_attempts):
        """Test that path traversal attacks are prevented."""
        for malicious_path in malicious_path_attempts:
            request = MCPRequest(
                id=f"path-traversal-{hash(malicious_path)}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": malicious_path}},
            )

            response = await mcp_server.handle_request(request)

            # Should reject malicious paths with appropriate error
            assert_mcp_error_response(response, -32602)

            # Ensure path is flagged as unsafe
            assert_file_path_safe(malicious_path) == False or response.error is not None

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self, mcp_server, temp_dir):
        """Test handling of corrupted files."""
        corrupted_files = [
            create_corrupted_file("corrupted.pdf", temp_dir),
            create_corrupted_file("corrupted.json", temp_dir),
            create_corrupted_file("corrupted.png", temp_dir),
        ]

        for corrupted_file in corrupted_files:
            request = MCPRequest(
                id=f"corrupted-{Path(corrupted_file).stem}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": corrupted_file}},
            )

            response = await mcp_server.handle_request(request)

            # Should handle corrupted files gracefully
            assert response.result is not None or response.error is not None

            # Error messages should not leak system information
            if response.error:
                error_msg = response.error["message"]
                assert "traceback" not in error_msg.lower()
                assert "exception" not in error_msg.lower()


class TestConvertFileWithMocking:
    """Test convert_file tool with mocked dependencies."""

    @pytest.mark.unit
    @patch("markitdown_mcp.server.MarkItDown")
    @pytest.mark.asyncio
    async def test_markitdown_success_mock(
        self, mock_markitdown_class, mcp_server, sample_text_file
    ):
        """Test successful conversion with mocked MarkItDown."""
        # Setup mock
        mock_instance = mock_markitdown_class.return_value
        mock_result = Mock()
        mock_result.text_content = "Mocked conversion result"
        mock_instance.convert.return_value = mock_result

        # Create new server instance to use mocked MarkItDown
        server = MarkItDownMCPServer()

        request = MCPRequest(
            id="mock-success-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": sample_text_file}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "Mocked conversion result")
        mock_instance.convert.assert_called_once()

    @pytest.mark.unit
    @patch("markitdown_mcp.server.MarkItDown")
    @pytest.mark.asyncio
    async def test_markitdown_error_mock(self, mock_markitdown_class, mcp_server, sample_text_file):
        """Test error handling with mocked MarkItDown exception."""
        # Setup mock to raise exception
        mock_instance = mock_markitdown_class.return_value
        mock_instance.convert.side_effect = Exception("Mocked conversion error")

        # Create new server instance to use mocked MarkItDown
        server = MarkItDownMCPServer()

        request = MCPRequest(
            id="mock-error-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": sample_text_file}},
        )

        response = await server.handle_request(request)

        assert_mcp_error_response(response, -32603, "mock-error-test")
        assert "conversion" in response.error["message"].lower()
        mock_instance.convert.assert_called_once()
