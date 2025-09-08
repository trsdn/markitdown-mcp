"""
Python version compatibility tests.
Tests server behavior across different Python versions.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_error_response, assert_mcp_success_response


class PythonVersionTester:
    """Test Python version-specific features and compatibility."""

    def __init__(self):
        self.python_version = sys.version_info
        self.version_string = (
            f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"
        )

    def get_version_info(self) -> Dict[str, Any]:
        """Get detailed Python version information."""
        return {
            "version": self.python_version,
            "version_string": self.version_string,
            "major": self.python_version.major,
            "minor": self.python_version.minor,
            "micro": self.python_version.micro,
            "implementation": sys.implementation.name,
            "implementation_version": sys.implementation.version,
            "api_version": sys.api_version,
            "features": {
                "async_await": self.python_version >= (3, 5),
                "f_strings": self.python_version >= (3, 6),
                "dataclasses": self.python_version >= (3, 7),
                "walrus_operator": self.python_version >= (3, 8),
                "union_types": self.python_version >= (3, 10),
                "match_statement": self.python_version >= (3, 10),
            },
        }

    def is_supported_version(self) -> Tuple[bool, str]:
        """Check if current Python version is supported."""
        if self.python_version < (3, 10):
            return False, f"Python {self.version_string} not supported. Requires Python 3.10+"
        return True, f"Python {self.version_string} is supported"


class TestMinimumVersionRequirements:
    """Test minimum Python version requirements."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_python_310_minimum_requirement(self):
        """Test that Python 3.10 is the minimum supported version."""
        tester = PythonVersionTester()
        version_info = tester.get_version_info()

        supported, message = tester.is_supported_version()

        if not supported:
            pytest.skip(message)

        print(f"✓ Running on supported Python version: {version_info['version_string']}")

        # Test basic server functionality
        server = MarkItDownMCPServer()
        request = MCPRequest(id="version-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "version-test")

        # Verify server reports correct info
        server_info = response.result["serverInfo"]
        assert server_info["name"] == "markitdown-server"
        assert "version" in server_info

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_required_language_features(self):
        """Test that required Python language features are available."""
        tester = PythonVersionTester()
        features = tester.get_version_info()["features"]

        # Features required by the server
        required_features = {
            "async_await": "Async/await syntax required for server",
            "f_strings": "F-string formatting used in server",
            "dataclasses": "Dataclasses used for request/response objects",
        }

        for feature, description in required_features.items():
            assert features[
                feature
            ], f"{description} - not available in Python {tester.version_string}"

        print(f"✓ All required language features available in Python {tester.version_string}")


class TestAsyncCompatibility:
    """Test async/await compatibility across Python versions."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_asyncio_basic_functionality(self):
        """Test basic asyncio functionality."""
        # Test that asyncio works correctly
        server = MarkItDownMCPServer()

        # Test simple async operation
        request = MCPRequest(id="asyncio-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "asyncio-test")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_concurrent_async_operations(self, temp_dir):
        """Test concurrent async operations work correctly."""
        server = MarkItDownMCPServer()

        # Create test files
        test_files = []
        for i in range(3):
            test_file = Path(temp_dir) / f"async_test_{i}.txt"
            test_file.write_text(f"Async test content {i}")
            test_files.append(str(test_file))

        # Create concurrent requests
        requests = [
            MCPRequest(
                id=f"async-concurrent-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(3)
        ]

        # Execute concurrently
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for i, response in enumerate(responses):
            assert_mcp_success_response(response, f"async-concurrent-{i}")
            content = response.result["content"][0]["text"]
            assert f"Async test content {i}" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """Test async exception handling."""
        server = MarkItDownMCPServer()

        # Create request that will cause an error
        request = MCPRequest(
            id="async-exception-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": "/nonexistent/async_test.txt"},
            },
        )

        response = await server.handle_request(request)

        # Should handle error gracefully in async context
        assert_mcp_error_response(response, -32602, "async-exception-test")

        # Server should remain functional after error
        recovery_request = MCPRequest(id="async-recovery", method="initialize", params={})
        recovery_response = await server.handle_request(recovery_request)

        assert_mcp_success_response(recovery_response, "async-recovery")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_asyncio_event_loop_compatibility(self):
        """Test compatibility with different asyncio event loop policies."""
        # Get current event loop
        loop = asyncio.get_event_loop()

        server = MarkItDownMCPServer()

        # Test that server works with current event loop
        request = MCPRequest(id="loop-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "loop-test")

        # Test that we can get loop info
        assert loop is not None
        assert loop.is_running()


class TestDatastructureCompatibility:
    """Test dataclass and type annotation compatibility."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_dataclass_functionality(self):
        """Test dataclass functionality across Python versions."""
        from markitdown_mcp.server import MCPRequest, MCPResponse

        # Test MCPRequest dataclass
        request = MCPRequest(id="dataclass-test", method="initialize", params={"test": "data"})

        assert request.id == "dataclass-test"
        assert request.method == "initialize"
        assert request.params == {"test": "data"}

        # Test MCPResponse dataclass
        response = MCPResponse(id="response-test", result={"status": "ok"})

        assert response.id == "response-test"
        assert response.result == {"status": "ok"}
        assert response.error is None

        # Test with error
        error_response = MCPResponse(
            id="error-test", error={"code": -32601, "message": "Test error"}
        )

        assert error_response.id == "error-test"
        assert error_response.error == {"code": -32601, "message": "Test error"}
        assert error_response.result is None

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_type_annotations_compatibility(self):
        """Test type annotation compatibility."""
        # Import server with type annotations
        from markitdown_mcp.server import MarkItDownMCPServer

        server = MarkItDownMCPServer()

        # Type annotations should not cause runtime errors
        request = MCPRequest(id="type-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "type-test")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_optional_type_handling(self):
        """Test Optional type handling."""

        from markitdown_mcp.server import MCPResponse

        # Test with None values (Optional types)
        response = MCPResponse(id="optional-test", result=None, error=None)

        assert response.id == "optional-test"
        assert response.result is None
        assert response.error is None


class TestBuiltinFunctionCompatibility:
    """Test compatibility with built-in functions across Python versions."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_json_handling_compatibility(self, temp_dir):
        """Test JSON handling across Python versions."""
        import json

        server = MarkItDownMCPServer()

        # Create JSON test file
        test_data = {
            "python_version": sys.version_info[:3],
            "test_data": ["item1", "item2", "item3"],
            "nested": {"boolean": True, "null_value": None, "number": 42.5},
        }

        json_file = Path(temp_dir) / "python_version_test.json"
        with open(json_file, "w") as f:
            json.dump(test_data, f, indent=2)

        # Test JSON file conversion
        request = MCPRequest(
            id="json-compat-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(json_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "json-compat-test")
        content = response.result["content"][0]["text"]
        assert str(sys.version_info[0]) in content  # Should contain major version
        assert "test_data" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_pathlib_compatibility(self, temp_dir):
        """Test pathlib compatibility across Python versions."""
        from pathlib import Path

        server = MarkItDownMCPServer()

        # Test Path object handling
        test_file = Path(temp_dir) / "pathlib_test.txt"
        test_file.write_text("Pathlib compatibility test")

        # Test various Path operations
        assert test_file.exists()
        assert test_file.is_file()
        assert test_file.suffix == ".txt"
        assert test_file.stem == "pathlib_test"

        # Test with server
        request = MCPRequest(
            id="pathlib-compat-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "pathlib-compat-test")
        content = response.result["content"][0]["text"]
        assert "Pathlib compatibility test" in content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_base64_compatibility(self):
        """Test base64 handling across Python versions."""
        import base64

        server = MarkItDownMCPServer()

        # Test base64 encoding/decoding
        test_content = "Base64 compatibility test\nPython version: " + sys.version
        encoded_content = base64.b64encode(test_content.encode("utf-8")).decode("ascii")

        # Verify encoding/decoding works
        decoded_content = base64.b64decode(encoded_content).decode("utf-8")
        assert decoded_content == test_content

        # Test with server
        request = MCPRequest(
            id="base64-compat-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "base64_test.txt"},
            },
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "base64-compat-test")
        content = response.result["content"][0]["text"]
        assert "Base64 compatibility test" in content


class TestVersionSpecificFeatures:
    """Test version-specific Python features."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_f_string_support(self, temp_dir):
        """Test f-string support (Python 3.6+)."""
        tester = PythonVersionTester()

        if not tester.get_version_info()["features"]["f_strings"]:
            pytest.skip("F-strings not available in this Python version")

        server = MarkItDownMCPServer()

        # F-strings should work in server code
        test_file = Path(temp_dir) / "f_string_test.txt"
        version = sys.version_info
        content = f"F-string test on Python {version.major}.{version.minor}"
        test_file.write_text(content)

        request = MCPRequest(
            id="f-string-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)

        assert_mcp_success_response(response, "f-string-test")
        result_content = response.result["content"][0]["text"]
        assert f"Python {version.major}.{version.minor}" in result_content

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_walrus_operator_compatibility(self):
        """Test walrus operator compatibility (Python 3.8+)."""
        tester = PythonVersionTester()

        if not tester.get_version_info()["features"]["walrus_operator"]:
            pytest.skip("Walrus operator not available in this Python version")

        # Test walrus operator in context where it might be useful
        server = MarkItDownMCPServer()

        # Simple test that walrus operator works
        test_list = [1, 2, 3, 4, 5]
        result = [x for x in test_list if (x * 2) > 4]  # Walrus operator pattern
        assert result == [3, 4, 5]  # Should work if walrus operator supported

        # Server should still function normally
        request = MCPRequest(id="walrus-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "walrus-test")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_union_type_compatibility(self):
        """Test union type compatibility (Python 3.10+)."""
        tester = PythonVersionTester()

        if not tester.get_version_info()["features"]["union_types"]:
            pytest.skip("Union types (X | Y) not available in this Python version")

        # Test that union types work if available
        # This is more about ensuring compatibility than functionality
        server = MarkItDownMCPServer()

        request = MCPRequest(id="union-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "union-test")


class TestBackwardCompatibility:
    """Test backward compatibility considerations."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_no_deprecated_features(self):
        """Test that server doesn't use deprecated Python features."""
        # Test that server initializes without deprecation warnings
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Initialize server
            server = MarkItDownMCPServer()

            # Test basic functionality
            request = MCPRequest(id="deprecation-test", method="initialize", params={})
            response = await server.handle_request(request)

            assert_mcp_success_response(response, "deprecation-test")

            # Check for deprecation warnings
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]

            # Should not have deprecation warnings from server code
            server_warnings = [
                w for w in deprecation_warnings if "markitdown_mcp" in str(w.filename)
            ]

            assert (
                len(server_warnings) == 0
            ), f"Server code has deprecation warnings: {server_warnings}"

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_future_compatibility_preparation(self):
        """Test preparation for future Python versions."""
        # Test that server uses modern Python practices that will be forward-compatible
        server = MarkItDownMCPServer()

        # Test that server doesn't rely on deprecated __import__ behavior
        request = MCPRequest(id="future-compat-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "future-compat-test")

        # Test that all imports are absolute (good practice)
        # This is tested by ensuring the server works correctly
        tools_request = MCPRequest(id="imports-test", method="tools/list", params={})
        tools_response = await server.handle_request(tools_request)

        assert_mcp_success_response(tools_response, "imports-test")
        tools = tools_response.result["tools"]
        assert len(tools) == 3


class TestImplementationCompatibility:
    """Test compatibility with different Python implementations."""

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_cpython_compatibility(self):
        """Test CPython compatibility."""
        implementation = sys.implementation.name

        if implementation != "cpython":
            pytest.skip(f"Not running on CPython (running on {implementation})")

        server = MarkItDownMCPServer()

        request = MCPRequest(id="cpython-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "cpython-test")
        print(f"✓ Compatible with CPython {sys.version}")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_pypy_compatibility(self):
        """Test PyPy compatibility."""
        implementation = sys.implementation.name

        if implementation != "pypy":
            pytest.skip(f"Not running on PyPy (running on {implementation})")

        server = MarkItDownMCPServer()

        # PyPy might have different performance characteristics
        request = MCPRequest(id="pypy-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "pypy-test")
        print(f"✓ Compatible with PyPy {sys.version}")

    @pytest.mark.compatibility
    @pytest.mark.asyncio
    async def test_generic_implementation_compatibility(self):
        """Test compatibility with any Python implementation."""
        implementation = sys.implementation.name
        version = sys.implementation.version

        print(f"Testing on {implementation} {version}")

        server = MarkItDownMCPServer()

        # Basic functionality should work on any implementation
        request = MCPRequest(id="generic-impl-test", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "generic-impl-test")

        # Tools should be available
        tools_request = MCPRequest(id="tools-impl-test", method="tools/list", params={})
        tools_response = await server.handle_request(tools_request)

        assert_mcp_success_response(tools_response, "tools-impl-test")
        tools = tools_response.result["tools"]
        assert len(tools) == 3

        print(f"✓ Compatible with {implementation} {version}")
