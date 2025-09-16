# MCP Configuration Examples

This directory contains example configurations for using the MarkItDown MCP server with various MCP clients.

## Quick Start

1. Copy the appropriate configuration file for your MCP client
2. Update the `command` path if needed to match your installation
3. Add the configuration to your client's MCP settings

## Configuration Files

### `mcp_config.json`
Basic MCP server configuration showing all available tools and capabilities.

### `claude_code_config.json`
Configuration optimized for Claude Code with environment variables.

### `cursor_config.json`
Configuration for Cursor IDE with timeout and capability specifications.

## Usage in Different Clients

### Claude Code
```bash
# Add to your Claude Code configuration
cp examples/claude_code_config.json ~/.config/claude-code/mcp.json
```

### Cursor
```bash
# Add to your Cursor settings
cp examples/cursor_config.json ~/.cursor/mcp-config.json
```

### Custom MCP Client
Use `mcp_config.json` as a template and modify according to your client's requirements.

## Configuration Options

### Basic Options
- `command`: Path to the markitdown-mcp executable
- `args`: Command line arguments (usually empty)
- `description`: Human-readable description of the server

### Advanced Options
- `env`: Environment variables to set for the server process
- `timeout`: Request timeout in milliseconds
- `capabilities`: Server capabilities and limitations

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure `markitdown-mcp` is in your PATH or use full path
2. **Permission denied**: Make sure the executable has proper permissions
3. **Timeout errors**: Increase the timeout value for large file processing

### Debugging

Enable debug logging by setting environment variables:
```json
{
  "env": {
    "LOG_LEVEL": "DEBUG",
    "MCP_DEBUG": "1"
  }
}
```

## Security Considerations

- The server only operates on files within configured safe directories
- Base64 content is processed in temporary files that are automatically cleaned up
- No network access is required for file conversion operations

## Performance Notes

- Large files (>50MB) may take longer to process
- PDF files require additional dependencies (`pip install markitdown[pdf]`)
- Directory conversions process files sequentially to manage memory usage