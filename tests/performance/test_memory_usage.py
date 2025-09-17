"""
Memory usage and efficiency performance tests.
Tests server memory management, leak detection, and efficiency.
"""

import base64
import gc
import json
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict

import psutil
import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_success_response


class MemoryProfiler:
    """Profile memory usage during test execution."""

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = None
        self.peak_memory = 0
        self.measurements = []
        self.tracemalloc_started = False

    def start_profiling(self):
        """Start memory profiling."""
        # Force garbage collection to get clean baseline
        gc.collect()

        # Start tracemalloc for detailed memory tracking
        tracemalloc.start()
        self.tracemalloc_started = True

        # Record baseline
        self.baseline_memory = self.process.memory_info().rss
        self.peak_memory = self.baseline_memory

        self.record_measurement("baseline")

    def record_measurement(self, label: str = "") -> Dict[str, Any]:
        """Record a memory measurement."""
        current_memory = self.process.memory_info().rss
        vms = self.process.memory_info().vms

        self.peak_memory = max(self.peak_memory, current_memory)

        # Get tracemalloc snapshot if available
        tracemalloc_info = None
        if self.tracemalloc_started:
            try:
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics("lineno")
                if top_stats:
                    tracemalloc_info = {
                        "current_mb": sum(stat.size for stat in top_stats) / (1024 * 1024),
                        "top_allocations": len(top_stats),
                    }
            except Exception:
                # Ignore tracemalloc errors if not available
                pass

        measurement = {
            "label": label,
            "timestamp": time.time(),
            "rss_mb": current_memory / (1024 * 1024),
            "vms_mb": vms / (1024 * 1024),
            "rss_delta_mb": (current_memory - self.baseline_memory) / (1024 * 1024),
            "tracemalloc": tracemalloc_info,
        }

        self.measurements.append(measurement)
        return measurement

    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and get summary."""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False

        # Final measurement
        final_measurement = self.record_measurement("final")

        # Calculate summary statistics
        peak_delta = (self.peak_memory - self.baseline_memory) / (1024 * 1024)
        final_delta = final_measurement["rss_delta_mb"]

        # Check for potential memory leaks
        # Adjust threshold for CI environments where import overhead is higher
        leak_threshold = 100 if os.environ.get("CI") else 50  # MB
        potential_leak = final_delta > leak_threshold

        return {
            "baseline_mb": self.baseline_memory / (1024 * 1024),
            "peak_mb": self.peak_memory / (1024 * 1024),
            "final_mb": final_measurement["rss_mb"],
            "peak_delta_mb": peak_delta,
            "final_delta_mb": final_delta,
            "potential_leak": potential_leak,
            "measurements": self.measurements,
        }

    def force_cleanup(self):
        """Force garbage collection and cleanup."""
        gc.collect()
        time.sleep(0.1)  # Allow cleanup to complete


class TestBasicMemoryUsage:
    """Test basic memory usage patterns."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_server_initialization_memory(self):
        """Test memory usage during server initialization."""
        profiler = MemoryProfiler()
        profiler.start_profiling()

        # Create server
        server = MarkItDownMCPServer()
        profiler.record_measurement("server_created")

        # Initialize
        request = MCPRequest(id="init-memory", method="initialize", params={})
        response = await server.handle_request(request)

        assert_mcp_success_response(response, "init-memory")
        profiler.record_measurement("after_init")

        summary = profiler.stop_profiling()

        # Server initialization should use minimal memory
        assert (
            summary["peak_delta_mb"] < 50
        ), f"Server initialization used too much memory: {summary['peak_delta_mb']:.2f}MB"
        assert not summary["potential_leak"], "Potential memory leak detected during initialization"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_file_conversion_memory(self, temp_dir):
        """Test memory usage for single file conversion."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "memory_test.txt"
        content = "Memory usage test file.\n" + "Line of content.\n" * 1000  # ~15KB
        test_file.write_text(content)

        profiler.start_profiling()

        # Convert file
        request = MCPRequest(
            id="memory-convert",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
        )

        response = await server.handle_request(request)
        profiler.record_measurement("after_conversion")

        # Force cleanup
        profiler.force_cleanup()
        profiler.record_measurement("after_cleanup")

        assert_mcp_success_response(response, "memory-convert")
        summary = profiler.stop_profiling()

        # Single file conversion should use minimal memory
        assert (
            summary["peak_delta_mb"] < 20
        ), f"Single file conversion used excessive memory: {summary['peak_delta_mb']:.2f}MB"

        # Memory should return close to baseline after cleanup
        cleanup_delta = summary["measurements"][-2]["rss_delta_mb"]  # after_cleanup measurement
        assert (
            cleanup_delta < 10
        ), f"Memory not properly cleaned up: {cleanup_delta:.2f}MB remaining"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_base64_processing_memory(self):
        """Test memory usage for base64 content processing."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create base64 content (1MB when decoded)
        content = "Base64 memory test content.\n" * 40000  # ~1MB
        encoded_content = base64.b64encode(content.encode()).decode()

        profiler.start_profiling()

        # Process base64 content
        request = MCPRequest(
            id="memory-base64",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "memory_test.txt"},
            },
        )

        response = await server.handle_request(request)
        profiler.record_measurement("after_base64")

        # Cleanup
        profiler.force_cleanup()
        profiler.record_measurement("after_cleanup")

        assert_mcp_success_response(response, "memory-base64")
        summary = profiler.stop_profiling()

        # Base64 processing should be memory efficient
        # Should not use much more than the content size
        assert (
            summary["peak_delta_mb"] < 50
        ), f"Base64 processing used excessive memory: {summary['peak_delta_mb']:.2f}MB"

        # Temporary files should be cleaned up
        cleanup_delta = summary["measurements"][-2]["rss_delta_mb"]
        assert (
            cleanup_delta < 15
        ), f"Base64 temp files not cleaned up: {cleanup_delta:.2f}MB remaining"


class TestMemoryScaling:
    """Test how memory usage scales with workload."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multiple_file_conversions_memory_scaling(self, temp_dir):
        """Test memory scaling with multiple file conversions."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create multiple test files
        test_files = []
        for i in range(20):
            file_path = Path(temp_dir) / f"scaling_test_{i:02d}.txt"
            content = f"Scaling test file {i}.\n" + "Content line.\n" * 500  # ~8KB each
            file_path.write_text(content)
            test_files.append(str(file_path))

        profiler.start_profiling()

        # Process files sequentially and monitor memory
        for i, file_path in enumerate(test_files):
            request = MCPRequest(
                id=f"scaling-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": file_path}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"scaling-{i}")

            profiler.record_measurement(f"file_{i}")

            # Periodic cleanup
            if i % 5 == 4:
                profiler.force_cleanup()
                profiler.record_measurement(f"cleanup_{i}")

        # Final cleanup
        profiler.force_cleanup()
        profiler.record_measurement("final_cleanup")

        summary = profiler.stop_profiling()

        # Memory should not grow linearly with number of files
        # Should plateau due to cleanup between operations
        measurements = summary["measurements"]
        memory_deltas = [m["rss_delta_mb"] for m in measurements if "file_" in m["label"]]

        # Memory growth should be sublinear
        max_delta = max(memory_deltas)
        assert max_delta < 100, f"Memory grew too much with multiple files: {max_delta:.2f}MB"

        # Final memory should be reasonable
        assert (
            summary["final_delta_mb"] < 30
        ), f"Final memory usage too high: {summary['final_delta_mb']:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_file_memory_efficiency(self, temp_dir):
        """Test memory efficiency with large files."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create large file (5MB)
        large_file = Path(temp_dir) / "large_memory_test.txt"
        content = "Large file memory efficiency test.\n" * 200000  # ~5MB
        large_file.write_text(content)

        file_size_mb = large_file.stat().st_size / (1024 * 1024)

        profiler.start_profiling()

        # Convert large file
        request = MCPRequest(
            id="large-memory",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        response = await server.handle_request(request)
        profiler.record_measurement("after_large_file")

        # Cleanup
        profiler.force_cleanup()
        profiler.record_measurement("after_cleanup")

        if response.result:
            assert_mcp_success_response(response, "large-memory")
            summary = profiler.stop_profiling()

            # Memory usage should be proportional to file size, not excessive
            # Should not use much more than 6x file size (increased due to 10MB output limit)
            memory_efficiency_ratio = summary["peak_delta_mb"] / file_size_mb
            assert (
                memory_efficiency_ratio < 6.0
            ), f"Memory efficiency poor: {memory_efficiency_ratio:.2f}x file size"

            # Memory should be cleaned up after processing (adjusted for 10MB output limit)
            cleanup_delta = summary["measurements"][-2]["rss_delta_mb"]
            assert (
                cleanup_delta < file_size_mb * 8
            ), f"Large file memory not cleaned up: {cleanup_delta:.2f}MB"

        else:
            # If large file processing failed, that's acceptable
            assert response.error is not None

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_directory_processing_memory_scaling(self, temp_dir):
        """Test memory scaling with directory processing."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create directory with many files
        source_dir = Path(temp_dir) / "memory_scaling_dir"
        source_dir.mkdir()
        output_dir = Path(temp_dir) / "memory_output"

        num_files = 50
        for i in range(num_files):
            file_path = source_dir / f"file_{i:03d}.txt"
            content = f"Directory scaling file {i}.\n" + "Content line.\n" * 100  # ~1.5KB each
            file_path.write_text(content)

        total_content_size = sum(f.stat().st_size for f in source_dir.glob("*.txt")) / (1024 * 1024)

        profiler.start_profiling()

        # Process directory
        request = MCPRequest(
            id="dir-memory-scaling",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(source_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await server.handle_request(request)
        profiler.record_measurement("after_directory")

        # Cleanup
        profiler.force_cleanup()
        profiler.record_measurement("after_cleanup")

        assert_mcp_success_response(response, "dir-memory-scaling")
        summary = profiler.stop_profiling()

        # Directory processing should be memory efficient
        # Should not load all files into memory simultaneously
        assert (
            summary["peak_delta_mb"] < 200
        ), f"Directory processing used excessive memory: {summary['peak_delta_mb']:.2f}MB"

        # Memory efficiency should be reasonable compared to total content
        if total_content_size > 0:
            efficiency_ratio = summary["peak_delta_mb"] / total_content_size
            assert (
                efficiency_ratio < 100.0
            ), f"Directory processing memory efficiency poor: {efficiency_ratio:.2f}x"


class TestMemoryLeakDetection:
    """Test for memory leaks in various scenarios."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_repeated_conversions_leak_detection(self, temp_dir):
        """Test for memory leaks with repeated file conversions."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create test file
        test_file = Path(temp_dir) / "leak_test.txt"
        content = "Memory leak detection test.\n" + "Line content.\n" * 1000  # ~15KB
        test_file.write_text(content)

        profiler.start_profiling()

        # Perform many repeated conversions
        num_iterations = 30
        for i in range(num_iterations):
            request = MCPRequest(
                id=f"leak-test-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"leak-test-{i}")

            # Record memory every 5 iterations
            if i % 5 == 4:
                profiler.record_measurement(f"iteration_{i}")

        # Final cleanup and measurement
        profiler.force_cleanup()
        profiler.record_measurement("final_cleanup")

        summary = profiler.stop_profiling()

        # Analyze memory trend
        measurements = [m for m in summary["measurements"] if "iteration_" in m["label"]]
        memory_deltas = [m["rss_delta_mb"] for m in measurements]

        # Memory should not continuously grow
        if len(memory_deltas) >= 3:
            # Check if there's a consistent upward trend
            trend_increases = sum(
                1 for i in range(1, len(memory_deltas)) if memory_deltas[i] > memory_deltas[i - 1]
            )
            trend_ratio = trend_increases / (len(memory_deltas) - 1)

            # Should not be consistently increasing (indicating leak)
            assert (
                trend_ratio < 0.7
            ), f"Potential memory leak detected: {trend_ratio:.2%} of measurements show increase"

        # Final memory should not be excessively high
        assert (
            summary["final_delta_mb"] < 50
        ), f"Final memory usage suggests leak: {summary['final_delta_mb']:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_base64_temp_file_cleanup_leak_detection(self):
        """Test for memory leaks in base64 temporary file handling."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create base64 content
        content = "Base64 temp file leak test.\n" * 5000  # ~125KB
        encoded_content = base64.b64encode(content.encode()).decode()

        profiler.start_profiling()

        # Process many base64 files
        num_iterations = 25
        for i in range(num_iterations):
            request = MCPRequest(
                id=f"base64-leak-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {
                        "file_content": encoded_content,
                        "filename": f"leak_test_{i}.txt",
                    },
                },
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"base64-leak-{i}")

            if i % 5 == 4:
                profiler.record_measurement(f"base64_iteration_{i}")

        # Final cleanup
        profiler.force_cleanup()
        profiler.record_measurement("final_cleanup")

        summary = profiler.stop_profiling()

        # Temporary files should not cause memory leaks
        assert (
            summary["final_delta_mb"] < 30
        ), f"Base64 temp file processing suggests leak: {summary['final_delta_mb']:.2f}MB"
        assert not summary["potential_leak"], "Potential memory leak detected in base64 processing"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_handling_memory_leaks(self, temp_dir):
        """Test for memory leaks in error handling scenarios."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create valid file for comparison
        valid_file = Path(temp_dir) / "valid.txt"
        valid_file.write_text("Valid file content.")

        profiler.start_profiling()

        # Mix of valid and error-inducing requests
        for i in range(20):
            if i % 3 == 0:
                # Valid request
                request = MCPRequest(
                    id=f"error-leak-valid-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(valid_file)}},
                )
            else:
                # Error request
                request = MCPRequest(
                    id=f"error-leak-invalid-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": f"/nonexistent/file_{i}.txt"},
                    },
                )

            await server.handle_request(request)
            # Don't assert success - errors are expected

            if i % 5 == 4:
                profiler.record_measurement(f"error_iteration_{i}")

        # Final cleanup
        profiler.force_cleanup()
        profiler.record_measurement("final_cleanup")

        summary = profiler.stop_profiling()

        # Error handling should not cause memory leaks
        assert (
            summary["final_delta_mb"] < 25
        ), f"Error handling suggests memory leak: {summary['final_delta_mb']:.2f}MB"
        assert not summary["potential_leak"], "Potential memory leak detected in error handling"


class TestMemoryStressScenarios:
    """Test memory behavior under stress conditions."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_under_high_load(self, temp_dir):
        """Test memory behavior under high processing load."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        # Create various files for high load test
        files = []

        # Small files
        for i in range(10):
            file_path = Path(temp_dir) / f"small_{i}.txt"
            file_path.write_text(f"Small file {i} content.")
            files.append(str(file_path))

        # Medium files
        for i in range(5):
            file_path = Path(temp_dir) / f"medium_{i}.txt"
            content = f"Medium file {i}.\n" + "Content line.\n" * 1000
            file_path.write_text(content)
            files.append(str(file_path))

        profiler.start_profiling()

        # High load processing
        for iteration in range(3):  # 3 complete rounds
            for i, file_path in enumerate(files):
                request = MCPRequest(
                    id=f"stress-{iteration}-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": file_path}},
                )

                await server.handle_request(request)
                # Accept some failures under stress

            profiler.record_measurement(f"iteration_{iteration}")

            # Periodic cleanup
            if iteration % 2 == 1:
                profiler.force_cleanup()
                profiler.record_measurement(f"cleanup_{iteration}")

        # Final cleanup
        profiler.force_cleanup()
        profiler.record_measurement("final_cleanup")

        summary = profiler.stop_profiling()

        # Under high load, memory should still be managed reasonably
        assert (
            summary["peak_delta_mb"] < 300
        ), f"High load memory usage excessive: {summary['peak_delta_mb']:.2f}MB"
        assert (
            summary["final_delta_mb"] < 100
        ), f"High load final memory too high: {summary['final_delta_mb']:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_recovery_after_large_operations(self, temp_dir):
        """Test memory recovery after processing large operations."""
        profiler = MemoryProfiler()
        server = MarkItDownMCPServer()

        profiler.start_profiling()
        baseline = profiler.record_measurement("initial_baseline")

        # Process several large operations
        large_operations = [
            # Large text file
            ("large_text.txt", "Large text operation.\n" * 50000),  # ~1MB
            # Large JSON
            (
                "large_data.json",
                json.dumps(
                    {"records": [{"id": i, "data": f"Record {i} data"} for i in range(10000)]}
                ),
            ),
            # Large CSV
            (
                "large_data.csv",
                "ID,Name,Description\n"
                + "\n".join([f"{i},Name{i},Description for item {i}" for i in range(20000)]),
            ),
        ]

        for filename, content in large_operations:
            # Create large file
            large_file = Path(temp_dir) / filename
            large_file.write_text(content)

            profiler.record_measurement(f"before_{filename}")

            # Process large file
            request = MCPRequest(
                id=f"large-op-{filename}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
            )

            await server.handle_request(request)

            profiler.record_measurement(f"after_{filename}")

            # Force cleanup after each large operation
            profiler.force_cleanup()
            profiler.record_measurement(f"cleanup_{filename}")

            # Clean up file to save disk space
            large_file.unlink()

        summary = profiler.stop_profiling()

        # Memory should recover after each large operation
        cleanup_measurements = [m for m in summary["measurements"] if "cleanup_" in m["label"]]

        for cleanup_measurement in cleanup_measurements:
            recovery_delta = cleanup_measurement["rss_delta_mb"] - baseline["rss_delta_mb"]
            assert (
                recovery_delta < 50
            ), f"Poor memory recovery after large operation: {recovery_delta:.2f}MB"

        # Final memory should be close to baseline
        final_recovery = summary["final_delta_mb"] - baseline["rss_delta_mb"]
        assert final_recovery < 30, f"Overall memory recovery poor: {final_recovery:.2f}MB"
