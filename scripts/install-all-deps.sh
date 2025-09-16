#!/bin/bash

# MarkItDown MCP Server - Install All Dependencies Script
# This script ensures all optional dependencies are installed for full functionality

echo "🚀 Installing MarkItDown MCP Server with ALL dependencies..."
echo ""

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed. Please install it first:"
    echo "   brew install pipx  # on macOS"
    echo "   sudo apt install pipx  # on Ubuntu/Debian"
    echo "   python -m pip install --user pipx  # or using pip"
    exit 1
fi

# Install or reinstall the MCP server
echo "📦 Installing MarkItDown MCP Server..."
pipx install --force git+https://github.com/trsdn/markitdown-mcp.git

# Install all required dependencies
echo ""
echo "💉 Injecting all required dependencies..."

# Core MarkItDown dependencies
echo "  → Installing PDF, OCR, and Speech dependencies..."
pipx inject markitdown-mcp 'markitdown[all]' --force

# Excel support
echo "  → Installing Excel support..."
pipx inject markitdown-mcp openpyxl xlrd pandas tabulate --force

# Advanced PDF support
echo "  → Installing advanced PDF support..."
pipx inject markitdown-mcp pymupdf pdfplumber pytesseract --force

# Audio/video support
echo "  → Installing audio processing support..."
pipx inject markitdown-mcp pydub speechrecognition --force

echo ""
echo "✅ Installation complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Add the MCP server to your Claude Desktop configuration"
echo "2. Restart Claude Desktop"
echo ""
echo "📝 Configuration example for claude_desktop_config.json:"
echo '{'
echo '  "mcpServers": {'
echo '    "markitdown": {'
echo '      "command": "markitdown-mcp",'
echo '      "args": []'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "📍 Config file locations:"
echo "  - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "  - Windows: %APPDATA%\\Claude\\claude_desktop_config.json"