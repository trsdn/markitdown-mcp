#!/usr/bin/env python3
"""
Test data generator for MarkItDown MCP Server tests.
Creates sample files in all supported formats for comprehensive testing.
"""

import base64
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List


class TestDataGenerator:
    """Generate test files for all supported formats."""

    def __init__(self, fixtures_dir: Path):
        self.fixtures_dir = Path(fixtures_dir)
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.docs_dir = self.fixtures_dir / "documents"
        self.output_dir = self.fixtures_dir / "expected_outputs"
        self.malicious_dir = self.fixtures_dir / "malicious"

        for dir_path in [self.docs_dir, self.output_dir, self.malicious_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> Dict[str, List[str]]:
        """Generate all test files and return paths organized by category."""
        files = {
            "text": self._create_text_files(),
            "office": self._create_office_files(),
            "web": self._create_web_files(),
            "data": self._create_data_files(),
            "images": self._create_image_files(),
            "audio": self._create_audio_files(),
            "archives": self._create_archive_files(),
            "corrupted": self._create_corrupted_files(),
            "malicious": self._create_malicious_test_files(),
            "large": self._create_large_files(),
        }

        # Generate expected outputs
        self._create_expected_outputs()

        return files

    def _create_text_files(self) -> List[str]:
        """Create text format test files."""
        files = []
        text_dir = self.docs_dir / "text"
        text_dir.mkdir(exist_ok=True)

        # Plain text files
        files.append(
            self._create_file(
                text_dir / "simple.txt",
                "This is a simple text file.\nIt contains multiple lines.\n"
                "Perfect for testing basic conversion.",
            )
        )

        files.append(
            self._create_file(
                text_dir / "unicode.txt",
                "Unicode test: 你好世界 🌍 Héllo Wörld émojis and accénts\n"
                "Special characters: ®©™ ¼½¾ αβγδε\n"
                "Mathematical symbols: ∑∆∇√∞ ∈∉∀∃",
            )
        )

        files.append(self._create_file(text_dir / "empty.txt", ""))

        # Markdown files
        files.append(
            self._create_file(
                text_dir / "sample.md",
                """# Sample Markdown Document

## Introduction
This is a **bold** statement with *italic* text.

### Features
- List item 1
- List item 2
  - Nested item
  - Another nested item

### Code Example
```python
def hello_world():
    print("Hello, World!")
```

### Links and Images
[Link to example](https://example.com)

> This is a blockquote with important information.

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| A        | B        | C        |
| 1        | 2        | 3        |
""",
            )
        )

        # RST files
        files.append(
            self._create_file(
                text_dir / "sample.rst",
                """Sample reStructuredText Document
==================================

Introduction
------------

This is a sample reStructuredText document for testing purposes.

Features
~~~~~~~~

* List item 1
* List item 2

  * Nested item
  * Another nested item

Code Example::

    def hello_world():
        print("Hello, World!")

.. note::
   This is an important note.

.. warning::
   This is a warning message.
""",
            )
        )

        return files

    def _create_office_files(self) -> List[str]:
        """Create Office document test files (simplified versions)."""
        files = []
        office_dir = self.docs_dir / "office"
        office_dir.mkdir(exist_ok=True)

        # Note: These are simplified text-based representations
        # Real Office files would require libraries like python-docx, openpyxl

        # Create a simple text file that mimics office content
        files.append(
            self._create_file(
                office_dir / "document.docx.txt",
                "Sample Document\n\nThis represents the content of a Word document.\n\n"
                "Features:\n- Bold text\n- Italic text\n- Lists and tables\n\n"
                "Conclusion: This document demonstrates various formatting options.",
            )
        )

        files.append(
            self._create_file(
                office_dir / "presentation.pptx.txt",
                "Slide 1: Title Slide\nSample Presentation\nSubtitle goes here\n\n"
                "Slide 2: Content\n• Bullet point 1\n• Bullet point 2\n• Bullet point 3\n\n"
                "Slide 3: Conclusion\nThank you for your attention!",
            )
        )

        files.append(
            self._create_file(
                office_dir / "spreadsheet.xlsx.txt",
                "Name,Age,City\nJohn Doe,30,New York\nJane Smith,25,Los Angeles\n"
                "Bob Johnson,35,Chicago\n\nSummary:\nTotal Records: 3\nAverage Age: 30",
            )
        )

        return files

    def _create_web_files(self) -> List[str]:
        """Create web format test files."""
        files = []
        web_dir = self.docs_dir / "web"
        web_dir.mkdir(exist_ok=True)

        # HTML files
        files.append(
            self._create_file(
                web_dir / "simple.html",
                """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample HTML Document</title>
</head>
<body>
    <h1>Welcome to Our Website</h1>
    <p>This is a <strong>sample HTML document</strong> for testing purposes.</p>

    <h2>Features</h2>
    <ul>
        <li>Semantic HTML structure</li>
        <li>Proper heading hierarchy</li>
        <li>Lists and text formatting</li>
    </ul>

    <h3>Contact Information</h3>
    <p>Email: <a href="mailto:test@example.com">test@example.com</a></p>

    <blockquote>
        <p>"This is a sample blockquote to demonstrate various HTML elements."</p>
    </blockquote>
</body>
</html>""",
            )
        )

        # XML files
        xml_root = ET.Element("catalog")

        book1 = ET.SubElement(xml_root, "book", id="1")
        ET.SubElement(book1, "title").text = "Sample Book Title"
        ET.SubElement(book1, "author").text = "John Author"
        ET.SubElement(book1, "year").text = "2024"
        ET.SubElement(book1, "price").text = "29.99"

        book2 = ET.SubElement(xml_root, "book", id="2")
        ET.SubElement(book2, "title").text = "Another Book"
        ET.SubElement(book2, "author").text = "Jane Writer"
        ET.SubElement(book2, "year").text = "2023"
        ET.SubElement(book2, "price").text = "24.99"

        xml_content = ET.tostring(xml_root, encoding="unicode", xml_declaration=True)
        files.append(self._create_file(web_dir / "catalog.xml", xml_content))

        return files

    def _create_data_files(self) -> List[str]:
        """Create data format test files."""
        files = []
        data_dir = self.docs_dir / "data"
        data_dir.mkdir(exist_ok=True)

        # JSON files
        json_data = {
            "name": "Sample JSON Document",
            "version": "1.0",
            "description": "This is a sample JSON file for testing purposes",
            "features": ["JSON parsing", "Data structure validation", "Unicode support"],
            "metadata": {
                "created": "2024-01-01T00:00:00Z",
                "author": "Test Generator",
                "tags": ["test", "sample", "json"],
            },
            "numbers": [1, 2, 3, 4, 5],
            "boolean": True,
            "null_value": None,
        }

        files.append(
            self._create_file(
                data_dir / "sample.json", json.dumps(json_data, indent=2, ensure_ascii=False)
            )
        )

        # CSV files
        csv_content = "Name,Age,City,Salary,Department\n"
        csv_content += "John Doe,30,New York,75000,Engineering\n"
        csv_content += "Jane Smith,25,Los Angeles,65000,Marketing\n"
        csv_content += "Bob Johnson,35,Chicago,80000,Sales\n"
        csv_content += "Alice Brown,28,Boston,70000,Engineering\n"
        csv_content += "Charlie Davis,32,Seattle,90000,Engineering\n"

        files.append(self._create_file(data_dir / "employees.csv", csv_content))

        # CSV with special characters
        csv_special = "Product,Price,Description\n"
        csv_special += '"Coffee Mug",12.99,"A nice coffee mug with ""quotes"""\n'
        csv_special += "Laptop,999.99,High-performance laptop\n"
        csv_special += '"Notebook, Spiral",5.99,"Contains commas, and quotes"\n'

        files.append(self._create_file(data_dir / "products.csv", csv_special))

        return files

    def _create_image_files(self) -> List[str]:
        """Create image test files (minimal test images)."""
        files = []
        image_dir = self.docs_dir / "images"
        image_dir.mkdir(exist_ok=True)

        # Create minimal PNG (1x1 pixel red dot)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwA"
            "DhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        files.append(self._create_binary_file(image_dir / "test.png", png_data))

        # Create minimal JPEG (valid 1x1 pixel image)
        jpeg_data = base64.b64decode(
            "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
            "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEB"
            "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDAREA"
            "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
            "AQAAAAAAAAAAAAAAAAAAAAAAv/8QAFBEBAAAAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCx"
            "AA=="
        )
        files.append(self._create_binary_file(image_dir / "test.jpg", jpeg_data))

        # Create a simple GIF (1x1 transparent pixel)
        gif_data = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")
        files.append(self._create_binary_file(image_dir / "test.gif", gif_data))

        return files

    def _create_audio_files(self) -> List[str]:
        """Create audio test files (minimal audio files)."""
        files = []
        audio_dir = self.docs_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        # Create placeholder audio files (actual audio would require complex binary data)
        files.append(
            self._create_file(
                audio_dir / "speech.wav.txt",
                "Audio transcript: Hello world, this is a test audio file for "
                "speech recognition testing.",
            )
        )

        files.append(
            self._create_file(
                audio_dir / "music.mp3.txt",
                "Audio metadata: Song Title - Artist Name - Album: Test Album (2024)",
            )
        )

        return files

    def _create_archive_files(self) -> List[str]:
        """Create archive test files."""
        files = []
        archive_dir = self.docs_dir / "archives"
        archive_dir.mkdir(exist_ok=True)

        # Create a ZIP file with multiple files
        zip_path = archive_dir / "sample.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "This is a readme file inside the ZIP archive.")
            zf.writestr("data.json", '{"message": "Hello from inside ZIP"}')
            zf.writestr("subfolder/nested.txt", "This file is in a subfolder.")

        files.append(str(zip_path))
        return files

    def _create_corrupted_files(self) -> List[str]:
        """Create intentionally corrupted files for error handling tests."""
        files = []
        corrupted_dir = self.docs_dir / "corrupted"
        corrupted_dir.mkdir(exist_ok=True)

        # Corrupted JSON
        files.append(
            self._create_file(corrupted_dir / "invalid.json", '{"incomplete": "json", "missing":')
        )

        # Corrupted CSV
        files.append(
            self._create_file(
                corrupted_dir / "malformed.csv", 'Name,Age\n"Unclosed quote,25\nNormal Name,30'
            )
        )

        # Corrupted XML
        files.append(
            self._create_file(
                corrupted_dir / "broken.xml", '<?xml version="1.0"?><root><unclosed>content'
            )
        )

        # Fake PDF (not actually PDF format)
        files.append(
            self._create_file(
                corrupted_dir / "fake.pdf",
                "This is not a real PDF file, just plain text pretending to be one.",
            )
        )

        return files

    def _create_malicious_test_files(self) -> List[str]:
        """Create safe test files for security testing."""
        files = []

        # Path traversal test filenames (safe content)
        traversal_names = [
            "normal_file.txt",
            "..%2f..%2f..%2fetc%2fpasswd",
            "....//....//....//etc//passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for name in traversal_names:
            # Create safe filename and safe content
            safe_name = name.replace("/", "_").replace("\\", "_").replace("%", "_")
            files.append(
                self._create_file(
                    self.malicious_dir / f"path_traversal_{safe_name}",
                    f"Safe test content for security testing: {name}",
                )
            )

        # Large file for DoS testing (1MB of repeating content)
        large_content = "A" * 1024 * 1024  # 1MB
        files.append(self._create_file(self.malicious_dir / "large_dos_test.txt", large_content))

        return files

    def _create_large_files(self) -> List[str]:
        """Create large files for performance testing."""
        files = []
        large_dir = self.docs_dir / "large"
        large_dir.mkdir(exist_ok=True)

        # 10MB text file
        large_text = "This is line number {}\n" * 500000  # ~10MB
        files.append(
            self._create_file(large_dir / "large_text_10mb.txt", large_text.format(*range(500000)))
        )

        # Large JSON file (1MB)
        large_json_data = {
            "records": [
                {
                    "id": i,
                    "name": f"Record {i}",
                    "description": f"This is a long description for record {i} " * 10,
                    "metadata": {
                        "created": "2024-01-01T00:00:00Z",
                        "tags": [f"tag{j}" for j in range(5)],
                    },
                }
                for i in range(1000)
            ]
        }

        files.append(
            self._create_file(
                large_dir / "large_data_1mb.json", json.dumps(large_json_data, indent=2)
            )
        )

        return files

    def _create_expected_outputs(self):
        """Create expected output files for deterministic tests."""
        # Simple text conversion expected output
        self._create_file(
            self.output_dir / "simple_txt_expected.md",
            "This is a simple text file.\nIt contains multiple lines.\n"
            "Perfect for testing basic conversion.",
        )

        # JSON conversion expected output
        self._create_file(
            self.output_dir / "sample_json_expected.md",
            """```json
{
  "name": "Sample JSON Document",
  "version": "1.0",
  "description": "This is a sample JSON file for testing purposes",
  "features": [
    "JSON parsing",
    "Data structure validation",
    "Unicode support"
  ]
}
```""",
        )

        # CSV conversion expected output
        self._create_file(
            self.output_dir / "employees_csv_expected.md",
            """| Name | Age | City | Salary | Department |
|------|-----|------|--------|------------|
| John Doe | 30 | New York | 75000 | Engineering |
| Jane Smith | 25 | Los Angeles | 65000 | Marketing |
| Bob Johnson | 35 | Chicago | 80000 | Sales |
| Alice Brown | 28 | Boston | 70000 | Engineering |
| Charlie Davis | 32 | Seattle | 90000 | Engineering |""",
        )

    def _create_file(self, path: Path, content: str) -> str:
        """Create a text file with given content."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _create_binary_file(self, path: Path, content: bytes) -> str:
        """Create a binary file with given content."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)


def main():
    """Generate all test data."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    generator = TestDataGenerator(fixtures_dir)

    print("Generating test data...")
    files = generator.generate_all()

    total_files = sum(len(file_list) for file_list in files.values())
    print(f"Generated {total_files} test files in the following categories:")

    for category, file_list in files.items():
        print(f"  {category}: {len(file_list)} files")

    print(f"\nAll test data saved to: {fixtures_dir}")


if __name__ == "__main__":
    main()
