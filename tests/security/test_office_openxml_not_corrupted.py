"""Regression tests for Office Open XML (.docx/.xlsx/.pptx) handling.

These formats are ZIP archives whose MIME type contains the substring "xml"
(``application/vnd.openxmlformats-...``). A previous version routed them through
the text-based XML sanitizer, which read the binary ZIP as UTF-8 and wrote a
corrupted copy to a ``.xml`` temp file, causing ``BadZipFile`` downstream.

See: convert_file failing with a generic "Conversion failed" for valid .docx.
"""

import zipfile
from pathlib import Path

import pytest

from markitdown_mcp.server import validate_file_content_security


def _make_minimal_ooxml(path: Path) -> None:
    """Write a minimal but structurally valid Office Open XML (ZIP) file."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        zf.writestr("word/document.xml", "<document>hello</document>")


@pytest.mark.parametrize("ext", [".docx", ".xlsx", ".pptx"])
def test_ooxml_not_routed_through_xml_sanitizer(temp_dir, ext):
    """A ZIP-based office file must survive security validation as a valid ZIP."""
    src = Path(temp_dir) / f"sample{ext}"
    _make_minimal_ooxml(src)
    assert zipfile.is_zipfile(src)  # sanity: input really is a zip

    validated = validate_file_content_security(str(src))

    # The validator must not rewrite the binary file into a corrupted .xml temp.
    assert validated == str(src), "office file should not be rerouted to a sanitized temp file"
    # The core regression: the file the converter receives is still a valid ZIP.
    assert zipfile.is_zipfile(validated), "office ZIP was corrupted by the XML sanitizer"


def test_real_xml_still_sanitized(temp_dir):
    """Genuine .xml files must still be routed through the XML sanitizer."""
    src = Path(temp_dir) / "data.xml"
    src.write_text("<root><a>hi</a></root>", encoding="utf-8")

    validated = validate_file_content_security(str(src))

    # Sanitizer returns a *new* temp path for real XML input.
    assert validated != str(src)
    assert validated.endswith(".xml")
