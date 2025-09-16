# API Documentation

This directory contains technical API documentation for the MarkItDown MCP server.

## Available Tools

### `convert_file`
Convert a single file to markdown format.

**Parameters:**
- `file_path` (string, optional): Path to the file to convert
- `file_content` (string, optional): Base64-encoded file content
- `filename` (string, required if using file_content): Original filename

**Returns:**
- `content`: Array of content blocks with converted markdown

### `convert_directory`
Convert all supported files in a directory to markdown.

**Parameters:**
- `input_directory` (string, required): Path to input directory
- `output_directory` (string, optional): Path to output directory

**Returns:**
- `content`: Summary of conversion results

### `list_supported_formats`
List all supported file formats for conversion.

**Parameters:** None

**Returns:**
- `content`: List of supported file formats and descriptions

## MCP Protocol Implementation

The server implements MCP protocol version `2024-11-05` with the following capabilities:

### Server Info
```json
{
  "name": "markitdown-server",
  "version": "1.0.0"
}
```

### Capabilities
```json
{
  "tools": {}
}
```

## Error Handling

The server returns standard MCP error responses:

### Common Error Codes
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

### Tool-Specific Errors
- File not found
- Permission denied
- Unsupported format
- Conversion failed

## Security Features

- Path traversal protection
- Safe directory restrictions
- Temporary file cleanup
- Request size limits
- DoS protection

## Performance Considerations

- Memory usage optimization
- Large file handling
- Concurrent request management
- Resource cleanup