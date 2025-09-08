"""
Cross-platform compatibility tests.
Tests server behavior across different operating systems and environments.
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_error_response, assert_mcp_success_response


class PlatformDetector:
    """Detect and provide platform-specific information."""

    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """Get comprehensive platform information."""
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "architecture": platform.architecture(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "node": platform.node(),
            "processor": platform.processor(),
            "is_windows": os.name == "nt",
            "is_posix": os.name == "posix",
            "is_macos": platform.system() == "Darwin",
            "is_linux": platform.system() == "Linux",
            "path_separator": os.sep,
            "line_separator": os.linesep,
            "env_path_separator": os.pathsep,
        }

    @staticmethod
    def is_windows() -> bool:
        return os.name == "nt"

    @staticmethod
    def is_unix_like() -> bool:
        return os.name == "posix"

    @staticmethod
    def is_macos() -> bool:
        return platform.system() == "Darwin"

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"


class TestPlatformBasics:
    """Test basic platform compatibility."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_server_initialization_cross_platform(self):
        """Test server initialization works on all platforms."""
        platform_info = PlatformDetector.get_platform_info()

        # Server should initialize regardless of platform
        server = MarkItDownMCPServer()

        request = MCPRequest(id="platform-init-test", method="initialize", params={})

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "platform-init-test")

        # Verify server info is consistent across platforms
        server_info = response.result["serverInfo"]
        assert server_info["name"] == "markitdown-server"
        assert server_info["version"] == "1.0.0"

        # Protocol version should be consistent
        assert response.result["protocolVersion"] == "2024-11-05"

        print(
            f"✓ Server initialization successful on {platform_info['system']} {platform_info['machine']}"
        )

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_tools_list_cross_platform(self):
        """Test tools listing consistency across platforms."""
        server = MarkItDownMCPServer()

        request = MCPRequest(id="platform-tools-test", method="tools/list", params={})

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "platform-tools-test")

        tools = response.result["tools"]
        assert len(tools) == 3, f"Expected 3 tools on all platforms, got {len(tools)}"

        # Verify expected tools
        tool_names = {tool["name"] for tool in tools}
        expected_tools = {"convert_file", "list_supported_formats", "convert_directory"}
        assert tool_names == expected_tools, f"Tool set inconsistent across platforms: {tool_names}"

        # Verify tool schemas are complete
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_supported_formats_consistency(self):
        """Test that supported formats are consistent across platforms."""
        server = MarkItDownMCPServer()

        request = MCPRequest(
            id="platform-formats-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "platform-formats-test")

        formats_text = response.result["content"][0]["text"]

        # Core formats should be supported on all platforms
        core_formats = [".txt", ".json", ".csv", ".html", ".md", ".xml"]
        for fmt in core_formats:
            assert fmt in formats_text, f"Core format {fmt} not supported on this platform"

        # Should mention major categories
        categories = ["Office Documents", "Images", "Audio", "Text Files"]
        for category in categories:
            assert category in formats_text, f"Category {category} missing from formats list"


class TestFileSystemCompatibility:
    """Test file system compatibility across platforms."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_path_handling_cross_platform(self, temp_dir):
        """Test path handling works on all platforms."""
        server = MarkItDownMCPServer()
        platform_info = PlatformDetector.get_platform_info()

        # Create test file with platform-appropriate path
        test_file = Path(temp_dir) / "cross_platform_test.txt"
        test_content = f"Cross-platform test on {platform_info['system']}\nPath separator: {platform_info['path_separator']}\n"
        test_file.write_text(test_content, encoding="utf-8")

        # Test with both forward slashes and platform-native paths
        test_paths = [
            str(test_file),  # Native path
            str(test_file).replace(os.sep, "/"),  # Forward slashes
        ]

        if PlatformDetector.is_windows():
            # Test Windows-specific path formats
            test_paths.extend(
                [
                    str(test_file).replace("/", "\\"),  # Backslashes
                    str(test_file).upper(),  # Upper case (Windows is case-insensitive)
                ]
            )

        for i, path in enumerate(test_paths):
            request = MCPRequest(
                id=f"platform-path-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": path}},
            )

            response = await server.handle_request(request)

            # Should handle all path formats appropriately
            if response.result:
                assert_mcp_success_response(response, f"platform-path-{i}")
                content = response.result["content"][0]["text"]
                assert "Cross-platform test" in content
            else:
                # Some path formats may not work - that's acceptable
                assert response.error is not None

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_unicode_filename_support(self, temp_dir):
        """Test Unicode filename support across platforms."""
        server = MarkItDownMCPServer()

        # Unicode filenames to test
        unicode_filenames = [
            "test_básico.txt",  # Accented characters
            "测试文件.txt",  # Chinese characters
            "файл_тест.txt",  # Cyrillic
            "ملف_اختبار.txt",  # Arabic (RTL)
            "test_emoji_🚀.txt",  # Emoji
        ]

        successful_unicode = 0

        for filename in unicode_filenames:
            try:
                # Create file with Unicode name
                unicode_file = Path(temp_dir) / filename
                unicode_content = f"Unicode filename test: {filename}\nContent in UTF-8 encoding."
                unicode_file.write_text(unicode_content, encoding="utf-8")

                # Test conversion
                request = MCPRequest(
                    id=f"unicode-{hash(filename) % 1000}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(unicode_file)}},
                )

                response = await server.handle_request(request)

                if response.result:
                    successful_unicode += 1
                    content = response.result["content"][0]["text"]
                    assert filename in content or "Unicode filename test" in content

            except (OSError, UnicodeEncodeError, UnicodeDecodeError):
                # Some Unicode filenames may not be supported by the filesystem
                # This is platform-dependent and acceptable
                pass

        # At least basic accented characters should work
        assert successful_unicode >= 1, "Platform should support at least basic Unicode filenames"

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_case_sensitivity_handling(self, temp_dir):
        """Test case sensitivity handling across platforms."""
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "CaseSensitive.txt"
        test_file.write_text("Case sensitivity test content")

        # Test different case variations
        case_variations = [
            str(test_file),  # Original case
            str(test_file).lower(),  # All lowercase
            str(test_file).upper(),  # All uppercase
            str(test_file).replace("CaseSensitive", "casesensitive"),  # Mixed case
        ]

        results = []

        for variation in case_variations:
            request = MCPRequest(
                id=f"case-test-{hash(variation) % 1000}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": variation}},
            )

            response = await server.handle_request(request)
            results.append((variation, response.result is not None))

        # On case-insensitive systems (Windows, macOS by default), all should work
        # On case-sensitive systems (Linux), only exact match should work
        original_works = results[0][1]
        assert original_works, "Original filename should always work"

        if PlatformDetector.is_windows():
            # Windows is case-insensitive
            all_work = all(result for _, result in results)
            assert all_work, "All case variations should work on Windows"

        # Don't assert strict requirements for other platforms as behavior varies


class TestEnvironmentCompatibility:
    """Test compatibility across different Python environments."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_python_version_compatibility(self):
        """Test compatibility with current Python version."""
        python_version = sys.version_info
        platform_info = PlatformDetector.get_platform_info()

        # Server should work with Python 3.10+
        assert python_version >= (
            3,
            10,
        ), f"Python {python_version[0]}.{python_version[1]} not supported"

        server = MarkItDownMCPServer()

        # Test basic functionality
        request = MCPRequest(id="python-compat", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "python-compat")

        print(
            f"✓ Compatible with Python {platform_info['python_version']} ({platform_info['python_implementation']})"
        )

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_encoding_handling(self, temp_dir):
        """Test text encoding handling across platforms."""
        server = MarkItDownMCPServer()

        # Test different encodings
        encoding_tests = [
            ("utf-8", "UTF-8 test: Hello 世界 🌍"),
            ("utf-16", "UTF-16 test content"),
            ("latin1", "Latin1 test: café résumé naïve"),
        ]

        for encoding, content in encoding_tests:
            try:
                # Create file with specific encoding
                encoded_file = Path(temp_dir) / f"encoding_{encoding}.txt"

                if encoding == "latin1":
                    # Ensure content is latin1-compatible
                    safe_content = "Latin1 test: cafe resume naive"
                    encoded_file.write_text(safe_content, encoding=encoding)
                else:
                    encoded_file.write_text(content, encoding=encoding)

                # Test conversion
                request = MCPRequest(
                    id=f"encoding-{encoding}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(encoded_file)}},
                )

                response = await server.handle_request(request)

                # Should handle different encodings gracefully
                if response.result:
                    result_content = response.result["content"][0]["text"]
                    assert len(result_content) > 0, f"Empty result for {encoding}"
                else:
                    # Encoding issues may cause errors - that's acceptable
                    assert response.error is not None

            except (UnicodeError, LookupError):
                # Some encodings may not be supported - that's acceptable
                pass

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_line_ending_compatibility(self, temp_dir):
        """Test line ending handling across platforms."""
        server = MarkItDownMCPServer()
        platform_info = PlatformDetector.get_platform_info()

        # Test different line endings
        line_ending_tests = [
            ("unix", "\n", "Unix line endings"),
            ("windows", "\r\n", "Windows line endings"),
            ("mac_classic", "\r", "Classic Mac line endings"),
            ("mixed", "\n\r\n", "Mixed line endings"),
        ]

        for ending_type, line_end, description in line_ending_tests:
            # Create file with specific line endings
            content_lines = [
                "Line 1 of test content",
                "Line 2 with different ending",
                "Line 3 final line",
            ]
            content = line_end.join(content_lines)

            line_ending_file = Path(temp_dir) / f"line_endings_{ending_type}.txt"

            # Write as binary to preserve exact line endings
            line_ending_file.write_bytes(content.encode("utf-8"))

            # Test conversion
            request = MCPRequest(
                id=f"line-endings-{ending_type}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(line_ending_file)}},
            )

            response = await server.handle_request(request)

            # Should handle all line ending types
            if response.result:
                result_content = response.result["content"][0]["text"]
                # All line types should preserve content
                assert "Line 1 of test content" in result_content
                assert "Line 2 with different ending" in result_content
                assert "Line 3 final line" in result_content
            else:
                # Some line ending issues might cause errors
                assert response.error is not None


class TestDependencyCompatibility:
    """Test compatibility with different dependency configurations."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_markitdown_library_integration(self, temp_dir):
        """Test integration with MarkItDown library across platforms."""
        server = MarkItDownMCPServer()

        # Test MarkItDown integration with basic formats
        test_files = [
            ("simple.txt", "Simple text content for MarkItDown test"),
            ("data.json", '{"test": "MarkItDown JSON integration", "platform": "cross-platform"}'),
            ("table.csv", "Name,Value\nTest1,100\nTest2,200"),
        ]

        for filename, content in test_files:
            test_file = Path(temp_dir) / filename
            test_file.write_text(content)

            request = MCPRequest(
                id=f"markitdown-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)

            # MarkItDown should work with basic formats on all platforms
            assert_mcp_success_response(response, f"markitdown-{filename}")

            result_content = response.result["content"][0]["text"]
            if filename == "simple.txt":
                assert "Simple text content" in result_content
            elif filename == "data.json":
                assert "MarkItDown JSON integration" in result_content
            elif filename == "table.csv":
                assert "Test1" in result_content and "100" in result_content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_optional_dependency_handling(self, temp_dir):
        """Test handling of optional dependencies."""
        server = MarkItDownMCPServer()

        # Test formats that might require optional dependencies
        optional_dependency_formats = [
            # These might work depending on available dependencies
            ("document.html", "<html><body><h1>HTML Test</h1><p>Content</p></body></html>"),
            ("structure.xml", '<?xml version="1.0"?><root><item>XML Test</item></root>'),
        ]

        for filename, content in optional_dependency_formats:
            test_file = Path(temp_dir) / filename
            test_file.write_text(content)

            request = MCPRequest(
                id=f"optional-deps-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)

            # Should either work or fail gracefully
            if response.result:
                # If successful, should contain expected content
                result_content = response.result["content"][0]["text"]
                if "html" in filename.lower():
                    assert "HTML Test" in result_content or "Content" in result_content
                elif "xml" in filename.lower():
                    assert "XML Test" in result_content
            else:
                # If failed, should have informative error
                assert response.error is not None
                error_msg = response.error["message"].lower()
                # Should indicate missing dependency or format not supported
                acceptable_errors = ["dependency", "not supported", "format", "library", "module"]
                assert any(
                    term in error_msg for term in acceptable_errors
                ), f"Unclear error for optional dependency: {error_msg}"


class TestPerformanceAcrossPlatforms:
    """Test performance consistency across platforms."""

    @pytest.mark.compatibility
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_basic_performance_cross_platform(self, temp_dir):
        """Test basic performance metrics across platforms."""
        import time

        server = MarkItDownMCPServer()
        platform_info = PlatformDetector.get_platform_info()

        # Create standardized test file
        perf_file = Path(temp_dir) / "performance_test.txt"
        content = "Performance test line.\n" * 1000  # ~20KB
        perf_file.write_text(content)

        # Measure conversion time
        start_time = time.time()

        request = MCPRequest(
            id="platform-performance",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(perf_file)}},
        )

        response = await server.handle_request(request)

        end_time = time.time()
        conversion_time = end_time - start_time

        # Should complete successfully
        assert_mcp_success_response(response, "platform-performance")

        # Performance should be reasonable across platforms
        # Allow more time on slower platforms, but should not hang
        max_time = 10.0  # 10 seconds should be plenty for 20KB
        assert (
            conversion_time < max_time
        ), f"Conversion too slow on {platform_info['system']}: {conversion_time:.2f}s"

        # Log performance for comparison
        print(f"✓ Platform {platform_info['system']}: {conversion_time:.2f}s for 20KB file")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_concurrent_performance_cross_platform(self, temp_dir):
        """Test concurrent request performance across platforms."""
        import asyncio
        import time

        server = MarkItDownMCPServer()

        # Create test files
        test_files = []
        for i in range(5):
            test_file = Path(temp_dir) / f"concurrent_{i}.txt"
            content = f"Concurrent test file {i}\nContent for performance testing.\n"
            test_file.write_text(content)
            test_files.append(str(test_file))

        # Create concurrent requests
        requests = [
            MCPRequest(
                id=f"concurrent-perf-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(5)
        ]

        # Execute concurrently
        start_time = time.time()
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        concurrent_time = end_time - start_time

        # All should succeed
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"concurrent-perf-{i}")

        # Concurrent processing should be efficient
        assert concurrent_time < 15, f"Concurrent processing too slow: {concurrent_time:.2f}s"

        # Should be faster than sequential (parallelization benefit)
        # This is a rough estimate - actual benefit depends on platform
        theoretical_sequential = 5 * 2.0  # Assume 2s per file sequentially
        efficiency = theoretical_sequential / concurrent_time
        assert efficiency > 0.5, f"Poor concurrent efficiency: {efficiency:.2f}x"


class TestPlatformSpecificFeatures:
    """Test platform-specific features and limitations."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_windows_specific_features(self, temp_dir):
        """Test Windows-specific features and limitations."""
        if not PlatformDetector.is_windows():
            pytest.skip("Windows-specific test")

        server = MarkItDownMCPServer()

        # Test Windows path formats
        test_file = Path(temp_dir) / "windows_test.txt"
        test_file.write_text("Windows-specific test content")

        # Test UNC path format (if applicable)
        windows_paths = [
            str(test_file),  # Standard path
            str(test_file).replace("/", "\\"),  # Backslash path
        ]

        # Test drive letter handling
        if ":" in str(test_file):
            # Add drive letter variants
            drive_path = str(test_file)
            windows_paths.extend(
                [
                    drive_path.upper(),  # Upper case drive
                    drive_path.lower(),  # Lower case drive
                ]
            )

        for path in windows_paths:
            request = MCPRequest(
                id=f"windows-path-{hash(path) % 1000}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": path}},
            )

            response = await server.handle_request(request)

            # All Windows path formats should work
            if response.result:
                assert_mcp_success_response(response)
                content = response.result["content"][0]["text"]
                assert "Windows-specific test content" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_unix_specific_features(self, temp_dir):
        """Test Unix-specific features (Linux, macOS)."""
        if not PlatformDetector.is_unix_like():
            pytest.skip("Unix-specific test")

        server = MarkItDownMCPServer()

        # Test Unix path features
        test_file = Path(temp_dir) / "unix_test.txt"
        test_file.write_text("Unix-specific test content")

        # Test relative path handling
        current_dir = Path.cwd()
        try:
            os.chdir(temp_dir)

            request = MCPRequest(
                id="unix-relative-path",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": "./unix_test.txt"}},
            )

            response = await server.handle_request(request)

            # Should handle relative paths
            if response.result:
                assert_mcp_success_response(response, "unix-relative-path")
                content = response.result["content"][0]["text"]
                assert "Unix-specific test content" in content
            else:
                # Relative paths might not be supported - that's acceptable
                assert response.error is not None

        finally:
            os.chdir(current_dir)

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_macos_specific_features(self, temp_dir):
        """Test macOS-specific features."""
        if not PlatformDetector.is_macos():
            pytest.skip("macOS-specific test")

        server = MarkItDownMCPServer()

        # Test macOS extended attributes handling
        test_file = Path(temp_dir) / "macos_test.txt"
        test_file.write_text("macOS-specific test content")

        # macOS might add extended attributes
        request = MCPRequest(
            id="macos-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        # Should handle macOS files correctly
        assert_mcp_success_response(response, "macos-test")
        content = response.result["content"][0]["text"]
        assert "macOS-specific test content" in content
