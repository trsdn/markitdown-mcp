"""
End-to-end file conversion integration tests.
Tests actual file conversion with real MarkItDown library.
"""

from pathlib import Path

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import (
    assert_convert_file_response,
    assert_mcp_success_response,
)


class TestFileConversionIntegration:
    """Test end-to-end file conversion with real files."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_text_file_conversion_end_to_end(self, temp_dir):
        """Test complete text file conversion flow."""
        server = MarkItDownMCPServer()

        # Create test file with various text features
        test_content = """# Sample Document

This is a **test document** with various formatting:

## Features
- Lists
- *Italic text*
- **Bold text**
- `Code snippets`

### Code Block
```
function hello() {
    console.log("Hello, World!");
}
```

> This is a blockquote for testing.

Link: [GitHub](https://github.com)

---

End of document.
"""

        test_file = Path(temp_dir) / "sample.md"
        test_file.write_text(test_content)

        # Convert the file
        request = MCPRequest(
            id="text-conversion-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "Sample Document", "sample.md")

        # Verify content preservation
        result_text = response.result["content"][0]["text"]
        assert "test document" in result_text
        assert "Features" in result_text
        assert "blockquote" in result_text
        assert "GitHub" in result_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_json_file_conversion_end_to_end(self, temp_dir):
        """Test complete JSON file conversion flow."""
        server = MarkItDownMCPServer()

        # Create complex JSON file
        json_content = """{
  "api": {
    "name": "MarkItDown MCP Server",
    "version": "1.0.0",
    "description": "Document conversion API"
  },
  "features": [
    {
      "name": "File Conversion",
      "supported_formats": ["pdf", "docx", "txt", "json", "csv"],
      "description": "Convert documents to Markdown"
    },
    {
      "name": "Directory Processing", 
      "batch_processing": true,
      "description": "Process multiple files at once"
    }
  ],
  "configuration": {
    "max_file_size": "100MB",
    "concurrent_requests": 10,
    "supported_languages": ["en", "es", "fr", "de"]
  },
  "metadata": {
    "created": "2024-01-01T00:00:00Z",
    "last_updated": null,
    "author": "Test Suite"
  }
}"""

        json_file = Path(temp_dir) / "config.json"
        json_file.write_text(json_content)

        # Convert the JSON file
        request = MCPRequest(
            id="json-conversion-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(json_file)}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "MarkItDown MCP Server", "config.json")

        # Verify JSON structure is preserved in converted text
        result_text = response.result["content"][0]["text"]
        assert "MarkItDown MCP Server" in result_text
        assert "File Conversion" in result_text
        assert "supported_formats" in result_text
        assert "100MB" in result_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_csv_file_conversion_end_to_end(self, temp_dir):
        """Test complete CSV file conversion flow."""
        server = MarkItDownMCPServer()

        # Create CSV with various data types
        csv_content = """Name,Age,Department,Salary,Start Date,Active
John Doe,30,Engineering,85000.50,2020-01-15,true
Jane Smith,28,"Marketing & Sales",72000.00,2021-03-22,true
Bob Johnson,35,Engineering,95000.00,2019-07-10,true
Alice Brown,26,HR,55000.25,2022-01-03,true
Charlie Davis,42,"Engineering, Senior",125000.00,2018-05-14,false
Emma Wilson,29,Marketing,68000.75,2021-09-08,true
"""

        csv_file = Path(temp_dir) / "employees.csv"
        csv_file.write_text(csv_content)

        # Convert the CSV file
        request = MCPRequest(
            id="csv-conversion-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(csv_file)}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "John Doe", "employees.csv")

        # Verify CSV data is preserved
        result_text = response.result["content"][0]["text"]
        assert "Jane Smith" in result_text
        assert "Engineering" in result_text
        assert "85000" in result_text
        assert "Marketing" in result_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_html_file_conversion_end_to_end(self, temp_dir):
        """Test complete HTML file conversion flow."""
        server = MarkItDownMCPServer()

        # Create HTML file with various elements
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sample HTML Page</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .highlight { background-color: yellow; }
    </style>
</head>
<body>
    <header>
        <h1>Welcome to Our Website</h1>
        <nav>
            <ul>
                <li><a href="#about">About</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="about">
            <h2>About Us</h2>
            <p>We are a <em>leading provider</em> of <strong>document conversion services</strong>.</p>
            <p class="highlight">Our mission is to make document processing simple and efficient.</p>
        </section>
        
        <section id="services">
            <h2>Our Services</h2>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Description</th>
                        <th>Price</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>PDF Conversion</td>
                        <td>Convert PDF files to various formats</td>
                        <td>$10/file</td>
                    </tr>
                    <tr>
                        <td>Batch Processing</td>
                        <td>Process multiple files simultaneously</td>
                        <td>$50/batch</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <section id="contact">
            <h2>Contact Information</h2>
            <form>
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
                
                <label for="email">Email:</label>
                <input type="email" id="email" name="email" required>
                
                <label for="message">Message:</label>
                <textarea id="message" name="message" rows="4" required></textarea>
                
                <button type="submit">Send Message</button>
            </form>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 Document Conversion Services. All rights reserved.</p>
    </footer>
    
    <script>
        console.log("Page loaded successfully");
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Thank you for your message!');
        });
    </script>
</body>
</html>"""

        html_file = Path(temp_dir) / "webpage.html"
        html_file.write_text(html_content)

        # Convert the HTML file
        request = MCPRequest(
            id="html-conversion-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(html_file)}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "Welcome to Our Website", "webpage.html")

        # Verify HTML content is extracted
        result_text = response.result["content"][0]["text"]
        assert "About Us" in result_text
        assert "leading provider" in result_text
        assert "PDF Conversion" in result_text
        assert "Contact Information" in result_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_xml_file_conversion_end_to_end(self, temp_dir):
        """Test complete XML file conversion flow."""
        server = MarkItDownMCPServer()

        # Create XML file with various elements
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<bookstore>
    <book id="1" category="fiction">
        <title lang="en">The Great Gatsby</title>
        <author>F. Scott Fitzgerald</author>
        <year>1925</year>
        <price currency="USD">12.99</price>
        <description>
            A classic American novel set in the summer of 1922.
            The story is narrated by Nick Carraway.
        </description>
        <tags>
            <tag>classic</tag>
            <tag>american literature</tag>
            <tag>1920s</tag>
        </tags>
    </book>
    
    <book id="2" category="science">
        <title lang="en">A Brief History of Time</title>
        <author>Stephen Hawking</author>
        <year>1988</year>
        <price currency="USD">15.99</price>
        <description>
            A popular science book on cosmology by physicist Stephen Hawking.
        </description>
        <tags>
            <tag>science</tag>
            <tag>cosmology</tag>
            <tag>physics</tag>
        </tags>
    </book>
    
    <metadata>
        <catalog_version>2.1</catalog_version>
        <last_updated>2024-01-01</last_updated>
        <total_books>2</total_books>
    </metadata>
</bookstore>"""

        xml_file = Path(temp_dir) / "bookstore.xml"
        xml_file.write_text(xml_content)

        # Convert the XML file
        request = MCPRequest(
            id="xml-conversion-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(xml_file)}},
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "Great Gatsby", "bookstore.xml")

        # Verify XML content is preserved
        result_text = response.result["content"][0]["text"]
        assert "F. Scott Fitzgerald" in result_text
        assert "Stephen Hawking" in result_text
        assert "1925" in result_text
        assert "cosmology" in result_text


class TestDirectoryConversionIntegration:
    """Test end-to-end directory conversion with real files."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_directory_conversion_mixed_files(self, temp_dir):
        """Test directory conversion with mixed file types."""
        server = MarkItDownMCPServer()

        # Create directory structure with various files
        source_dir = Path(temp_dir) / "mixed_docs"
        source_dir.mkdir()

        output_dir = Path(temp_dir) / "converted_output"
        output_dir.mkdir()

        # Create various file types
        files_created = {
            "readme.txt": "# Project README\n\nThis is a sample project.",
            "config.json": '{"name": "project", "version": "1.0"}',
            "data.csv": "Name,Value\nSetting1,100\nSetting2,200",
            "info.html": "<html><body><h1>Information</h1><p>Details here.</p></body></html>",
            "notes.md": "## Notes\n\n- Important point 1\n- Important point 2",
        }

        for filename, content in files_created.items():
            file_path = source_dir / filename
            file_path.write_text(content)

        # Convert directory
        request = MCPRequest(
            id="dir-mixed-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(source_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "dir-mixed-test")

        # Verify conversion results
        result_text = response.result["content"][0]["text"]
        assert "Successfully converted: 5" in result_text
        assert "Failed conversions: 0" in result_text

        # Verify output files exist
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 5

        # Check specific conversions
        readme_output = output_dir / "readme.md"
        assert readme_output.exists()
        readme_content = readme_output.read_text()
        assert "Project README" in readme_content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nested_directory_conversion(self, temp_dir):
        """Test directory conversion with nested structure."""
        server = MarkItDownMCPServer()

        # Create nested directory structure
        base_dir = Path(temp_dir) / "nested_project"
        base_dir.mkdir()

        # Create subdirectories
        (base_dir / "docs").mkdir()
        (base_dir / "data" / "config").mkdir(parents=True)
        (base_dir / "scripts").mkdir()

        # Create files in different locations
        files = {
            "README.txt": "Main project README",
            "docs/guide.md": "# User Guide\n\nInstructions here.",
            "docs/api.txt": "API Documentation\n\nEndpoints and usage.",
            "data/settings.json": '{"debug": true, "port": 8080}',
            "data/config/app.json": '{"name": "MyApp", "env": "production"}',
            "scripts/deploy.txt": "Deployment script documentation",
        }

        for rel_path, content in files.items():
            file_path = base_dir / rel_path
            file_path.write_text(content)

        output_dir = Path(temp_dir) / "nested_output"

        # Convert nested directory
        request = MCPRequest(
            id="nested-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(base_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "nested-dir-test")

        # Verify all files were processed
        result_text = response.result["content"][0]["text"]
        assert "Successfully converted: 6" in result_text

        # Verify nested structure is preserved
        assert (output_dir / "README.md").exists()
        assert (output_dir / "docs" / "guide.md").exists()
        assert (output_dir / "docs" / "api.md").exists()
        assert (output_dir / "data" / "settings.md").exists()
        assert (output_dir / "data" / "config" / "app.md").exists()
        assert (output_dir / "scripts" / "deploy.md").exists()


class TestBase64ConversionIntegration:
    """Test end-to-end base64 content conversion."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_base64_text_conversion_end_to_end(self):
        """Test complete base64 text conversion flow."""
        server = MarkItDownMCPServer()

        # Create content to encode
        original_content = """# Base64 Test Document

This document tests base64 encoding and decoding.

## Features
- Unicode support: 你好 🌍
- Special characters: ®©™
- Code blocks:

```python
def hello():
    print("Hello from base64!")
```

End of test document.
"""

        # Encode content
        import base64

        encoded_content = base64.b64encode(original_content.encode("utf-8")).decode("ascii")

        # Convert via base64
        request = MCPRequest(
            id="base64-text-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "base64_test.md"},
            },
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "Base64 Test Document", "base64_test.md")

        # Verify content preservation
        result_text = response.result["content"][0]["text"]
        assert "Unicode support" in result_text
        assert "你好 🌍" in result_text
        assert "Special characters" in result_text
        assert "Hello from base64!" in result_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_base64_json_conversion_end_to_end(self):
        """Test complete base64 JSON conversion flow."""
        server = MarkItDownMCPServer()

        # Create JSON content
        json_content = """{
  "test": "base64 encoding",
  "unicode": "测试 🚀",
  "nested": {
    "array": [1, 2, 3],
    "object": {
      "key": "value"
    }
  },
  "special_chars": "quotes \\"test\\" and slashes \\\\"
}"""

        # Encode content
        import base64

        encoded_content = base64.b64encode(json_content.encode("utf-8")).decode("ascii")

        # Convert via base64
        request = MCPRequest(
            id="base64-json-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "test_data.json"},
            },
        )

        response = await server.handle_request(request)

        assert_convert_file_response(response, "base64 encoding", "test_data.json")

        # Verify JSON structure preservation
        result_text = response.result["content"][0]["text"]
        assert "测试 🚀" in result_text
        assert "nested" in result_text
        assert "array" in result_text
        assert "quotes" in result_text


class TestErrorScenariosIntegration:
    """Test error scenarios in real conversion contexts."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_corrupted_file_handling_integration(self, temp_dir):
        """Test handling of corrupted files in integration context."""
        server = MarkItDownMCPServer()

        # Create files with various corruption types
        corrupted_files = {
            "invalid.json": '{"incomplete": json without closing',
            "broken.csv": 'Name,Age\n"Unclosed quote,25\nValid,30',
            "fake.pdf": "This is not a PDF file at all, just text",
            "incomplete.html": "<html><body><h1>Missing closing tags",
        }

        results = []

        for filename, content in corrupted_files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)

            request = MCPRequest(
                id=f"corrupt-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(file_path)}},
            )

            response = await server.handle_request(request)
            results.append((filename, response))

        # Analyze results - some may succeed with partial conversion,
        # others may fail gracefully
        for filename, response in results:
            # Response should either succeed or fail gracefully
            assert response.result is not None or response.error is not None

            # If there's an error, it should be informative
            if response.error:
                error_msg = response.error["message"]
                # Error should not expose system internals
                assert "traceback" not in error_msg.lower()
                assert "exception" not in error_msg.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_permission_errors_integration(self, temp_dir):
        """Test handling of permission errors in integration context."""
        server = MarkItDownMCPServer()

        # Create a file and make it unreadable (if supported by OS)
        test_file = Path(temp_dir) / "restricted.txt"
        test_file.write_text("This file will be made unreadable")

        try:
            # Try to make file unreadable
            test_file.chmod(0o000)

            request = MCPRequest(
                id="permission-test",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)

            # Should handle permission error gracefully
            if response.error:
                error_msg = response.error["message"].lower()
                assert any(term in error_msg for term in ["permission", "access", "denied", "readable"])

        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except:
                pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_file_timeout_integration(self, temp_dir):
        """Test handling of very large files that might timeout."""
        server = MarkItDownMCPServer()

        # Create a very large text file (5MB)
        large_content = "This is a large file line.\n" * 250000  # ~5MB
        large_file = Path(temp_dir) / "very_large.txt"
        large_file.write_text(large_content)

        request = MCPRequest(
            id="large-file-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        # This might take a while or timeout
        response = await server.handle_request(request)

        # Should either succeed or fail gracefully
        assert response.result is not None or response.error is not None

        if response.result:
            # If successful, should contain expected content
            result_text = response.result["content"][0]["text"]
            assert "large file line" in result_text

        if response.error:
            # If failed, error should be reasonable
            error_msg = response.error["message"].lower()
            # Could be timeout, memory, or processing error
            acceptable_errors = ["timeout", "memory", "size", "large", "processing"]
            assert any(term in error_msg for term in acceptable_errors)
