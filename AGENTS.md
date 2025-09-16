# AI Agents Integration Guide

This guide provides comprehensive information for AI agents and assistants on how to effectively use the MarkItDown MCP server for document conversion tasks.

## 🤖 Quick Reference for AI Agents

### Primary Use Cases
- Convert documents (PDF, Word, Excel, PowerPoint) to markdown
- Extract readable text from various file formats
- Batch process directories of documents
- Support users with document analysis workflows

### Available Tools
1. **`convert_file`** - Convert individual files
2. **`convert_directory`** - Batch convert directories
3. **`list_supported_formats`** - Show supported formats

## 🛠️ Tool Usage Guide

### `convert_file` Tool

**When to use:**
- User provides a file path for conversion
- User shares base64 content that needs conversion
- Single document analysis required

**Parameters:**
```json
{
  "file_path": "/path/to/document.pdf",     // For local files
  "file_content": "base64encoded...",      // For shared content
  "filename": "document.pdf"               // Required with file_content
}
```

**Example scenarios:**
- "Convert this PDF to markdown"
- "Extract text from this Word document"
- "Make this Excel file readable"

### `convert_directory` Tool

**When to use:**
- User wants to process multiple files
- Batch conversion workflows
- Directory cleanup/organization tasks

**Parameters:**
```json
{
  "input_directory": "/path/to/input",
  "output_directory": "/path/to/output"    // Optional
}
```

**Example scenarios:**
- "Convert all documents in this folder"
- "Process my downloads directory"
- "Batch convert these reports"

### `list_supported_formats` Tool

**When to use:**
- User asks about supported file types
- Error troubleshooting (unsupported format)
- Capability discovery

**Parameters:** None

**Example scenarios:**
- "What file types can you convert?"
- "Can you handle PowerPoint files?"
- "Is Excel supported?"

## 💡 Best Practices for AI Agents

### 1. Format Detection
```python
# Always check format support first if unsure
if user_asks_about_unknown_format:
    call_tool("list_supported_formats")
```

### 2. Error Handling
- Check file paths exist before conversion
- Validate base64 content before processing
- Provide helpful error explanations to users

### 3. File Size Awareness
- Warn users about large files (>50MB may be slow)
- Suggest breaking up large directories
- Monitor conversion time for user experience

### 4. Security Considerations
- Never process files outside safe directories
- Validate file paths for security
- Be cautious with user-provided paths

## 🔧 Common Integration Patterns

### Pattern 1: Document Analysis Workflow
```python
def analyze_document(file_path):
    # Step 1: Convert to markdown
    result = convert_file(file_path=file_path)

    # Step 2: Extract and analyze content
    markdown_content = result['content'][0]['text']

    # Step 3: Provide analysis to user
    return analyze_markdown(markdown_content)
```

### Pattern 2: Batch Processing
```python
def process_document_folder(input_dir, output_dir):
    # Convert entire directory
    result = convert_directory(
        input_directory=input_dir,
        output_directory=output_dir
    )

    # Report results to user
    return summarize_conversion_results(result)
```

### Pattern 3: Format Validation
```python
def validate_and_convert(file_path):
    # Check if format is supported
    formats = list_supported_formats()

    # Extract file extension
    file_ext = get_extension(file_path)

    if file_ext in supported_formats:
        return convert_file(file_path=file_path)
    else:
        return suggest_alternative_formats()
```

## 🎯 User Experience Guidelines

### Helpful Responses
- **Good**: "I'll convert your PDF to markdown so we can analyze the content..."
- **Better**: "Converting your 15-page PDF report to markdown format for analysis. This may take a moment..."

### Error Handling
- **Good**: "The file couldn't be converted."
- **Better**: "This file format isn't supported. I can convert PDF, Word, Excel, and PowerPoint files. Would you like me to show all supported formats?"

### Progress Communication
- **Large files**: "Processing your 45MB document, this may take 30-60 seconds..."
- **Directories**: "Converting 23 files in your directory, processing in batches..."

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Do This
```python
# Don't assume all files can be converted
convert_file(mystery_file_path)

# Don't ignore errors
result = convert_file(file_path)
# ... proceed without checking if conversion succeeded

# Don't process unsafe paths
convert_file("/etc/passwd")
```

### ✅ Do This Instead
```python
# Check format support first
formats = list_supported_formats()
if is_supported(file_path, formats):
    result = convert_file(file_path)
    if result.get('error'):
        handle_conversion_error(result['error'])
    else:
        process_markdown(result['content'])
```

## 🔍 Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| "File not found" | Invalid path | Verify file exists and path is correct |
| "Permission denied" | File access rights | Check file permissions or use different file |
| "Unsupported format" | File type not supported | Use `list_supported_formats` to check alternatives |
| "Conversion failed" | File corrupted/encrypted | Try different file or check file integrity |

### Performance Issues
- **Slow conversion**: Normal for large files, inform user
- **Memory errors**: File too large, suggest breaking into smaller parts
- **Timeout**: Increase patience, very large files can take minutes

## 📊 Supported Formats Reference

### Documents
- **PDF**: `.pdf` (requires markitdown[pdf] dependencies)
- **Word**: `.docx`, `.doc`
- **PowerPoint**: `.pptx`, `.ppt`
- **Excel**: `.xlsx`, `.xls`

### Web & Markup
- **HTML**: `.html`, `.htm`
- **XML**: `.xml`
- **Markdown**: `.md`, `.markdown`

### Data
- **CSV**: `.csv`
- **JSON**: `.json`
- **Text**: `.txt`

### Usage Notes
- PDF conversion requires additional dependencies
- Office formats work best with newer file versions
- Large Excel files may have content limits

## 🔒 Security Features

### Path Protection
- Server only operates in configured safe directories
- Path traversal attacks are prevented
- Temporary files are automatically cleaned up

### Content Safety
- Base64 content is processed in secure temporary files
- No permanent storage of user content
- Memory is efficiently managed and cleaned

### Usage Limits
- File size limits prevent resource exhaustion
- Request rate limiting protects against DoS
- Timeout protections prevent hanging processes

## 📈 Performance Optimization

### For AI Agents
- Cache format lists to reduce API calls
- Batch similar operations when possible
- Provide progress feedback for long operations
- Handle errors gracefully with helpful messages

### For Users
- Process smaller files first for faster feedback
- Use specific output directories for organization
- Consider file size when setting expectations

## 🤝 Integration Examples

### Claude Code Integration
```json
{
  "mcpServers": {
    "markitdown": {
      "command": "markitdown-mcp",
      "description": "Convert documents to markdown for analysis"
    }
  }
}
```

### Custom Agent Integration
```python
class DocumentConverter:
    def __init__(self, mcp_client):
        self.mcp = mcp_client

    async def convert_and_analyze(self, file_path):
        # Convert document
        result = await self.mcp.call_tool(
            "convert_file",
            {"file_path": file_path}
        )

        # Extract content
        markdown = result['content'][0]['text']

        # Perform analysis
        return self.analyze_content(markdown)
```

## 📚 Additional Resources

- **[API Documentation](docs/api/)** - Technical specifications
- **[Configuration Examples](examples/)** - MCP client configurations
- **[Testing Guide](docs/development/TESTING_STRATEGY.md)** - Testing approach
- **[Known Issues](docs/guides/KNOWN_ISSUES.md)** - Common problems and solutions

---

*This guide is maintained for AI agents and assistants using the MarkItDown MCP server. For human developers, see the main [README.md](README.md) and [development documentation](docs/development/).*