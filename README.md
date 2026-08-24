# 📄 MarkItDown MCP Server

[![MCP](https://img.shields.io/badge/Model_Context_Protocol-MCP-blue)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/trsdn-markitdown-mcp.svg)](https://pypi.org/project/trsdn-markitdown-mcp/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/trsdn/markitdown-mcp/workflows/CI/badge.svg)](https://github.com/trsdn/markitdown-mcp/actions)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

A powerful **Model Context Protocol (MCP) server** that converts 29+ file formats to clean, structured Markdown using Microsoft's MarkItDown library.

> [!IMPORTANT]
> **This is not Microsoft's official `markitdown-mcp` package.**
> This is an independent community project published on PyPI as
> **[`trsdn-markitdown-mcp`](https://pypi.org/project/trsdn-markitdown-mcp/)**.
> It *uses* Microsoft's [`markitdown`](https://pypi.org/project/markitdown/) library as a
> dependency, but it is developed and maintained separately from
> [`markitdown-mcp`](https://pypi.org/project/markitdown-mcp/) by Microsoft.
>
> - **PyPI distribution name**: `trsdn-markitdown-mcp`
> - **Python import name**: `markitdown_mcp`
> - **CLI command**: `markitdown-mcp` (alias: `trsdn-markitdown-mcp`)


🔥 **Perfect for Claude Desktop, MCP clients, and AI workflows!** 

## ✨ Features

- 🔌 **MCP Protocol**: Seamless integration with Claude Desktop and MCP clients
- 📁 **29+ File Formats**: PDFs, Office docs, images, audio, archives, and more
- 🔍 **Image Metadata**: Extract EXIF metadata from images (JPG, PNG, GIF, etc.)
- 🎵 **Speech Recognition**: Convert audio to text with speech transcription (MP3, WAV)*

*_Requires `markitdown[all]` installation for full functionality_

### 📦 Dependency Requirements by File Type

| File Type | Required Dependencies | Install Command |
|-----------|----------------------|-----------------|
| **PDF** | `pypdf`, `pymupdf`, `pdfplumber` | `pipx inject trsdn-markitdown-mcp 'markitdown[all]'` |
| **Excel (.xlsx, .xls)** | `openpyxl`, `xlrd`, `pandas` | `pipx inject trsdn-markitdown-mcp openpyxl xlrd pandas` |
| **PowerPoint (.pptx)** | `python-pptx` | Included in base install |
| **Images** | `PIL`, `exiftool` (optional) | Included in base install |
| **Audio** | `pydub`, `speech_recognition` | `pipx inject trsdn-markitdown-mcp 'markitdown[all]'` |
| **Basic formats** | None | Base install only |

**Note**: For the best experience, we recommend installing all dependencies using the **Complete Install** method below.
- 📊 **Office Documents**: Word, PowerPoint, Excel files
- 🌐 **Web Content**: HTML, XML, JSON, CSV
- 📚 **E-books & Archives**: EPUB, ZIP files
- ⚡ **Fast & Reliable**: Built on Microsoft's MarkItDown library

## 🚀 Quick Start for Claude Desktop

1. **Install the server with ALL features:**
   ```bash
   # One command to install everything
   pipx install trsdn-markitdown-mcp && \
   pipx inject trsdn-markitdown-mcp 'markitdown[all]' openpyxl xlrd pandas pymupdf pdfplumber
   ```

2. **Add to your Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "markitdown": {
         "command": "markitdown-mcp",
         "args": []
       }
     }
   }
   ```

3. **Restart Claude Desktop** and start converting files!

## Features

- Convert multiple file formats to Markdown
- Batch processing of entire directories
- Preserves directory structure in output
- Environment variable support via .env file

## 📋 Available MCP Tools

### 🔧 `convert_file`
Convert a single file to Markdown.
```json
{
  "name": "convert_file",
  "arguments": {
    "file_path": "/path/to/document.pdf"
  }
}
```

### 📋 `list_supported_formats`
Get a complete list of supported file formats.
```json
{
  "name": "list_supported_formats",
  "arguments": {}
}
```

### 📁 `convert_directory`
Convert all supported files in a directory.
```json
{
  "name": "convert_directory", 
  "arguments": {
    "input_directory": "/path/to/files",
    "output_directory": "/path/to/markdown" 
  }
}
```

## 📄 Supported File Formats (29+)

| Category | Extensions | Features |
|----------|------------|----------|
| **📊 Office** | `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls` | Full document structure |
| **🖼️ Images** | `.jpg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp` | EXIF metadata extraction |
| **🎵 Audio** | `.mp3`, `.wav` | Speech-to-text transcription |
| **🌐 Web** | `.html`, `.htm`, `.xml`, `.json`, `.csv` | Clean formatting |
| **📚 Books** | `.epub` | Chapter extraction |
| **📦 Archives** | `.zip` | Auto-extract and process |
| **📝 Text** | `.txt`, `.md`, `.rst` | Direct conversion |

## Installation

> Published on PyPI as **`trsdn-markitdown-mcp`** — not to be confused with Microsoft's `markitdown-mcp`.

### Option 1: Install from PyPI (Recommended)

```bash
# Isolated install with pipx
pipx install trsdn-markitdown-mcp

# Or with pip
pip install trsdn-markitdown-mcp

# Or run without installing (uv)
uvx trsdn-markitdown-mcp
```

### Option 2: Install from source (development)

```bash
git clone https://github.com/trsdn/markitdown-mcp.git
cd markitdown-mcp
pip install -e ".[all]"
```

### Option 3: Direct usage from a checkout

```bash
cd markitdown-mcp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

### MCP Server Mode (Recommended)

After installation:
```bash
# Start the MCP server (for use with MCP clients)
markitdown-mcp

# Equivalent alternatives
trsdn-markitdown-mcp
python -m markitdown_mcp
```

## 🛠️ Installation Options

### 🚀 One-Command Install (Recommended)
Install with ALL dependencies in one command:
```bash
# Using pipx (recommended)
pipx install trsdn-markitdown-mcp && \
pipx inject trsdn-markitdown-mcp 'markitdown[all]' openpyxl xlrd pandas pymupdf pdfplumber pytesseract pydub speechrecognition

# Or download and run the install script
curl -sSL https://raw.githubusercontent.com/trsdn/markitdown-mcp/main/scripts/install-all-deps.sh | bash
```

### Quick Install (Basic Features Only)
```bash
pip install trsdn-markitdown-mcp
```

### Complete Install with All Dependencies (Step by Step)

To ensure all file formats are supported, use one of these methods:

#### Method 1: Using pipx (Recommended)
```bash
# Install the MCP server
pipx install trsdn-markitdown-mcp

# Install all required dependencies for full functionality
pipx inject trsdn-markitdown-mcp 'markitdown[all]'         # PDF, OCR, Speech
pipx inject trsdn-markitdown-mcp openpyxl xlrd pandas      # Excel support
pipx inject trsdn-markitdown-mcp pymupdf pdfplumber        # Advanced PDF
```

#### Method 2: Using pip with virtual environment
```bash
# Create and activate virtual environment
python -m venv markitdown-env
source markitdown-env/bin/activate  # On Windows: markitdown-env\Scripts\activate

# Install with all dependencies in one command
git clone https://github.com/trsdn/markitdown-mcp.git
cd markitdown-mcp
pip install -e ".[all]"  # This installs everything!
```

#### Method 3: For Claude Desktop with existing installation
If you already have the MCP server installed but some formats aren't working:
```bash
# Find your installation
which markitdown-mcp  # Shows path like /Users/you/.local/bin/markitdown-mcp

# Inject missing dependencies
pipx inject trsdn-markitdown-mcp 'markitdown[all]' openpyxl xlrd pandas pymupdf pdfplumber
```

### Verify Installation
After installation, verify the server responds to MCP requests:
```bash
# Ask the server for its tool list over stdio (JSON-RPC)
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | markitdown-mcp

# For pipx installations, check injected packages
pipx list --include-injected
```

## 🔧 Claude Desktop Configuration

Add this to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "markitdown-mcp",
      "args": []
    }
  }
}
```

Prefer running it without a permanent install? Use `uvx` (the package name is
`trsdn-markitdown-mcp`, the command is `markitdown-mcp`):

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "uvx",
      "args": ["trsdn-markitdown-mcp"]
    }
  }
}
```

**Config file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## 💡 Usage Examples

### Convert a PDF
```
Convert the file ~/Documents/report.pdf to markdown
```

### Batch Process Directory
```
Convert all files in ~/Downloads/documents/ to markdown
```

### Check Supported Formats
```
What file formats can you convert to markdown?
```

## 🔍 Troubleshooting

### Missing Dependencies Errors
If you see errors like:
- `PdfConverter threw MissingDependencyException`
- `XlsxConverter threw MissingDependencyException`
- `PptxConverter threw BadZipFile`

This means some optional dependencies are missing. Follow the **Complete Install** instructions above.

### Unicode Errors with .md Files
Some Markdown files with special characters may fail with `UnicodeDecodeError`. This is a known limitation in the MarkItDown library.

### Installation Issues
- **"externally-managed-environment" error**: Use pipx instead of pip
- **Permission denied**: Never use sudo with pip; use pipx or virtual environments
- **Command not found**: Make sure `~/.local/bin` is in your PATH

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for more details.

## Configuration

No special configuration required. The tool uses the MarkItDown library for document conversion.

## Usage

### Basic Usage

```bash
# Convert all supported files from input/ to output/
python mdconvert.py
```

### Custom Directories

Specify custom input and output directories:
```bash
python mdconvert.py --input /path/to/docs --output /path/to/markdown
```

### Single File Conversion

Convert a single file:
```bash
python mdconvert.py --file document.pdf
```

## Command Line Options

- `--input, -i`: Input directory (default: `input`)
- `--output, -o`: Output directory (default: `output`)
- `--file, -f`: Convert a single file instead of a directory

## MCP Server Features

The MCP server provides three tools:

### 1. convert_file
Convert a single file to Markdown.
- **Input**: File path or base64 encoded content with filename
- **Output**: Converted Markdown content

### 2. list_supported_formats
List all supported file formats.
- **Output**: Categorized list of supported file extensions

### 3. convert_directory
Convert all supported files in a directory.
- **Input**: Input directory path, optional output directory
- **Output**: Summary of conversion results

## Directory Structure

```
markitdown-mcp/
├── mcp_server.py        # MCP protocol server
├── mdconvert.py         # CLI script
├── mcp_config.json      # MCP configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── input/              # Default input directory
├── output/             # Default output directory
└── venv/               # Virtual environment
```

## 🔍 How It Works

This MCP server leverages Microsoft's MarkItDown library to provide intelligent document conversion:

- **📄 PDFs**: Extracts text, tables, and structure
- **🖼️ Images**: Uses OCR to extract text content + EXIF metadata  
- **🎵 Audio**: Converts speech to text transcription (MP3, WAV)
- **📊 Office**: Preserves formatting from Word, Excel, PowerPoint
- **🌐 HTML**: Converts to clean, readable Markdown
- **📦 Archives**: Automatically extracts and processes contents

## 🏷️ Tags

`mcp` `model-context-protocol` `claude-desktop` `markdown` `document-conversion` `pdf` `ocr` `speech-to-text` `markitdown` `ai-tools`

## 📋 Requirements

- **Python**: 3.10+
- **MCP Client**: Claude Desktop or compatible MCP client
- **Dependencies**: Automatically installed via pip

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🚀 Quick Start for Contributors
```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/markitdown-mcp.git
cd markitdown-mcp

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Test your changes
markitdown-mcp  # Test the server works
```

### 📝 Ways to Contribute
- 🐛 **Bug Reports**: Found an issue? [Report it](https://github.com/trsdn/markitdown-mcp/issues/new?template=bug_report.yml)
- 💡 **Feature Requests**: Have an idea? [Suggest it](https://github.com/trsdn/markitdown-mcp/issues/new?template=feature_request.yml)  
- 📄 **New File Formats**: Add support for more file types
- 📚 **Documentation**: Improve guides and examples
- 🧪 **Testing**: Add tests and improve reliability
- 🎨 **Code Quality**: Refactor and optimize

### 📋 Contribution Process
1. Read our [Contributing Guide](docs/development/CONTRIBUTING.md)
2. Check [existing issues](https://github.com/trsdn/markitdown-mcp/issues)
3. Fork the repository
4. Create a feature branch (`feat/amazing-feature`)
5. Make your changes with tests
6. Submit a pull request

**Please read [docs/development/CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for detailed guidelines.**

## 📚 Documentation

### For Users
- **[Examples](examples/)** - MCP client configuration examples
- **[Known Issues](docs/guides/KNOWN_ISSUES.md)** - Common problems and solutions
- **[Changelog](CHANGELOG.md)** - Version history and updates

### For AI Agents
- **[AGENTS.md](AGENTS.md)** - Comprehensive guide for AI agent integration
- **[API Documentation](docs/api/)** - Technical specifications and tool details

### For Developers
- **[Contributing Guide](docs/development/CONTRIBUTING.md)** - How to contribute
- **[Testing Strategy](docs/development/TESTING_STRATEGY.md)** - Testing approach and guidelines
- **[Documentation](docs/)** - Complete documentation index

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Claude Desktop](https://claude.ai/)  
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown)# Test workflow fixes
# Test fix verification
