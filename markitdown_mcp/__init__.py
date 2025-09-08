"""
MarkItDown MCP Server - A Model Context Protocol server for document conversion.

This package provides a Model Context Protocol (MCP) server that converts various
file formats to Markdown using Microsoft's MarkItDown library.

Supported formats include:
- Office documents (PDF, DOCX, PPTX, XLSX)
- Images with OCR (JPG, PNG, GIF, BMP, TIFF, WebP)
- Audio with speech recognition (MP3, WAV, FLAC, M4A, OGG, WMA)
- Web/markup files (HTML, HTM)
- Data formats (CSV, JSON, XML)
- Archives (ZIP) and e-books (EPUB)
- Text files (TXT, MD, RST)
"""

__version__ = "1.0.0"
__author__ = "MarkItDown MCP"
__email__ = "noreply@example.com"

from .server import MarkItDownMCPServer

__all__ = ["MarkItDownMCPServer"]
