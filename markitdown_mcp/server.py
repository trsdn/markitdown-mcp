#!/usr/bin/env python3
"""
MarkItDown MCP Server - Model Context Protocol server for document conversion
Converts various file formats to Markdown using Microsoft's MarkItDown library.
"""

import asyncio
import base64
import functools
import hmac
import json
import logging
import os
import signal
import sys
import tempfile
import threading
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from markitdown import MarkItDown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("markitdown-mcp")


class SecurityError(Exception):
    """Raised when a security violation is detected."""


class TimeoutError(Exception):
    """Raised when an operation times out."""


def timeout_handler(signum, frame):
    """Handler for timeout signal."""
    raise TimeoutError("Operation timed out")


def with_timeout(timeout_seconds=30):
    """Decorator to add timeout protection to functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set up timeout handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Reset alarm and handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator


def sanitize_unicode_text(text: str) -> str:
    """
    Sanitize Unicode text by normalizing and removing dangerous characters.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Unicode normalization
    text = unicodedata.normalize('NFKC', text)
    
    # Remove Bidi override characters and other potentially dangerous Unicode
    dangerous_chars = [
        '\u202E',  # RIGHT-TO-LEFT OVERRIDE
        '\u202D',  # LEFT-TO-RIGHT OVERRIDE
        '\u2066',  # LEFT-TO-RIGHT ISOLATE
        '\u2067',  # RIGHT-TO-LEFT ISOLATE
        '\u2068',  # FIRST STRONG ISOLATE
        '\u2069',  # POP DIRECTIONAL ISOLATE
    ]
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text


def secure_compare(a: str, b: str) -> bool:
    """
    Perform constant-time string comparison to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal
    """
    return hmac.compare_digest(str(a).encode(), str(b).encode())


def normalize_timing(func):
    """
    Decorator to normalize execution time and prevent timing attacks.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with normalized timing
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = e
            success = False
        
        # Ensure minimum execution time to prevent timing differences
        min_time = 0.1  # 100ms minimum
        elapsed = time.time() - start_time
        if elapsed < min_time:
            time.sleep(min_time - elapsed)
        
        if success:
            return result
        else:
            raise result
    
    return wrapper


def validate_base64(data: str, max_size: int = 10 * 1024 * 1024) -> bytes:
    """
    Validate and decode base64 data with size limits.
    
    Args:
        data: Base64 encoded string
        max_size: Maximum allowed decoded size in bytes
        
    Returns:
        Decoded bytes
        
    Raises:
        SecurityError: If validation fails
    """
    try:
        # Basic format check
        if not isinstance(data, str):
            raise SecurityError("Security violation: invalid base64 format")
        
        # Decode with validation
        decoded = base64.b64decode(data, validate=True)
        
        # Check size limit
        if len(decoded) > max_size:
            raise SecurityError("Security violation: file too large")
        
        return decoded
        
    except Exception as e:
        raise SecurityError("Security violation: invalid base64 data")


def extract_text_from_binary(data: bytes, filename: str = "") -> Optional[str]:
    """
    Extract readable text from potentially binary data.
    
    Args:
        data: Binary data
        filename: Optional filename for context
        
    Returns:
        Extracted text or None if no readable content found
    """
    try:
        # Try UTF-8 first
        try:
            text = data.decode('utf-8')
            # Check if it contains reasonable amount of printable characters
            printable_ratio = sum(1 for c in text if c.isprintable() or c.isspace()) / len(text)
            if printable_ratio > 0.7:  # At least 70% printable
                return text
        except UnicodeDecodeError:
            pass
        
        # Try other common encodings
        encodings = ['latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                text = data.decode(encoding, errors='ignore')
                printable_ratio = sum(1 for c in text if c.isprintable() or c.isspace()) / len(text)
                if printable_ratio > 0.7:
                    return text
            except:
                continue
        
        # Extract printable ASCII characters as fallback
        printable_chars = ''.join(chr(b) for b in data if 32 <= b <= 126 or b in [9, 10, 13])
        if len(printable_chars) > 20:  # At least some readable content
            return printable_chars
        
        return None
        
    except Exception:
        return None


@with_timeout(30)
def safe_convert_with_limits(markitdown_instance, file_path: str) -> Any:
    """
    Safely convert a file with timeout and recursion protection.
    
    Args:
        markitdown_instance: MarkItDown instance
        file_path: Path to file to convert
        
    Returns:
        Conversion result
        
    Raises:
        TimeoutError: If conversion times out
        RecursionError: If recursion limit is exceeded
        SecurityError: For security violations
    """
    # Set recursion limit
    original_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(100)  # Conservative limit
    
    try:
        # Check if file might contain binary data in text format
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            with open(file_path, 'rb') as f:
                data = f.read(1024)  # Read first 1KB to check
                
            # If it's a text file but contains significant binary content
            mime_type = None
            try:
                import mimetypes
                mime_type = mimetypes.guess_type(file_path)[0]
            except:
                pass
                
            if mime_type and mime_type.startswith('text/'):
                # For text files, extract readable content if binary data present
                try:
                    # Test if it's valid text
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    # Contains binary data, extract text portions
                    extracted_text = extract_text_from_binary(data, str(file_path_obj))
                    if extracted_text:
                        # Create temporary file with extracted text
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                            tmp.write(extracted_text)
                            temp_path = tmp.name
                        try:
                            result = markitdown_instance.convert(temp_path)
                            if hasattr(result, 'text_content') and result.text_content:
                                result.text_content = sanitize_unicode_text(result.text_content)
                            return result
                        finally:
                            Path(temp_path).unlink(missing_ok=True)
        
        # Normal conversion
        result = markitdown_instance.convert(file_path)
        
        # Sanitize the result text
        if hasattr(result, 'text_content') and result.text_content:
            result.text_content = sanitize_unicode_text(result.text_content)
        
        return result
        
    except RecursionError:
        raise SecurityError("Security violation: processing limit exceeded")
    except Exception as e:
        if "recursion" in str(e).lower():
            raise SecurityError("Security violation: processing limit exceeded")
        raise
    finally:
        # Restore original recursion limit
        sys.setrecursionlimit(original_limit)


@normalize_timing
def validate_and_sanitize_path(
    file_path: str, allowed_dirs: Optional[List[str]] = None
) -> Tuple[Path, bool]:
    """
    Validate and sanitize file paths to prevent path traversal attacks.

    Args:
        file_path: The file path to validate
        allowed_dirs: List of allowed directory prefixes (optional)

    Returns:
        Tuple of (sanitized_path, is_safe)

    Raises:
        SecurityError: If path is potentially malicious
    """
    try:
        # Convert to Path object and resolve to absolute path
        path = Path(file_path).resolve()

        # Check for dangerous path patterns
        path_str = str(path).lower()
        dangerous_patterns = [
            "/etc/",
            "/proc/",
            "/sys/",
            "/dev/",
            "/root/",
            "/boot/",
            "/usr/bin/",
            "/usr/sbin/",
            "/sbin/",
            "/bin/",
            "\\windows\\",
            "\\system32\\",
            "\\program files\\",
            "\\programdata\\",
            "\\users\\administrator\\",
            "/var/log/",
            "/var/run/",
        ]

        for pattern in dangerous_patterns:
            if pattern in path_str:
                raise SecurityError("Security violation: access denied")

        # Check for path traversal attempts in the original path
        if ".." in file_path:
            raise SecurityError("Security violation: path traversal detected")

        # For absolute paths, check if they're in allowed directories
        if file_path.startswith("/") or (len(file_path) > 2 and file_path[1] == ":"):
            if allowed_dirs:
                # Resolve allowed directories for proper comparison
                resolved_allowed_dirs = [
                    str(Path(allowed_dir).resolve()) for allowed_dir in allowed_dirs
                ]
                is_allowed = any(
                    str(path).startswith(allowed_dir) for allowed_dir in resolved_allowed_dirs
                )
                if not is_allowed:
                    raise SecurityError("Security violation: access denied")
            else:
                # If no allowed dirs specified, check against temp directory
                temp_dir = Path(tempfile.gettempdir()).resolve()
                if not str(path).startswith(str(temp_dir)):
                    raise SecurityError("Security violation: access denied")

        # Check file extension for potentially dangerous files
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".sh",
            ".ps1",
            ".scr",
            ".vbs",
            ".jar",
            ".app",
            ".dmg",
            ".pkg",
            ".deb",
            ".rpm",
        ]

        if path.suffix.lower() in dangerous_extensions:
            raise SecurityError("Security violation: file type not allowed")

        # Additional checks for hidden/system files
        if path.name.startswith(".") and path.name in [".passwd", ".shadow", ".ssh", ".htaccess"]:
            raise SecurityError("Security violation: access denied")

        return path, True

    except (OSError, ValueError) as e:
        raise SecurityError("Security violation: invalid path")


def get_safe_working_directories() -> List[str]:
    """Get list of safe working directories for file operations."""
    safe_dirs = []

    # Add current working directory
    safe_dirs.append(str(Path.cwd()))

    # Add home directory subdirectories (but not root directories)
    home = Path.home()
    safe_subdirs = ["Documents", "Downloads", "Desktop", "tmp"]
    for subdir in safe_subdirs:
        potential_dir = home / subdir
        if potential_dir.exists():
            safe_dirs.append(str(potential_dir))

    # Add temp directories
    temp_dir = Path(tempfile.gettempdir())
    safe_dirs.append(str(temp_dir))

    # Add test fixtures directory if it exists
    fixtures_dir = Path.cwd() / "tests" / "fixtures"
    if fixtures_dir.exists():
        safe_dirs.append(str(fixtures_dir))

    return safe_dirs


@dataclass
class MCPRequest:
    id: str
    method: str
    params: Dict[str, Any]


@dataclass
class MCPResponse:
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MarkItDownMCPServer:
    def __init__(self):
        self.markitdown = MarkItDown()
        self.supported_extensions = {
            # Office documents
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".xls",
            # Web and markup
            ".html",
            ".htm",
            # Data formats
            ".csv",
            ".json",
            ".xml",
            # Archives
            ".zip",
            # E-books
            ".epub",
            # Images (common formats)
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",
            # Audio (common formats)
            ".mp3",
            ".wav",
            ".flac",
            ".m4a",
            ".ogg",
            ".wma",
            # Text files
            ".txt",
            ".md",
            ".rst",
        }
        # Initialize safe working directories
        self.safe_directories = get_safe_working_directories()
        logger.info(f"Initialized with safe directories: {self.safe_directories}")

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests"""
        try:
            if request.method == "initialize":
                return MCPResponse(
                    id=request.id,
                    result={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "markitdown-server", "version": "1.0.0"},
                    },
                )

            elif request.method == "tools/list":
                return MCPResponse(
                    id=request.id,
                    result={
                        "tools": [
                            {
                                "name": "convert_file",
                                "description": "Convert a file to Markdown using MarkItDown",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {
                                            "type": "string",
                                            "description": "Path to the file to convert",
                                        },
                                        "file_content": {
                                            "type": "string",
                                            "description": (
                                                "Base64 encoded file content "
                                                "(alternative to file_path)"
                                            ),
                                        },
                                        "filename": {
                                            "type": "string",
                                            "description": "Original filename when using "
                                            "file_content",
                                        },
                                    },
                                    "anyOf": [
                                        {"required": ["file_path"]},
                                        {"required": ["file_content", "filename"]},
                                    ],
                                },
                            },
                            {
                                "name": "list_supported_formats",
                                "description": "List all supported file formats for conversion",
                                "inputSchema": {"type": "object", "properties": {}},
                            },
                            {
                                "name": "convert_directory",
                                "description": "Convert all supported files in a "
                                "directory to Markdown",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "input_directory": {
                                            "type": "string",
                                            "description": "Path to the input directory",
                                        },
                                        "output_directory": {
                                            "type": "string",
                                            "description": "Path to the output directory "
                                            "(optional)",
                                        },
                                    },
                                    "required": ["input_directory"],
                                },
                            },
                        ]
                    },
                )

            elif request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})

                # Validate required parameters
                if not tool_name:
                    return MCPResponse(
                        id=request.id,
                        error={"code": -32602, "message": "Missing required parameter: name"},
                    )

                if tool_name == "convert_file":
                    return await self.convert_file_tool(request.id, arguments)
                elif tool_name == "list_supported_formats":
                    return await self.list_supported_formats_tool(request.id)
                elif tool_name == "convert_directory":
                    return await self.convert_directory_tool(request.id, arguments)
                else:
                    return MCPResponse(
                        id=request.id,
                        error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                    )

            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Unknown method: {request.method}"},
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse(
                id=request.id, error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )

    async def convert_file_tool(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Convert a single file to Markdown"""
        try:
            file_path = arguments.get("file_path")
            file_content = arguments.get("file_content")
            filename = arguments.get("filename")

            if file_path:
                # Convert from file path with security validation
                try:
                    # Validate and sanitize the file path
                    validated_path, is_safe = validate_and_sanitize_path(
                        file_path, self.safe_directories
                    )
                    logger.info(f"Validated file path: {file_path} -> {validated_path}")

                except SecurityError as e:
                    logger.warning(f"Security violation blocked: {e}")
                    return MCPResponse(
                        id=request_id,
                        error={"code": -32602, "message": f"Security violation: {str(e)}"},
                    )

                if not validated_path.exists():
                    return MCPResponse(
                        id=request_id,
                        error={"code": -32602, "message": f"File not found: {file_path}"},
                    )

                # Check if file is readable
                if not os.access(validated_path, os.R_OK):
                    return MCPResponse(
                        id=request_id,
                        error={"code": -32602, "message": f"File not readable: {file_path}"},
                    )

                try:
                    result = safe_convert_with_limits(self.markitdown, str(validated_path))
                except (TimeoutError, SecurityError) as e:
                    return MCPResponse(
                        id=request_id,
                        error={"code": -32602, "message": f"Security violation: {str(e)}"},
                    )
                markdown_content = result.text_content

                return MCPResponse(
                    id=request_id,
                    result={
                        "content": [
                            {
                                "type": "text",
                                "text": f"Successfully converted {validated_path.name} to "
                                f"Markdown:\n\n{markdown_content}",
                            }
                        ]
                    },
                )

            elif file_content and filename:
                # Convert from base64 encoded content
                try:
                    # Validate and decode base64 content
                    decoded_content = validate_base64(file_content)

                    # Create temporary file
                    with tempfile.NamedTemporaryFile(
                        suffix=Path(filename).suffix, delete=False
                    ) as temp_file:
                        temp_file.write(decoded_content)
                        temp_path = temp_file.name

                    try:
                        result = safe_convert_with_limits(self.markitdown, temp_path)
                        markdown_content = result.text_content

                        return MCPResponse(
                            id=request_id,
                            result={
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Successfully converted {filename} to "
                                        f"Markdown:\n\n{markdown_content}",
                                    }
                                ]
                            },
                        )
                    finally:
                        # Clean up temporary file
                        Path(temp_path).unlink(missing_ok=True)

                except Exception as e:
                    return MCPResponse(
                        id=request_id,
                        error={
                            "code": -32603,
                            "message": f"Error processing file content: {str(e)}",
                        },
                    )
            else:
                return MCPResponse(
                    id=request_id,
                    error={
                        "code": -32602,
                        "message": "Either file_path or (file_content + filename) required",
                    },
                )

        except Exception as e:
            logger.error(f"Error in convert_file_tool: {e}")
            return MCPResponse(
                id=request_id, error={"code": -32603, "message": f"Conversion failed: {str(e)}"}
            )

    async def list_supported_formats_tool(self, request_id: str) -> MCPResponse:
        """List all supported file formats"""
        format_categories = {
            "Office Documents": [".pdf", ".docx", ".pptx", ".xlsx", ".xls"],
            "Web and Markup": [".html", ".htm"],
            "Data Formats": [".csv", ".json", ".xml"],
            "Archives": [".zip"],
            "E-books": [".epub"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma"],
            "Text Files": [".txt", ".md", ".rst"],
        }

        format_list = []
        for category, extensions in format_categories.items():
            format_list.append(f"**{category}:**")
            for ext in extensions:
                format_list.append(f"  - {ext}")
            format_list.append("")

        return MCPResponse(
            id=request_id,
            result={
                "content": [
                    {
                        "type": "text",
                        "text": "Supported file formats for MarkItDown conversion:\n\n"
                        + "\n".join(format_list),
                    }
                ]
            },
        )

    async def convert_directory_tool(
        self, request_id: str, arguments: Dict[str, Any]
    ) -> MCPResponse:
        """Convert all supported files in a directory"""
        try:
            # Validate required arguments
            if "input_directory" not in arguments:
                return MCPResponse(
                    id=request_id,
                    error={"code": -32602, "message": "Missing required argument: input_directory"},
                )

            # Security validation for input directory
            try:
                validated_input_dir, is_safe = validate_and_sanitize_path(
                    arguments["input_directory"], self.safe_directories
                )
                logger.info(
                    f"Validated input directory: {arguments['input_directory']} -> "
                    f"{validated_input_dir}"
                )
            except SecurityError as e:
                logger.warning(f"Security violation blocked for directory: {e}")
                return MCPResponse(
                    id=request_id,
                    error={"code": -32602, "message": f"Security violation: {str(e)}"},
                )

            # Security validation for output directory if specified
            if "output_directory" in arguments:
                try:
                    validated_output_dir, is_safe = validate_and_sanitize_path(
                        arguments["output_directory"], self.safe_directories
                    )
                    logger.info(
                        f"Validated output directory: {arguments['output_directory']} -> "
                        f"{validated_output_dir}"
                    )
                except SecurityError as e:
                    logger.warning(f"Security violation blocked for output directory: {e}")
                    return MCPResponse(
                        id=request_id,
                        error={
                            "code": -32602,
                            "message": f"Security violation in output directory: {str(e)}",
                        },
                    )
            else:
                # Create output directory as sibling to input directory to avoid recursion
                validated_output_dir = (
                    validated_input_dir.parent / f"{validated_input_dir.name}_converted_markdown"
                )

            if not validated_input_dir.exists():
                return MCPResponse(
                    id=request_id,
                    error={
                        "code": -32602,
                        "message": f"Input directory not found: {arguments['input_directory']}",
                    },
                )

            if not validated_input_dir.is_dir():
                return MCPResponse(
                    id=request_id,
                    error={
                        "code": -32602,
                        "message": f"Path is not a directory: {arguments['input_directory']}",
                    },
                )

            success_count = 0
            failed_count = 0
            failed_files = []

            validated_output_dir.mkdir(parents=True, exist_ok=True)

            for file_path in validated_input_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    try:
                        relative_path = file_path.relative_to(validated_input_dir)
                        output_path = validated_output_dir / relative_path.with_suffix(".md")
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        # Use asyncio to run blocking operations with timeout protection
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, safe_convert_with_limits, self.markitdown, str(file_path)
                        )
                        markdown_content = result.text_content

                        # Write file asynchronously
                        def write_file():
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(markdown_content)

                        await asyncio.get_event_loop().run_in_executor(None, write_file)
                        success_count += 1

                    except Exception as e:
                        failed_count += 1
                        error_msg = str(e)
                        # Sanitize error message to prevent information leakage
                        if "No such file" in error_msg or "Permission denied" in error_msg:
                            error_msg = "File access error"
                        elif len(error_msg) > 100:
                            error_msg = error_msg[:100] + "..."
                        failed_files.append(f"{file_path.name}: {error_msg}")

            result_text = "Directory conversion completed:\n"
            result_text += f"- Successfully converted: {success_count} files\n"
            result_text += f"- Failed conversions: {failed_count} files\n"
            result_text += f"- Output directory: {validated_output_dir}\n"

            if failed_files:
                result_text += "\nFailed files:\n"
                for failed in failed_files[:10]:  # Limit to first 10 failures
                    result_text += f"  - {failed}\n"
                if len(failed_files) > 10:
                    result_text += f"  ... and {len(failed_files) - 10} more\n"

            return MCPResponse(
                id=request_id, result={"content": [{"type": "text", "text": result_text}]}
            )

        except Exception as e:
            logger.error(f"Error in convert_directory_tool: {e}")
            return MCPResponse(
                id=request_id,
                error={"code": -32603, "message": f"Directory conversion failed: {str(e)}"},
            )

    async def run(self):
        """Run the MCP server"""
        logger.info("MarkItDown MCP Server starting...")

        try:
            while True:
                # Read JSON-RPC message from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                try:
                    message = json.loads(line.strip())
                    request = MCPRequest(
                        id=message.get("id", "unknown"),
                        method=message["method"],
                        params=message.get("params", {}),
                    )

                    response = await self.handle_request(request)

                    # Send response
                    response_dict = {"jsonrpc": "2.0", "id": response.id}
                    if response.result is not None:
                        response_dict["result"] = response.result
                    if response.error is not None:
                        response_dict["error"] = response.error

                    print(json.dumps(response_dict), flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")


def main():
    """Main entry point for console script"""

    async def run_server():
        server = MarkItDownMCPServer()
        await server.run()

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
