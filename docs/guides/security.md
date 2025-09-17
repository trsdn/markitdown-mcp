# Security Guide

This guide covers the security features and best practices for the MarkItDown MCP server.

## Security Features

### Path Validation
- Path traversal prevention
- Safe directory restrictions
- Absolute path validation

### File Size Limits
- Configurable maximum file sizes
- Default 100MB limit
- Memory usage protection

### Timeout Protection
- 30-second default timeout
- Prevents resource exhaustion
- Configurable per operation

### Content Sanitization
- XML security validation
- JSON parsing limits
- CSV injection prevention
- Unicode normalization

### Access Control
- Safe working directories only
- No arbitrary file system access
- Environment-based configuration

## Configuration

Set security limits via environment variables:

```bash
export MAX_FILE_SIZE_MB=50
export CONVERSION_TIMEOUT=45
export SAFE_DIRECTORIES="/allowed/path1:/allowed/path2"
```

## Best Practices

1. **Limit file sizes** appropriate to your use case
2. **Restrict safe directories** to minimize attack surface
3. **Monitor resource usage** in production environments
4. **Keep dependencies updated** for security patches
5. **Use dedicated service accounts** with minimal privileges