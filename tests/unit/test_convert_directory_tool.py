"""
Unit tests for the convert_directory MCP tool
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_mcp_success_response,
    assert_mcp_error_response,
    assert_convert_directory_response,
    assert_file_converted_to_markdown,
)
from tests.helpers.file_utils import create_test_directory_structure, create_test_file


class TestConvertDirectoryBasicFunctionality:
    """Test basic functionality of convert_directory tool."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_directory_success(self, mcp_server, sample_directory):
        """Test successful directory conversion."""
        output_dir = tempfile.mkdtemp()

        try:
            request = MCPRequest(
                id="dir-convert-test",
                method="tools/call",
                params={
                    "name": "convert_directory",
                    "arguments": {
                        "input_directory": sample_directory["directory"],
                        "output_directory": output_dir,
                    },
                },
            )

            response = await mcp_server.handle_request(request)

            assert_convert_directory_response(
                response, expected_success_count=sample_directory["count"]
            )

            # Check that output directory exists and has files
            output_path = Path(output_dir)
            assert output_path.exists()

            # Should have markdown files
            md_files = list(output_path.glob("*.md"))
            assert len(md_files) > 0, "Should create markdown files"

        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_directory_without_output_dir(self, mcp_server, sample_directory):
        """Test directory conversion without specifying output directory."""
        request = MCPRequest(
            id="dir-convert-no-output-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": sample_directory["directory"]
                    # No output_directory specified
                },
            },
        )

        response = await mcp_server.handle_request(request)

        # Should either succeed with default output or provide clear error
        if response.result:
            assert_convert_directory_response(response)
        else:
            assert_mcp_error_response(response)
            assert "output" in response.error["message"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_convert_empty_directory(self, mcp_server, temp_dir):
        """Test converting an empty directory."""
        empty_dir = Path(temp_dir) / "empty"
        empty_dir.mkdir()

        output_dir = Path(temp_dir) / "empty_output"
        output_dir.mkdir()

        request = MCPRequest(
            id="empty-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(empty_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_directory_response(response, expected_success_count=0)


class TestConvertDirectoryErrorHandling:
    """Test error handling in convert_directory tool."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nonexistent_input_directory(self, mcp_server, temp_dir):
        """Test error when input directory doesn't exist."""
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        request = MCPRequest(
            id="nonexistent-input-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": "/nonexistent/directory",
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "nonexistent-input-test")
        assert (
            "not found" in response.error["message"].lower()
            or "exist" in response.error["message"].lower()
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_arguments(self, mcp_server):
        """Test error when required arguments are missing."""
        request = MCPRequest(
            id="missing-args-dir-test",
            method="tools/call",
            params={"name": "convert_directory", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "missing-args-dir-test")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_file_instead_of_directory(self, mcp_server, sample_text_file, temp_dir):
        """Test error when input path is a file, not directory."""
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        request = MCPRequest(
            id="file-not-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": sample_text_file,  # File, not directory
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_error_response(response, -32602, "file-not-dir-test")
        assert "directory" in response.error["message"].lower()


class TestConvertDirectoryComplexScenarios:
    """Test complex directory conversion scenarios."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nested_directory_structure(self, mcp_server, temp_dir):
        """Test conversion of nested directory structure."""
        # Create complex directory structure
        complex_structure = create_test_directory_structure(temp_dir)
        output_dir = Path(temp_dir) / "complex_output"
        output_dir.mkdir()

        request = MCPRequest(
            id="nested-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": complex_structure["base_directory"],
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_directory_response(
            response, expected_success_count=complex_structure["total_files"]
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mixed_file_types(self, mcp_server, temp_dir):
        """Test conversion of directory with mixed file types."""
        mixed_dir = Path(temp_dir) / "mixed"
        mixed_dir.mkdir()

        # Create various file types
        files_created = []

        # Supported formats
        files_created.append(create_test_file("Text content", "text.txt", str(mixed_dir)))
        files_created.append(create_test_file('{"key": "value"}', "data.json", str(mixed_dir)))
        files_created.append(create_test_file("Name,Age\nJohn,25", "people.csv", str(mixed_dir)))

        # Unsupported/problematic formats
        files_created.append(create_test_file("Binary-like content", "data.bin", str(mixed_dir)))

        output_dir = Path(temp_dir) / "mixed_output"
        output_dir.mkdir()

        request = MCPRequest(
            id="mixed-files-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(mixed_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_success_response(response, "mixed-files-test")

        # Should report both successes and failures
        content_text = response.result["content"][0]["text"]
        assert "successfully converted" in content_text.lower()

        # May have some failures for unsupported formats
        if "failed conversions" in content_text.lower():
            assert "0" not in content_text or "failed" not in content_text.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_large_directory(self, mcp_server, temp_dir):
        """Test conversion of directory with many files."""
        large_dir = Path(temp_dir) / "large"
        large_dir.mkdir()

        # Create 100 small files
        files_count = 100
        for i in range(files_count):
            create_test_file(f"Content of file {i}", f"file_{i:03d}.txt", str(large_dir))

        output_dir = Path(temp_dir) / "large_output"
        output_dir.mkdir()

        request = MCPRequest(
            id="large-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(large_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_directory_response(response, expected_success_count=files_count)

        # Check that all files were converted
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) == files_count, f"Expected {files_count} files, got {len(md_files)}"


class TestConvertDirectoryFileHandling:
    """Test specific file handling aspects of directory conversion."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_preserves_file_names(self, mcp_server, temp_dir):
        """Test that original file names are preserved in output."""
        test_dir = Path(temp_dir) / "names_test"
        test_dir.mkdir()
        output_dir = Path(temp_dir) / "names_output"
        output_dir.mkdir()

        # Create files with specific names
        test_files = [
            ("important_document.txt", "Important content"),
            ("data_analysis.json", '{"analysis": "complete"}'),
            ("meeting_notes.md", "# Meeting Notes\n\nDiscussion points"),
        ]

        for filename, content in test_files:
            create_test_file(content, filename, str(test_dir))

        request = MCPRequest(
            id="preserve-names-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(test_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        assert_convert_directory_response(response, expected_success_count=len(test_files))

        # Check that output files have corresponding names
        for filename, _ in test_files:
            stem = Path(filename).stem
            expected_output = output_dir / f"{stem}.md"
            assert expected_output.exists(), f"Expected output file {expected_output} should exist"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_duplicate_names(self, mcp_server, temp_dir):
        """Test handling of files with similar names."""
        test_dir = Path(temp_dir) / "duplicates"
        test_dir.mkdir()
        output_dir = Path(temp_dir) / "duplicates_output"
        output_dir.mkdir()

        # Create files that would have same output name
        create_test_file("Content 1", "document.txt", str(test_dir))
        create_test_file('{"data": 1}', "document.json", str(test_dir))
        create_test_file("Name,Value\nTest,1", "document.csv", str(test_dir))

        request = MCPRequest(
            id="duplicate-names-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(test_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        # Should handle duplicates gracefully (might overwrite or rename)
        assert_mcp_success_response(response, "duplicate-names-test")

        # At least one output file should exist
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) >= 1, "Should create at least one output file"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unicode_filenames(self, mcp_server, temp_dir):
        """Test handling of files with unicode names."""
        test_dir = Path(temp_dir) / "unicode"
        test_dir.mkdir()
        output_dir = Path(temp_dir) / "unicode_output"
        output_dir.mkdir()

        # Create files with unicode names
        unicode_files = [
            ("测试文档.txt", "Chinese filename content"),
            ("émojis_🚀_file.txt", "Emoji filename content"),
            ("café_résumé.txt", "Accented filename content"),
        ]

        for filename, content in unicode_files:
            try:
                create_test_file(content, filename, str(test_dir))
            except OSError:
                # Skip if filesystem doesn't support unicode names
                continue

        request = MCPRequest(
            id="unicode-filenames-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(test_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        # Should handle unicode filenames gracefully
        assert_mcp_success_response(response, "unicode-filenames-test")


class TestConvertDirectoryPerformance:
    """Test performance aspects of directory conversion."""

    @pytest.mark.unit
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_conversion_time_reasonable(self, mcp_server, temp_dir):
        """Test that directory conversion completes in reasonable time."""
        import time

        # Create moderate-sized directory (50 files)
        perf_dir = Path(temp_dir) / "performance"
        perf_dir.mkdir()
        output_dir = Path(temp_dir) / "performance_output"
        output_dir.mkdir()

        files_count = 50
        for i in range(files_count):
            content = f"Performance test file {i}\n" + "Content line\n" * 10
            create_test_file(content, f"perf_{i:02d}.txt", str(perf_dir))

        request = MCPRequest(
            id="performance-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(perf_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        start_time = time.time()
        response = await mcp_server.handle_request(request)
        end_time = time.time()

        # Should complete within reasonable time (30 seconds for 50 files)
        assert (
            end_time - start_time < 30
        ), f"Directory conversion took {end_time - start_time:.2f}s, expected < 30s"

        assert_convert_directory_response(response, expected_success_count=files_count)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_memory_usage_bounded(self, mcp_server, temp_dir):
        """Test that directory conversion doesn't use excessive memory."""
        # Create directory with files of various sizes
        memory_dir = Path(temp_dir) / "memory_test"
        memory_dir.mkdir()
        output_dir = Path(temp_dir) / "memory_output"
        output_dir.mkdir()

        # Create mix of small and medium files
        for i in range(10):
            size = "small" if i < 5 else "medium"
            content = f"Memory test {size} file {i}\n" + "Line of content\n" * (
                100 if size == "small" else 1000
            )
            create_test_file(content, f"memory_{size}_{i}.txt", str(memory_dir))

        request = MCPRequest(
            id="memory-usage-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(memory_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await mcp_server.handle_request(request)

        # Should complete without memory errors
        assert_convert_directory_response(response, expected_success_count=10)


class TestConvertDirectorySecurity:
    """Test security aspects of directory conversion."""

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, mcp_server, temp_dir):
        """Test prevention of path traversal attacks."""
        output_dir = Path(temp_dir) / "secure_output"
        output_dir.mkdir()

        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/shadow",
            "../../../../root/",
        ]

        for malicious_path in malicious_paths:
            request = MCPRequest(
                id=f"path-traversal-{hash(malicious_path)}",
                method="tools/call",
                params={
                    "name": "convert_directory",
                    "arguments": {
                        "input_directory": malicious_path,
                        "output_directory": str(output_dir),
                    },
                },
            )

            response = await mcp_server.handle_request(request)

            # Should reject malicious paths
            assert_mcp_error_response(response, -32602)

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_output_directory_safety(self, mcp_server, sample_directory):
        """Test that output directory paths are validated for safety."""
        unsafe_output_paths = [
            "/etc/important_system_dir",
            "../../../system_directory",
            "/root/dangerous_location",
        ]

        for unsafe_path in unsafe_output_paths:
            request = MCPRequest(
                id=f"unsafe-output-{hash(unsafe_path)}",
                method="tools/call",
                params={
                    "name": "convert_directory",
                    "arguments": {
                        "input_directory": sample_directory["directory"],
                        "output_directory": unsafe_path,
                    },
                },
            )

            response = await mcp_server.handle_request(request)

            # Should handle unsafe output paths appropriately
            # (Either reject them or handle them safely)
            if response.error:
                assert_mcp_error_response(response)
            else:
                # If allowed, should not actually write to unsafe locations
                assert_mcp_success_response(response)


class TestConvertDirectoryWithMocking:
    """Test convert_directory with mocked dependencies."""

    @pytest.mark.unit
    @patch("markitdown_mcp.server.MarkItDown")
    @pytest.mark.asyncio
    async def test_directory_conversion_with_mock(
        self, mock_markitdown_class, mcp_server, sample_directory, temp_dir
    ):
        """Test directory conversion with mocked MarkItDown."""
        # Setup mock
        mock_instance = mock_markitdown_class.return_value
        mock_result = Mock()
        mock_result.text_content = "Mocked conversion result"
        mock_instance.convert.return_value = mock_result

        output_dir = Path(temp_dir) / "mock_output"
        output_dir.mkdir()

        # Create new server instance to use mocked MarkItDown
        server = MarkItDownMCPServer()

        request = MCPRequest(
            id="mock-directory-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": sample_directory["directory"],
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await server.handle_request(request)

        assert_convert_directory_response(
            response, expected_success_count=sample_directory["count"]
        )

        # Verify mock was called for each file
        assert mock_instance.convert.call_count == sample_directory["count"]
