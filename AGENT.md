# AI Agent Guide for MarkItDown MCP Server

## Repository Overview

**Purpose**: A Model Context Protocol (MCP) server that converts 29+ file formats to Markdown using Microsoft's MarkItDown library.

**Target Use**: Integration with Claude Desktop and other MCP clients for document conversion workflows.

**Status**: Active development, approaching release-ready state.

## Architecture

### Core Components

```
markitdown-mcp/
├── markitdown_mcp/           # Main package
│   ├── __init__.py          # Package initialization
│   └── server.py            # Core MCP server implementation
├── tests/                   # Test suite (planned)
├── README.md               # User documentation
├── AGENT.md               # This file - AI agent guide
├── TESTING_STRATEGY.md    # Comprehensive testing plan
├── KNOWN_ISSUES.md        # Current limitations
├── pyproject.toml         # Python package configuration
├── requirements.txt       # Core dependencies
├── requirements-all.txt   # All optional dependencies
└── install-all-deps.sh   # One-command installation script
```

### MCP Server Implementation

**File**: `markitdown_mcp/server.py`

**Key Classes**:
- `MCPRequest`: JSON-RPC request wrapper
- `MCPResponse`: JSON-RPC response wrapper  
- `MarkItDownMCPServer`: Main server class

**Key Methods**:
- `handle_request()`: Main request router
- `convert_file_tool()`: Single file conversion
- `list_supported_formats_tool()`: List supported formats
- `convert_directory_tool()`: Batch directory conversion

## MCP Protocol Implementation

### Supported Methods
1. `initialize` - Server initialization
2. `tools/list` - List available tools
3. `tools/call` - Execute tool functions

### Available Tools
1. **convert_file**: Convert single file to Markdown
   - Input: `file_path` OR `file_content` + `filename`
   - Output: Markdown content

2. **list_supported_formats**: List all supported file formats
   - Input: None
   - Output: Categorized format list

3. **convert_directory**: Convert all files in directory
   - Input: `input_directory`, optional `output_directory`
   - Output: Conversion summary with success/failure counts

## File Format Support

### Fully Supported (29+ formats)
- **Office**: PDF, DOCX, PPTX, XLSX, XLS
- **Images**: JPG, PNG, GIF, BMP, TIFF, WebP (metadata only, NO OCR)
- **Audio**: MP3, WAV, FLAC, M4A, OGG, WMA (speech recognition)
- **Web**: HTML, HTM, XML, JSON, CSV
- **Text**: TXT, MD, RST
- **Archives**: ZIP (auto-extract and process)
- **E-books**: EPUB

### Important Limitations
- **Images**: Only EXIF metadata extraction - NO OCR support
- **Audio**: Requires speech recognition dependencies
- **Office**: Excel/PowerPoint need additional dependencies

## Dependencies

### Core Requirements
```bash
markitdown>=0.1.0
pypdf>=3.17.0
python-pptx>=0.6.21
pillow>=10.0.0
python-magic>=0.4.27
pdf2image>=1.16.3
python-dotenv>=1.0.0
```

### Optional Dependencies for Full Support
```bash
# Excel support
openpyxl>=3.1.2
xlrd>=2.0.1
pandas>=2.0.0

# Advanced PDF
pymupdf>=1.23.0
pdfplumber>=0.10.0

# Audio support
pydub>=0.25.1
speechrecognition>=3.10.0
```

### Installation Commands
```bash
# One-command install (recommended)
pipx install git+https://github.com/trsdn/markitdown-mcp.git && \
pipx inject markitdown-mcp 'markitdown[all]' openpyxl xlrd pandas pymupdf pdfplumber

# Or use the install script
curl -sSL https://raw.githubusercontent.com/trsdn/markitdown-mcp/main/install-all-deps.sh | bash
```

## Development Workflow

### Local Development Setup
```bash
git clone https://github.com/trsdn/markitdown-mcp.git
cd markitdown-mcp
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[all]"
```

### Testing the Server
```bash
# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{}}' | markitdown-mcp

# Test conversion
markitdown-mcp  # Then send JSON-RPC requests
```

### Claude Desktop Integration
Add to `claude_desktop_config.json`:
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

## Common Tasks for AI Agents

### 1. Troubleshooting Installation Issues

**Missing Dependencies Error**:
```bash
# Install missing Excel/PowerPoint support
pipx inject markitdown-mcp openpyxl xlrd pandas

# Install missing PDF support  
pipx inject markitdown-mcp 'markitdown[all]' pymupdf pdfplumber
```

**Externally Managed Environment Error**:
- Use `pipx` instead of `pip`
- Or create virtual environment
- Never suggest `sudo pip install`

### 2. Adding New Features

**Before modifying code**:
1. Read `TESTING_STRATEGY.md` for testing approach
2. Check `KNOWN_ISSUES.md` for current limitations
3. Understand MCP protocol requirements

**Key files to modify**:
- `markitdown_mcp/server.py` - Main implementation
- `pyproject.toml` - Dependencies and metadata
- `README.md` - User documentation
- Tests - Follow testing strategy

### 3. Debugging Conversion Issues

**Common issues**:
1. **Empty Markdown output**: Check if dependencies are installed
2. **Unicode errors**: Known issue with some .md files (upstream)
3. **Large file timeouts**: Expected for very large files
4. **Images return empty**: Expected - only EXIF metadata extracted

**Debugging steps**:
1. Test MarkItDown library directly
2. Check dependency installation
3. Verify file format support
4. Check error logs

### 4. Performance Optimization

**Known bottlenecks**:
- Large PDF files (100+ pages)
- Complex Office documents
- Audio file speech recognition
- Concurrent request handling

**Optimization areas**:
- Streaming for large files
- Caching converted results
- Memory management
- Concurrent request limits

## Code Style and Standards

### Python Code Standards
- **Python 3.10+** minimum requirement
- **Type hints** encouraged but not required
- **Error handling** must be comprehensive
- **Async/await** for all I/O operations
- **JSON-RPC 2.0** compliance mandatory

### MCP Protocol Standards
- All responses must include `id` from request
- Error codes must follow JSON-RPC standard
- Tool schemas must be valid JSON Schema
- Content must be properly formatted

### Documentation Standards
- Update `README.md` for user-facing changes
- Update `KNOWN_ISSUES.md` for limitations
- Add entries to `TESTING_STRATEGY.md` for new features
- Keep this `AGENT.md` current

## Testing Approach

**See `TESTING_STRATEGY.md` for complete details**

### Test Categories
- **Unit tests**: Individual function testing
- **Integration tests**: MCP protocol compliance
- **Performance tests**: Large files, concurrent requests
- **Security tests**: Path traversal, malicious inputs
- **Compatibility tests**: Cross-platform, Python versions

### Critical Test Areas
1. **MCP protocol compliance** - Most important
2. **File format support** - Core functionality
3. **Error handling** - User experience
4. **Security** - Path traversal protection
5. **Performance** - Large file handling

## Security Considerations

### Input Validation
- **Path traversal**: Validate all file paths
- **File size limits**: Prevent memory exhaustion
- **File type validation**: Verify file formats
- **Malicious content**: Handle corrupted files gracefully

### Resource Protection
- **Memory limits**: Monitor memory usage
- **Timeout protection**: Prevent infinite processing
- **Concurrent limits**: Prevent DoS attacks
- **Error information**: Don't leak system details

## Common AI Agent Mistakes to Avoid

### ❌ Don't Do
1. **Claim OCR support** - Images only provide EXIF metadata
2. **Use `sudo pip install`** - Always use pipx or virtual environments
3. **Ignore dependency requirements** - Many formats need specific packages
4. **Skip error handling** - MCP protocol requires proper error responses
5. **Modify core MarkItDown behavior** - We're a wrapper, not a replacement

### ✅ Do Instead
1. **Clearly document image limitations**
2. **Provide multiple installation methods**
3. **Test with all supported formats**
4. **Follow JSON-RPC 2.0 specification**
5. **Focus on MCP integration improvements**

## Release Checklist

When preparing for release:

1. ✅ **All tests pass** (once implemented)
2. ✅ **Documentation is current**
3. ✅ **Dependencies are properly specified**
4. ✅ **Installation methods work**
5. ✅ **Claude Desktop integration tested**
6. ✅ **Security review completed**
7. ✅ **Performance benchmarks established**
8. ✅ **Known issues documented**

## Useful Commands

```bash
# Development
git clone https://github.com/trsdn/markitdown-mcp.git
cd markitdown-mcp
pip install -e ".[all]"

# Testing
pytest tests/                    # Run all tests (once implemented)
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only

# Installation verification
markitdown-mcp --help          # Should not hang
pipx list --include-injected    # Check dependencies

# Debugging
echo '{"jsonrpc":"2.0","method":"tools/list","id":1,"params":{}}' | markitdown-mcp
```

## Repository Health

**Current Status**: ✅ Ready for testing implementation
**Next Steps**: Implement comprehensive test suite
**Known Issues**: See `KNOWN_ISSUES.md`
**Maintenance**: Active development

## Getting Help

1. **Issues**: Check `KNOWN_ISSUES.md` first
2. **Testing**: See `TESTING_STRATEGY.md`
3. **Installation**: See `README.md` installation section
4. **MCP Protocol**: Check official MCP documentation
5. **MarkItDown**: Check Microsoft's MarkItDown documentation

---

*This file is maintained to help AI agents effectively understand and contribute to the MarkItDown MCP Server project. Keep it updated as the project evolves.*