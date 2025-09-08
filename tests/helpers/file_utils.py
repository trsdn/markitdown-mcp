"""
File utilities for testing MarkItDown MCP Server
"""

import random
import shutil
import string
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union


def create_test_file(content: str, filename: str, temp_dir: Optional[str] = None) -> str:
    """Create a test file with specified content."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def create_binary_test_file(content: bytes, filename: str, temp_dir: Optional[str] = None) -> str:
    """Create a binary test file with specified content."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    return str(file_path)


def create_minimal_pdf(temp_dir: Optional[str] = None) -> str:
    """Create a minimal valid PDF file for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello PDF!) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000010 00000 n
0000000079 00000 n
0000000173 00000 n
0000000301 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
398
%%EOF"""
    return create_binary_test_file(pdf_content, "test.pdf", temp_dir)


def create_minimal_docx(temp_dir: Optional[str] = None) -> str:
    """Create a minimal DOCX file (ZIP format)."""
    import zipfile

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / "test.docx"

    # Create minimal DOCX structure
    with zipfile.ZipFile(file_path, "w") as docx:
        # Content types
        content_types = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
        docx.writestr("[Content_Types].xml", content_types)

        # Main document
        document = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Hello DOCX!</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>"""
        docx.writestr("word/document.xml", document)

    return str(file_path)


def create_minimal_xlsx(temp_dir: Optional[str] = None) -> str:
    """Create a minimal XLSX file."""
    import zipfile

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / "test.xlsx"

    with zipfile.ZipFile(file_path, "w") as xlsx:
        # Content types
        content_types = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
        xlsx.writestr("[Content_Types].xml", content_types)

        # Workbook
        workbook = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheets>
        <sheet name="Sheet1" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
    </sheets>
</workbook>"""
        xlsx.writestr("xl/workbook.xml", workbook)

        # Worksheet
        worksheet = """<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheetData>
        <row r="1">
            <c r="A1" t="inlineStr">
                <is><t>Hello XLSX!</t></is>
            </c>
        </row>
    </sheetData>
</worksheet>"""
        xlsx.writestr("xl/worksheets/sheet1.xml", worksheet)

    return str(file_path)


def create_test_image(width: int = 100, height: int = 100, temp_dir: Optional[str] = None) -> str:
    """Create a test image file with basic content."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        # Fallback: create a minimal PNG manually
        return create_minimal_png(temp_dir)

    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / "test_image.png"

    # Create simple test image
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Add some basic content
    draw.rectangle([10, 10, width - 10, height - 10], outline="black", width=2)
    draw.text((20, 20), "TEST", fill="black")

    img.save(file_path, "PNG")
    return str(file_path)


def create_minimal_png(temp_dir: Optional[str] = None) -> str:
    """Create a minimal valid PNG file."""
    # Minimal 1x1 white PNG
    png_content = bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,  # IHDR chunk size
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR
            0x00,
            0x00,
            0x00,
            0x01,  # width: 1
            0x00,
            0x00,
            0x00,
            0x01,  # height: 1
            0x08,
            0x02,
            0x00,
            0x00,
            0x00,  # bit depth, color type, etc.
            0x90,
            0x77,
            0x53,
            0xDE,  # CRC
            0x00,
            0x00,
            0x00,
            0x0C,  # IDAT chunk size
            0x49,
            0x44,
            0x41,
            0x54,  # IDAT
            0x08,
            0x99,
            0x01,
            0x01,
            0x00,
            0x00,
            0x00,
            0xFF,
            0xFF,
            0x00,
            0x00,
            0x00,
            0x02,
            0x00,
            0x01,
            0x73,
            0x75,
            0x01,
            0x18,  # CRC
            0x00,
            0x00,
            0x00,
            0x00,  # IEND chunk size
            0x49,
            0x45,
            0x4E,
            0x44,  # IEND
            0xAE,
            0x42,
            0x60,
            0x82,  # CRC
        ]
    )
    return create_binary_test_file(png_content, "minimal.png", temp_dir)


def create_corrupted_file(filename: str, temp_dir: Optional[str] = None) -> str:
    """Create a file with corrupted/invalid content."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / filename

    # Create corrupted content based on file extension
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        # Invalid PDF header
        content = b"%PDF-CORRUPTED\n%Invalid content"
    elif ext in [".docx", ".xlsx", ".pptx"]:
        # Invalid ZIP content
        content = b"PK\x03\x04CORRUPTED_ZIP_CONTENT"
    elif ext == ".json":
        # Invalid JSON
        content = b'{"invalid": json syntax missing quote}'
    elif ext == ".png":
        # Invalid PNG header
        content = b"\x89PNG\x0d\x0a\x1a\x0aCORRUPTED"
    else:
        # Generic corrupted binary content
        content = b"\x00\x01\x02\x03CORRUPTED\xff\xfe\xfd"

    file_path.write_bytes(content)
    return str(file_path)


def create_large_file(
    size_mb: int, filename: str = "large.txt", temp_dir: Optional[str] = None
) -> str:
    """Create a large file for performance testing."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    file_path = Path(temp_dir) / filename

    # Generate content
    line = "This is a line for large file testing. " * 10 + "\n"
    lines_needed = (size_mb * 1024 * 1024) // len(line.encode())

    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(lines_needed):
            f.write(f"Line {i}: {line}")

    return str(file_path)


def create_test_directory_structure(
    base_dir: Optional[str] = None,
) -> Dict[str, Union[str, List[str]]]:
    """Create a complex directory structure for testing."""
    if base_dir is None:
        base_dir = tempfile.mkdtemp()

    base_path = Path(base_dir)

    # Create directory structure
    dirs = [
        "documents",
        "documents/pdf",
        "documents/office",
        "documents/text",
        "images",
        "data",
        "mixed",
        "empty_dir",
    ]

    for dir_path in dirs:
        (base_path / dir_path).mkdir(parents=True, exist_ok=True)

    # Create test files
    files_created = []

    # Text files
    text_files = [
        ("documents/text/readme.txt", "This is a readme file."),
        ("documents/text/notes.md", "# Notes\n\nSome markdown notes."),
        ("mixed/info.txt", "Mixed directory text file."),
    ]

    for file_path, content in text_files:
        full_path = base_path / file_path
        full_path.write_text(content, encoding="utf-8")
        files_created.append(str(full_path))

    # Data files
    data_files = [
        ("data/config.json", '{"app": "test", "version": "1.0"}'),
        ("data/users.csv", "name,email\nJohn,john@test.com\nJane,jane@test.com"),
        ("mixed/sample.json", '{"mixed": true}'),
    ]

    for file_path, content in data_files:
        full_path = base_path / file_path
        full_path.write_text(content, encoding="utf-8")
        files_created.append(str(full_path))

    # Create binary files
    try:
        pdf_path = create_minimal_pdf(str(base_path / "documents/pdf"))
        files_created.append(pdf_path)

        docx_path = create_minimal_docx(str(base_path / "documents/office"))
        files_created.append(docx_path)

        image_path = create_test_image(temp_dir=str(base_path / "images"))
        files_created.append(image_path)
    except Exception:
        # Skip binary files if dependencies not available
        pass

    return {
        "base_directory": str(base_path),
        "files": files_created,
        "directories": [str(base_path / d) for d in dirs],
        "total_files": len(files_created),
    }


def generate_random_text(length: int) -> str:
    """Generate random text of specified length."""
    chars = string.ascii_letters + string.digits + " \n.,!?"
    return "".join(random.choices(chars, k=length))


def file_exists_and_readable(file_path: str) -> bool:
    """Check if file exists and is readable."""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and path.stat().st_size >= 0
    except Exception:
        return False


def get_file_info(file_path: str) -> Dict[str, Union[str, int]]:
    """Get basic file information."""
    path = Path(file_path)

    if not path.exists():
        return {"error": "File does not exist"}

    try:
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "extension": path.suffix,
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "readable": True,
        }
    except Exception as e:
        return {"error": str(e)}


def cleanup_temp_files(*file_paths: str) -> None:
    """Clean up temporary files and directories."""
    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except Exception:
            # Ignore cleanup errors
            pass
