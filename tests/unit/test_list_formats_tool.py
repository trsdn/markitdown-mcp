"""
Unit tests for the list_supported_formats MCP tool
"""

from unittest.mock import Mock, patch

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_list_formats_response,
    assert_mcp_error_response,
    assert_mcp_success_response,
)


class TestListSupportedFormatsBasicFunctionality:
    """Test basic functionality of list_supported_formats tool."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_formats_success(self, mcp_server):
        """Test successful format listing."""
        request = MCPRequest(
            id="list-formats-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)

        assert_list_formats_response(response)
        assert response.id == "list-formats-test"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_formats_no_arguments_needed(self, mcp_server):
        """Test that list_supported_formats works with empty arguments."""
        request = MCPRequest(
            id="list-formats-empty-args",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)

        assert_mcp_success_response(response, "list-formats-empty-args")


class TestListSupportedFormatsContent:
    """Test the content and structure of format listings."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_format_categories_present(self, mcp_server):
        """Test that all expected format categories are present."""
        request = MCPRequest(
            id="categories-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Check for major categories
        expected_categories = [
            "Office Documents",
            "office",  # PDF, DOCX, etc.
            "Images",
            "image",
            "Audio",
            "audio",
            "Web",
            "web",
            "markup",
            "Text",
            "text",
        ]

        # At least some categories should be present
        category_found = any(cat.lower() in content_text.lower() for cat in expected_categories)
        assert category_found, f"No expected categories found in: {content_text[:200]}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_common_extensions_present(self, mcp_server):
        """Test that common file extensions are listed."""
        request = MCPRequest(
            id="extensions-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Check for essential extensions
        essential_extensions = [".pdf", ".docx", ".txt", ".json", ".csv"]

        for ext in essential_extensions:
            assert ext in content_text, f"Extension {ext} should be listed in formats"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_format_count_accuracy(self, mcp_server):
        """Test that the claimed format count matches reality."""
        request = MCPRequest(
            id="count-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Count extensions mentioned (simple heuristic)
        import re

        extensions = re.findall(r"\.\w+", content_text)
        unique_extensions = set(extensions)

        # Should have at least 15 different extensions
        assert (
            len(unique_extensions) >= 15
        ), f"Expected at least 15 formats, found {len(unique_extensions)}: {unique_extensions}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_format_descriptions_helpful(self, mcp_server):
        """Test that format descriptions are helpful and informative."""
        request = MCPRequest(
            id="descriptions-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Should contain descriptive terms
        descriptive_terms = [
            "document",
            "image",
            "audio",
            "text",
            "data",
            "office",
            "pdf",
            "excel",
            "word",
            "powerpoint",
        ]

        terms_found = sum(1 for term in descriptive_terms if term.lower() in content_text.lower())

        assert (
            terms_found >= 5
        ), f"Format list should be descriptive, found only {terms_found} descriptive terms"


class TestListSupportedFormatsConsistency:
    """Test consistency and reliability of format listings."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_consistent_output(self, mcp_server):
        """Test that multiple calls return consistent results."""
        request = MCPRequest(
            id="consistency-test-1",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        # Call multiple times
        response1 = await mcp_server.handle_request(request)

        request.id = "consistency-test-2"
        response2 = await mcp_server.handle_request(request)

        request.id = "consistency-test-3"
        response3 = await mcp_server.handle_request(request)

        # All should succeed
        assert_mcp_success_response(response1, "consistency-test-1")
        assert_mcp_success_response(response2, "consistency-test-2")
        assert_mcp_success_response(response3, "consistency-test-3")

        # Content should be identical
        content1 = response1.result["content"][0]["text"]
        content2 = response2.result["content"][0]["text"]
        content3 = response3.result["content"][0]["text"]

        assert content1 == content2, "Format list should be consistent between calls"
        assert content2 == content3, "Format list should be consistent between calls"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fast_response_time(self, mcp_server):
        """Test that format listing is fast."""
        import time

        request = MCPRequest(
            id="speed-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        start_time = time.time()
        response = await mcp_server.handle_request(request)
        end_time = time.time()

        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0, "Format listing should be fast"
        assert_mcp_success_response(response, "speed-test")


class TestListSupportedFormatsEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_extra_arguments(self, mcp_server):
        """Test behavior when extra arguments are provided."""
        request = MCPRequest(
            id="extra-args-test",
            method="tools/call",
            params={
                "name": "list_supported_formats",
                "arguments": {"unnecessary_arg": "should_be_ignored", "another_arg": 123},
            },
        )

        response = await mcp_server.handle_request(request)

        # Should succeed and ignore extra arguments
        assert_mcp_success_response(response, "extra-args-test")
        assert_list_formats_response(response)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_format_requests(self, mcp_server):
        """Test multiple concurrent format list requests."""
        import asyncio

        requests = [
            MCPRequest(
                id=f"concurrent-format-{i}",
                method="tools/call",
                params={"name": "list_supported_formats", "arguments": {}},
            )
            for i in range(5)
        ]

        # Send all requests concurrently
        responses = await asyncio.gather(*[mcp_server.handle_request(req) for req in requests])

        # All should succeed with identical content
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"concurrent-format-{i}")
            assert_list_formats_response(response)

        # Content should be identical across all responses
        base_content = responses[0].result["content"][0]["text"]
        for response in responses[1:]:
            content = response.result["content"][0]["text"]
            assert content == base_content, "Concurrent responses should be identical"


class TestListSupportedFormatsIntegration:
    """Test integration aspects with the actual supported extensions."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_format_list_matches_server_capabilities(self, mcp_server):
        """Test that listed formats match server's actual supported extensions."""
        request = MCPRequest(
            id="capability-match-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Get actual supported extensions from server
        server_extensions = mcp_server.supported_extensions

        # Listed extensions should include most of the server's supported extensions
        import re

        listed_extensions = set(re.findall(r"\.\w+", content_text))

        # At least 80% of server extensions should be listed
        overlap = len(server_extensions.intersection(listed_extensions))
        coverage_ratio = overlap / len(server_extensions) if server_extensions else 0

        assert coverage_ratio >= 0.8, (
            f"Format list should cover most supported extensions. "
            f"Coverage: {coverage_ratio:.2%}, Server: {server_extensions}, Listed: {listed_extensions}"
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_no_unsupported_formats_listed(self, mcp_server):
        """Test that no clearly unsupported formats are listed."""
        request = MCPRequest(
            id="unsupported-check-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"].lower()

        # These formats should NOT be listed as supported
        unsupported_formats = [
            ".exe",
            ".dll",
            ".so",
            ".bin",  # Executables
            ".iso",
            ".img",
            ".dmg",  # Disk images
            ".torrent",
            ".magnet",  # P2P
            ".key",
            ".pem",
            ".crt",  # Security files
        ]

        for fmt in unsupported_formats:
            assert (
                fmt not in content_text
            ), f"Unsupported format {fmt} should not be listed as supported"


class TestListSupportedFormatsOutput:
    """Test the output formatting and presentation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_output_is_well_formatted(self, mcp_server):
        """Test that the format list output is well-formatted."""
        request = MCPRequest(
            id="formatting-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Should be reasonably long and structured
        assert len(content_text) > 100, "Format list should be comprehensive"

        # Should have some structure (headers, lists, etc.)
        lines = content_text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) > 10, "Format list should have multiple lines of content"

        # Should contain some formatting characters
        formatting_chars = ["*", "-", "|", "#", ":"]
        has_formatting = any(char in content_text for char in formatting_chars)

        assert has_formatting, "Format list should have some formatting"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_output_is_readable(self, mcp_server):
        """Test that the output is human-readable."""
        request = MCPRequest(
            id="readability-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await mcp_server.handle_request(request)
        content_text = response.result["content"][0]["text"]

        # Should contain readable words
        readable_words = [
            "file",
            "format",
            "document",
            "support",
            "convert",
            "office",
            "image",
            "text",
            "data",
            "audio",
        ]

        words_found = sum(1 for word in readable_words if word.lower() in content_text.lower())

        assert (
            words_found >= 5
        ), f"Format list should be readable, found only {words_found} readable words"

        # Should not be just a raw list of extensions
        extension_chars = content_text.count(".")
        total_chars = len(content_text)
        extension_ratio = extension_chars / total_chars if total_chars > 0 else 0

        assert (
            extension_ratio < 0.1
        ), f"Format list should not be just extensions (ratio: {extension_ratio:.2%})"


class TestListSupportedFormatsMocking:
    """Test list_supported_formats with mocked dependencies."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_with_mock_supported_extensions(self, mcp_server):
        """Test format listing with mocked supported extensions."""
        # Mock the supported extensions
        mock_extensions = {".txt", ".json", ".pdf", ".docx", ".png"}

        with patch.object(mcp_server, "supported_extensions", mock_extensions):
            request = MCPRequest(
                id="mock-extensions-test",
                method="tools/call",
                params={"name": "list_supported_formats", "arguments": {}},
            )

            response = await mcp_server.handle_request(request)

            assert_mcp_success_response(response, "mock-extensions-test")
            content_text = response.result["content"][0]["text"]

            # All mocked extensions should appear in the output
            for ext in mock_extensions:
                assert ext in content_text, f"Mocked extension {ext} should appear in output"
