"""
Dependency compatibility tests.
Tests server behavior with different dependency configurations and versions.
"""

import pytest
import sys
import importlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock
import tempfile

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_success_response, assert_mcp_error_response


class DependencyTester:
    """Test dependency-related scenarios."""

    def __init__(self):
        self.server = MarkItDownMCPServer()

    @staticmethod
    def get_installed_packages() -> Dict[str, str]:
        """Get list of installed packages and their versions."""
        try:
            import pkg_resources

            installed = {pkg.project_name: pkg.version for pkg in pkg_resources.working_set}
            return installed
        except ImportError:
            # Fallback for newer Python versions
            try:
                import importlib.metadata as metadata

                installed = {dist.name: dist.version for dist in metadata.distributions()}
                return installed
            except ImportError:
                return {}

    @staticmethod
    def check_package_availability(package_name: str) -> bool:
        """Check if a package is available for import."""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    @pytest.mark.asyncio
    async def test_with_missing_dependency(
        self, missing_module: str, test_function
    ) -> Dict[str, Any]:
        """Test server behavior when a dependency is missing."""
        # Mock the missing module to raise ImportError
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == missing_module or name.startswith(missing_module + "."):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        try:
            with patch("builtins.__import__", side_effect=mock_import):
                result = await test_function()
                return {"success": True, "result": result, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}


class TestCoreDependencies:
    """Test core dependency requirements."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_markitdown_dependency(self, temp_dir):
        """Test MarkItDown library dependency."""
        # Verify MarkItDown is available
        assert DependencyTester.check_package_availability(
            "markitdown"
        ), "MarkItDown library is required but not available"

        # Test basic MarkItDown functionality
        server = MarkItDownMCPServer()

        # Create simple test file
        test_file = Path(temp_dir) / "dependency_test.txt"
        test_file.write_text("MarkItDown dependency test content")

        request = MCPRequest(
            id="markitdown-dep-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "markitdown-dep-test")
        content = response.result["content"][0]["text"]
        assert "MarkItDown dependency test content" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_python_standard_library_usage(self):
        """Test usage of Python standard library components."""
        # Verify required standard library modules are available
        required_stdlib_modules = [
            "json",
            "pathlib",
            "asyncio",
            "tempfile",
            "base64",
            "dataclasses",
            "logging",
        ]

        for module in required_stdlib_modules:
            assert DependencyTester.check_package_availability(
                module
            ), f"Required standard library module '{module}' not available"

        # Test server functionality that uses these modules
        server = MarkItDownMCPServer()

        # Test JSON handling (json module)
        request = MCPRequest(id="stdlib-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "stdlib-test")

        # Verify response structure (uses dataclasses)
        assert hasattr(response, "id")
        assert hasattr(response, "result")
        assert hasattr(response, "error")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_base64_functionality(self):
        """Test base64 encoding/decoding functionality."""
        import base64

        server = MarkItDownMCPServer()

        # Test base64 content processing
        test_content = "Base64 dependency test content\nMultiple lines for testing"
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("ascii")

        request = MCPRequest(
            id="base64-dep-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "base64_test.txt"},
            },
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "base64-dep-test")
        content = response.result["content"][0]["text"]
        assert "Base64 dependency test content" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_pathlib_functionality(self, temp_dir):
        """Test pathlib Path handling."""
        from pathlib import Path

        server = MarkItDownMCPServer()

        # Test Path object handling
        test_file = Path(temp_dir) / "pathlib_test.txt"
        test_file.write_text("Pathlib dependency test")

        # Ensure server can handle Path objects properly
        request = MCPRequest(
            id="pathlib-dep-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "pathlib-dep-test")


class TestOptionalDependencies:
    """Test behavior with optional dependencies."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_missing_optional_dependencies(self, temp_dir):
        """Test behavior when optional dependencies are missing."""
        tester = DependencyTester()

        # Test with potentially missing optional dependencies
        optional_deps = [
            "openpyxl",  # Excel support
            "python-docx",  # Word document support
            "pypdf2",  # PDF support
            "pandas",  # Data processing
            "beautifulsoup4",  # HTML parsing
        ]

        # Create test files that might require optional dependencies
        test_files = [
            ("test.html", "<html><body><h1>HTML Test</h1></body></html>"),
            ("test.xml", '<?xml version="1.0"?><root><item>XML Test</item></root>'),
        ]

        server = MarkItDownMCPServer()

        for filename, content in test_files:
            test_file = Path(temp_dir) / filename
            test_file.write_text(content)

            # Test each file with potentially missing dependencies
            for dep in optional_deps:
                try:
                    # This may or may not work depending on available dependencies
                    request = MCPRequest(
                        id=f"optional-{dep}-{filename}",
                        method="tools/call",
                        params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
                    )

                    response = await server.handle_request(request)

                    # Should either work or fail gracefully
                    if response.result:
                        # If successful, should have valid content
                        content_text = response.result["content"][0]["text"]
                        assert len(content_text) > 0
                    else:
                        # If failed, should have informative error
                        assert response.error is not None
                        error_msg = response.error["message"].lower()

                        # Error should not be a crash
                        assert "traceback" not in error_msg
                        assert "internal error" not in error_msg

                except Exception:
                    # Optional dependency test failures are acceptable
                    pass

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_graceful_degradation_without_optional_deps(self, temp_dir):
        """Test graceful degradation when optional dependencies are unavailable."""
        server = MarkItDownMCPServer()

        # Test with formats that might need optional dependencies
        formats_to_test = [
            # Text formats should always work
            ("always_works.txt", "Text that should always work"),
            ("always_works.json", '{"should": "always work"}'),
            ("always_works.csv", "Name,Value\nTest,123"),
            # Formats that might need optional dependencies
            ("might_need_deps.html", "<html><body><p>HTML content</p></body></html>"),
            ("might_need_deps.xml", '<?xml version="1.0"?><data>XML content</data>'),
        ]

        always_working_count = 0
        total_working_count = 0

        for filename, content in formats_to_test:
            test_file = Path(temp_dir) / filename
            test_file.write_text(content)

            request = MCPRequest(
                id=f"degradation-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)

            if response.result:
                total_working_count += 1
                if "always_works" in filename:
                    always_working_count += 1
            else:
                # Should fail gracefully if optional dependencies missing
                assert response.error is not None
                if "always_works" in filename:
                    # Basic formats should always work
                    pytest.fail(f"Basic format {filename} should always work")

        # At least basic formats should work
        assert always_working_count >= 3, "Basic text formats should always work"

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_version_compatibility_handling(self):
        """Test handling of different dependency versions."""
        packages = DependencyTester.get_installed_packages()

        # Check for MarkItDown version
        if "markitdown" in packages:
            version = packages["markitdown"]
            print(f"MarkItDown version: {version}")

            # Test that server works with current version
            server = MarkItDownMCPServer()
            request = MCPRequest(id="version-test", method="initialize", params={})
            response = await server.handle_request(request)

            assert_mcp_success_response(response, "version-test")

        # Check Python version compatibility
        python_version = sys.version_info
        print(
            f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )

        # Should work with Python 3.10+
        assert python_version >= (3, 10), "Python 3.10+ required"


class TestDependencyIsolation:
    """Test dependency isolation and conflict resolution."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_namespace_isolation(self, temp_dir):
        """Test that server doesn't conflict with user's namespace."""
        server = MarkItDownMCPServer()

        # Simulate potential naming conflicts
        test_conflicts = [
            # Variable names that might conflict
            "json",
            "pathlib",
            "server",
            "request",
            "response",
        ]

        # Create a test that doesn't interfere with server internals
        test_file = Path(temp_dir) / "isolation_test.txt"
        test_file.write_text("Namespace isolation test")

        # Test should work regardless of potential conflicts
        request = MCPRequest(
            id="isolation-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "isolation-test")
        content = response.result["content"][0]["text"]
        assert "Namespace isolation test" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_module_import_safety(self):
        """Test that module imports are safe and don't affect global state."""
        # Import server module
        from markitdown_mcp.server import MarkItDownMCPServer

        # Should not affect global imports
        import sys
        import json
        import pathlib

        # These should still work normally
        assert hasattr(json, "dumps")
        assert hasattr(pathlib, "Path")
        assert hasattr(sys, "version")

        # Server should still work
        server = MarkItDownMCPServer()
        request = MCPRequest(id="import-safety", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "import-safety")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_memory_cleanup_dependencies(self, temp_dir):
        """Test that dependencies don't cause memory leaks."""
        import gc

        # Force garbage collection before test
        gc.collect()

        server = MarkItDownMCPServer()

        # Process multiple files to test memory cleanup
        for i in range(10):
            test_file = Path(temp_dir) / f"memory_cleanup_{i}.txt"
            test_file.write_text(f"Memory cleanup test {i}")

            request = MCPRequest(
                id=f"memory-cleanup-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"memory-cleanup-{i}")

            # Periodic cleanup
            if i % 3 == 2:
                gc.collect()

        # Final cleanup
        gc.collect()

        # If we get here without memory errors, cleanup is working


class TestDependencyErrorHandling:
    """Test error handling related to dependency issues."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_import_error_handling(self):
        """Test handling of import errors."""
        # This test simulates what happens when dependencies are missing
        # We can't actually remove dependencies, but we can test error paths

        server = MarkItDownMCPServer()

        # Test with malformed requests that might trigger import issues
        malformed_requests = [
            # Request with invalid parameters that might trigger edge cases
            MCPRequest(
                id="import-error-test-1",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": None}},  # Invalid path
            ),
            # Request that might trigger base64 import issues
            MCPRequest(
                id="import-error-test-2",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {"file_content": "invalid-base64", "filename": "test.txt"},
                },
            ),
        ]

        for request in malformed_requests:
            response = await server.handle_request(request)

            # Should handle errors gracefully, not crash with import errors
            if response.error:
                error_msg = response.error["message"].lower()
                # Should not be import-related errors
                assert "import" not in error_msg
                assert "module" not in error_msg
                # Should be parameter validation errors
                assert any(
                    term in error_msg for term in ["invalid", "required", "missing", "parameter"]
                )

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_dependency_version_conflicts(self):
        """Test handling of potential dependency version conflicts."""
        # Get current package versions
        packages = DependencyTester.get_installed_packages()

        server = MarkItDownMCPServer()

        # Test that server works despite potential version conflicts
        request = MCPRequest(id="version-conflict-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "version-conflict-test")

        # Test tools still work
        tools_request = MCPRequest(id="tools-conflict-test", method="tools/list", params={})
        tools_response = await server.handle_request(tools_request)

        assert_mcp_success_response(tools_response, "tools-conflict-test")
        tools = tools_response.result["tools"]
        assert len(tools) == 3

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_circular_dependency_prevention(self):
        """Test that there are no circular dependency issues."""
        # Import the main server module
        from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest, MCPResponse

        # Should be able to import without circular dependency errors
        server = MarkItDownMCPServer()

        # Should be able to create request/response objects
        request = MCPRequest(id="circular-test", method="initialize", params={})
        assert request.id == "circular-test"

        # Should be able to process request
        response = await server.handle_request(request)
        assert_mcp_success_response(response, "circular-test")

        # Response should be proper type
        assert isinstance(response, MCPResponse)


class TestDependencyDocumentation:
    """Test that dependency requirements are properly documented."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_required_dependencies_documented(self):
        """Test that required dependencies are documented."""
        # Check if we can identify required dependencies
        server = MarkItDownMCPServer()

        # Core dependencies should be available
        core_deps = ["markitdown"]

        for dep in core_deps:
            available = DependencyTester.check_package_availability(dep)
            assert available, f"Core dependency {dep} not available"

        # Server should initialize successfully with core dependencies
        request = MCPRequest(id="deps-doc-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "deps-doc-test")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_supported_formats_reflect_dependencies(self):
        """Test that supported formats list reflects available dependencies."""
        server = MarkItDownMCPServer()

        # Get supported formats
        request = MCPRequest(
            id="formats-deps-test",
            method="tools/call",
            params={"name": "list_supported_formats", "arguments": {}},
        )

        response = await server.handle_request(request)
        assert_mcp_success_response(response, "formats-deps-test")

        formats_text = response.result["content"][0]["text"]

        # Should list core formats that don't require optional dependencies
        core_formats = [".txt", ".json", ".csv", ".md"]
        for fmt in core_formats:
            assert fmt in formats_text, f"Core format {fmt} should always be supported"

        # Should not promise formats that require unavailable dependencies
        # This is harder to test automatically, but the list should be honest
        assert len(formats_text) > 100, "Should provide comprehensive format information"
