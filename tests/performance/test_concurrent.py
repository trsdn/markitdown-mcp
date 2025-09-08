"""
Concurrent request handling performance tests.
Tests server performance under concurrent load and resource contention.
"""

import asyncio
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest


class ConcurrencyTestHarness:
    """Test harness for concurrent operation testing."""

    def __init__(self):
        self.server = MarkItDownMCPServer()
        self.results = []
        self.start_time = None
        self.end_time = None

    async def run_concurrent_requests(self, requests: List[MCPRequest]) -> List[Dict[str, Any]]:
        """Run multiple requests concurrently and collect results."""
        self.start_time = time.time()

        # Create tasks for all requests
        tasks = [self._execute_request(req) for req in requests]

        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.time()

        # Process results
        results = []
        for i, (request, response) in enumerate(zip(requests, responses)):
            if isinstance(response, Exception):
                result = {
                    "request_id": request.id,
                    "success": False,
                    "exception": str(response),
                    "response": None,
                }
            else:
                result = {
                    "request_id": request.id,
                    "success": response.result is not None,
                    "response": response,
                    "exception": None,
                }
            results.append(result)

        self.results = results
        return results

    async def _execute_request(self, request: MCPRequest):
        """Execute a single request."""
        return await self.server.handle_request(request)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of concurrent execution."""
        total_time = self.end_time - self.start_time
        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful

        return {
            "total_requests": len(self.results),
            "successful_requests": successful,
            "failed_requests": failed,
            "success_rate": successful / len(self.results) if self.results else 0,
            "total_time": total_time,
            "requests_per_second": len(self.results) / total_time if total_time > 0 else 0,
        }


class TestBasicConcurrency:
    """Test basic concurrent request handling."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_initialize_requests(self):
        """Test multiple concurrent initialization requests."""
        harness = ConcurrencyTestHarness()

        # Create multiple initialization requests
        requests = [
            MCPRequest(id=f"concurrent-init-{i}", method="initialize", params={}) for i in range(10)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0
        assert summary["successful_requests"] == 10

        # Should complete quickly
        assert summary["total_time"] < 5.0
        assert summary["requests_per_second"] > 5

        # Verify all responses are identical and correct
        for result in results:
            response = result["response"]
            assert response.result["serverInfo"]["name"] == "markitdown-server"
            assert response.result["protocolVersion"] == "2024-11-05"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_tools_list_requests(self):
        """Test multiple concurrent tools/list requests."""
        harness = ConcurrencyTestHarness()

        # Create multiple tools list requests
        requests = [
            MCPRequest(id=f"concurrent-tools-{i}", method="tools/list", params={})
            for i in range(15)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0
        assert summary["successful_requests"] == 15

        # Should complete quickly
        assert summary["total_time"] < 3.0
        assert summary["requests_per_second"] > 10

        # Verify all responses are identical
        first_tools = results[0]["response"].result["tools"]
        for result in results[1:]:
            assert result["response"].result["tools"] == first_tools

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_format_list_requests(self):
        """Test multiple concurrent format list requests."""
        harness = ConcurrencyTestHarness()

        # Create multiple format list requests
        requests = [
            MCPRequest(
                id=f"concurrent-formats-{i}",
                method="tools/call",
                params={"name": "list_supported_formats", "arguments": {}},
            )
            for i in range(20)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Should be fast for read-only operations
        assert summary["requests_per_second"] > 15

        # Verify all responses are identical
        first_content = results[0]["response"].result["content"][0]["text"]
        for result in results[1:]:
            content = result["response"].result["content"][0]["text"]
            assert content == first_content


class TestConcurrentFileProcessing:
    """Test concurrent file processing operations."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_file_conversions_same_file(self, temp_dir):
        """Test concurrent conversions of the same file."""
        harness = ConcurrencyTestHarness()

        # Create test file
        test_file = Path(temp_dir) / "concurrent_test.txt"
        test_content = (
            "Concurrent processing test file.\nLine 2 of content.\nLine 3 with more text."
        )
        test_file.write_text(test_content)

        # Create multiple requests for the same file
        requests = [
            MCPRequest(
                id=f"concurrent-same-file-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )
            for i in range(8)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Performance should be reasonable
        assert summary["total_time"] < 10.0
        assert summary["requests_per_second"] > 2

        # Verify all results are identical and correct
        first_content = results[0]["response"].result["content"][0]["text"]
        assert "Concurrent processing test" in first_content

        for result in results[1:]:
            content = result["response"].result["content"][0]["text"]
            assert content == first_content

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_file_conversions_different_files(self, temp_dir):
        """Test concurrent conversions of different files."""
        harness = ConcurrencyTestHarness()

        # Create multiple test files
        test_files = []
        for i in range(12):
            file_path = Path(temp_dir) / f"concurrent_{i:02d}.txt"
            content = (
                f"Test file {i:02d} for concurrent processing.\nUnique content for file {i}.\n"
            )
            file_path.write_text(content)
            test_files.append(str(file_path))

        # Create concurrent requests for different files
        requests = [
            MCPRequest(
                id=f"concurrent-diff-file-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(12)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Performance should be reasonable for I/O bound operations
        assert summary["total_time"] < 15.0
        assert summary["requests_per_second"] > 1.5

        # Verify each result matches its corresponding file
        for i, result in enumerate(results):
            content = result["response"].result["content"][0]["text"]
            assert f"Test file {i:02d}" in content
            assert f"Unique content for file {i}" in content

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_mixed_file_types(self, temp_dir):
        """Test concurrent processing of mixed file types."""
        harness = ConcurrencyTestHarness()

        # Create files of different types
        file_configs = [
            ("text_1.txt", "Plain text file 1.\nMultiple lines of content."),
            ("data_1.json", '{"name": "test", "id": 1, "data": [1, 2, 3]}'),
            ("info_1.csv", "Name,Age,City\nAlice,30,NYC\nBob,25,LA"),
            ("page_1.html", "<html><body><h1>Test Page</h1><p>Content</p></body></html>"),
            ("text_2.txt", "Plain text file 2.\nDifferent content here."),
            ("data_2.json", '{"name": "test2", "id": 2, "data": [4, 5, 6]}'),
            ("info_2.csv", "Product,Price,Stock\nWidget,10.99,50\nGadget,15.99,30"),
            ("page_2.html", "<html><body><h2>Another Page</h2><p>More content</p></body></html>"),
        ]

        test_files = []
        for filename, content in file_configs:
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
            test_files.append(str(file_path))

        # Create concurrent requests for mixed file types
        requests = [
            MCPRequest(
                id=f"concurrent-mixed-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": test_files[i]}},
            )
            for i in range(len(test_files))
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Performance should handle mixed workload
        assert summary["total_time"] < 12.0

        # Verify content by file type
        for i, result in enumerate(results):
            filename = file_configs[i][0]
            content = result["response"].result["content"][0]["text"]

            if filename.endswith(".txt"):
                assert "Plain text file" in content
            elif filename.endswith(".json"):
                assert "test" in content
            elif filename.endswith(".csv"):
                assert "Alice" in content or "Product" in content
            elif filename.endswith(".html"):
                assert "Test Page" in content or "Another Page" in content

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_base64_processing(self):
        """Test concurrent base64 content processing."""
        harness = ConcurrencyTestHarness()

        # Create different base64 encoded contents
        import base64

        contents = [f"Base64 test content {i}.\nLine 2 for content {i}.\n" for i in range(10)]

        encoded_contents = [base64.b64encode(content.encode()).decode() for content in contents]

        # Create concurrent base64 requests
        requests = [
            MCPRequest(
                id=f"concurrent-base64-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {
                        "file_content": encoded_contents[i],
                        "filename": f"base64_test_{i}.txt",
                    },
                },
            )
            for i in range(10)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Should handle base64 processing efficiently
        assert summary["total_time"] < 8.0
        assert summary["requests_per_second"] > 2

        # Verify each result matches its input
        for i, result in enumerate(results):
            content = result["response"].result["content"][0]["text"]
            assert f"Base64 test content {i}" in content


class TestConcurrentDirectoryProcessing:
    """Test concurrent directory processing operations."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_directory_conversions(self, temp_dir):
        """Test concurrent directory processing."""
        harness = ConcurrencyTestHarness()

        # Create multiple directories with files
        num_dirs = 4
        directories = []

        for dir_idx in range(num_dirs):
            dir_path = Path(temp_dir) / f"concurrent_dir_{dir_idx}"
            dir_path.mkdir()

            # Create files in each directory
            for file_idx in range(5):
                file_path = dir_path / f"file_{file_idx}.txt"
                content = f"Directory {dir_idx}, File {file_idx}\nContent for testing."
                file_path.write_text(content)

            directories.append(str(dir_path))

        # Create concurrent directory requests
        requests = [
            MCPRequest(
                id=f"concurrent-dir-{i}",
                method="tools/call",
                params={
                    "name": "convert_directory",
                    "arguments": {
                        "input_directory": directories[i],
                        "output_directory": str(Path(temp_dir) / f"output_{i}"),
                    },
                },
            )
            for i in range(num_dirs)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # All should succeed
        assert summary["success_rate"] == 1.0

        # Directory processing should complete within reasonable time
        assert summary["total_time"] < 30.0

        # Verify each directory result
        for i, result in enumerate(results):
            content = result["response"].result["content"][0]["text"]
            assert "Successfully converted: 5" in content

            # Check output directory exists
            output_dir = Path(temp_dir) / f"output_{i}"
            assert output_dir.exists()
            md_files = list(output_dir.glob("*.md"))
            assert len(md_files) == 5


class TestStressAndLoad:
    """Test server under stress and high load conditions."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, temp_dir):
        """Test server under high concurrent load."""
        harness = ConcurrencyTestHarness()

        # Create test file
        stress_file = Path(temp_dir) / "stress_test.txt"
        content = "Stress test file content.\n" * 100  # Medium-sized content
        stress_file.write_text(content)

        # Create high number of concurrent requests
        num_requests = 50
        requests = [
            MCPRequest(
                id=f"stress-{i:03d}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(stress_file)}},
            )
            for i in range(num_requests)
        ]

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # Should handle high load gracefully
        # Accept some failures under extreme load, but most should succeed
        assert (
            summary["success_rate"] > 0.8
        ), f"Success rate too low under stress: {summary['success_rate']}"

        # Should complete within reasonable time even under load
        assert summary["total_time"] < 60.0

        # Verify successful responses are correct
        for result in results:
            if result["success"]:
                content = result["response"].result["content"][0]["text"]
                assert "Stress test file" in content

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_mixed_load_stress(self, temp_dir):
        """Test server under mixed concurrent load."""
        harness = ConcurrencyTestHarness()

        # Create various test files
        test_files = []

        # Small files
        for i in range(10):
            file_path = Path(temp_dir) / f"small_{i}.txt"
            file_path.write_text(f"Small file {i} content.")
            test_files.append(("small", str(file_path)))

        # Medium files
        for i in range(5):
            file_path = Path(temp_dir) / f"medium_{i}.txt"
            content = f"Medium file {i}.\n" + "Line content.\n" * 500
            file_path.write_text(content)
            test_files.append(("medium", str(file_path)))

        # JSON files
        for i in range(3):
            file_path = Path(temp_dir) / f"data_{i}.json"
            data = {"id": i, "items": list(range(100)), "description": f"Data file {i}"}
            file_path.write_text(json.dumps(data, indent=2))
            test_files.append(("json", str(file_path)))

        # Create mixed concurrent requests
        requests = []
        request_id = 0

        # Add file conversion requests
        for file_type, file_path in test_files:
            requests.append(
                MCPRequest(
                    id=f"mixed-load-{request_id:03d}-{file_type}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": file_path}},
                )
            )
            request_id += 1

        # Add some format list requests
        for i in range(5):
            requests.append(
                MCPRequest(
                    id=f"mixed-load-{request_id:03d}-formats",
                    method="tools/call",
                    params={"name": "list_supported_formats", "arguments": {}},
                )
            )
            request_id += 1

        # Shuffle requests for realistic mixed load
        random.shuffle(requests)

        await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # Should handle mixed load reasonably well
        assert (
            summary["success_rate"] > 0.85
        ), f"Mixed load success rate too low: {summary['success_rate']}"

        # Should complete mixed workload in reasonable time
        assert summary["total_time"] < 45.0
        assert summary["requests_per_second"] > 1.0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_contention_handling(self, temp_dir):
        """Test handling of resource contention scenarios."""
        harness = ConcurrencyTestHarness()

        # Create a larger file that requires more processing
        large_file = Path(temp_dir) / "contention_test.txt"
        content = "Resource contention test.\n" * 5000  # ~100KB
        large_file.write_text(content)

        # Create base64 content that requires temp file creation
        import base64

        base64_content = base64.b64encode(content.encode()).decode()

        # Mix of resource-intensive operations
        requests = []

        # Large file conversions
        for i in range(8):
            requests.append(
                MCPRequest(
                    id=f"contention-large-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
                )
            )

        # Base64 conversions (temp file creation)
        for i in range(6):
            requests.append(
                MCPRequest(
                    id=f"contention-base64-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {
                            "file_content": base64_content,
                            "filename": f"contention_{i}.txt",
                        },
                    },
                )
            )

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # Should handle resource contention gracefully
        assert (
            summary["success_rate"] > 0.75
        ), f"Resource contention handling failed: {summary['success_rate']}"

        # May take longer due to contention, but should complete
        assert summary["total_time"] < 120.0

        # Verify successful responses are correct
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= len(requests) * 0.75

        for result in successful_results:
            content = result["response"].result["content"][0]["text"]
            assert "Resource contention test" in content


class TestErrorHandlingUnderConcurrency:
    """Test error handling under concurrent conditions."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(self):
        """Test handling of errors under concurrent load."""
        harness = ConcurrencyTestHarness()

        # Mix of valid and invalid requests
        requests = []

        # Valid requests
        for i in range(5):
            requests.append(MCPRequest(id=f"valid-{i}", method="initialize", params={}))

        # Invalid requests
        for i in range(5):
            requests.append(
                MCPRequest(id=f"invalid-method-{i}", method="nonexistent/method", params={})
            )

        for i in range(5):
            requests.append(
                MCPRequest(
                    id=f"invalid-file-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": f"/nonexistent/file_{i}.txt"},
                    },
                )
            )

        # Shuffle for realistic error distribution
        random.shuffle(requests)

        results = await harness.run_concurrent_requests(requests)
        summary = harness.get_performance_summary()

        # Should complete all requests (success or failure)
        assert len(results) == 15

        # Should have mix of success and failure
        successful = summary["successful_requests"]
        failed = summary["failed_requests"]

        assert successful == 5  # Only valid requests should succeed
        assert failed == 10  # Invalid requests should fail gracefully

        # Verify error responses are proper
        for result in results:
            if not result["success"] and result["response"]:
                response = result["response"]
                assert response.error is not None
                assert response.error["code"] in [-32600, -32601, -32602, -32603]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_recovery_under_load(self, temp_dir):
        """Test server recovery after errors under concurrent load."""
        harness = ConcurrencyTestHarness()

        # Create valid test file
        valid_file = Path(temp_dir) / "recovery_test.txt"
        valid_file.write_text("Valid file for recovery testing.")

        # Create sequence: valid -> errors -> valid
        requests = []

        # Initial valid requests
        for i in range(3):
            requests.append(
                MCPRequest(
                    id=f"pre-error-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(valid_file)}},
                )
            )

        # Error-inducing requests
        for i in range(4):
            requests.append(
                MCPRequest(
                    id=f"error-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": f"/nonexistent/error_{i}.txt"},
                    },
                )
            )

        # Recovery validation requests
        for i in range(3):
            requests.append(
                MCPRequest(
                    id=f"post-error-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(valid_file)}},
                )
            )

        results = await harness.run_concurrent_requests(requests)
        harness.get_performance_summary()

        # Check that valid requests succeeded and errors failed appropriately
        pre_error_results = [r for r in results if r["request_id"].startswith("pre-error")]
        error_results = [r for r in results if r["request_id"].startswith("error")]
        post_error_results = [r for r in results if r["request_id"].startswith("post-error")]

        # All valid requests should succeed
        assert all(r["success"] for r in pre_error_results)
        assert all(r["success"] for r in post_error_results)

        # All error requests should fail gracefully
        assert all(not r["success"] for r in error_results)

        # Verify server recovered and continued processing correctly
        for result in post_error_results:
            content = result["response"].result["content"][0]["text"]
            assert "Valid file for recovery" in content
