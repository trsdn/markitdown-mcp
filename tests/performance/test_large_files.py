"""
Performance tests for large file processing.
Tests server performance with large files and memory efficiency.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict

import psutil
import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_success_response


class PerformanceMonitor:
    """Monitor system performance during tests."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory = None
        self.start_time = None
        self.peak_memory = 0
        self.measurements = []

    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
        self.peak_memory = self.start_memory

    def record_measurement(self, label: str = ""):
        """Record a performance measurement."""
        current_memory = self.process.memory_info().rss
        current_time = time.time()

        self.peak_memory = max(self.peak_memory, current_memory)

        measurement = {
            "label": label,
            "time": current_time - self.start_time,
            "memory_mb": current_memory / (1024 * 1024),
            "memory_delta_mb": (current_memory - self.start_memory) / (1024 * 1024),
        }

        self.measurements.append(measurement)
        return measurement

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        total_time = time.time() - self.start_time
        peak_memory_mb = self.peak_memory / (1024 * 1024)
        memory_delta_mb = (self.peak_memory - self.start_memory) / (1024 * 1024)

        return {
            "total_time": total_time,
            "peak_memory_mb": peak_memory_mb,
            "memory_delta_mb": memory_delta_mb,
            "measurements": self.measurements,
        }


def create_large_text_file(size_mb: int, file_path: Path) -> str:
    """Create a large text file of specified size."""
    # Calculate approximate lines needed
    line_content = "This is line content for performance testing. " * 5  # ~240 chars per line
    line_template = f"Line {{:06d}}: {line_content}\n"
    line_size = len(line_template.format(0).encode("utf-8"))
    lines_needed = (size_mb * 1024 * 1024) // line_size

    # Add 5% buffer to ensure we meet minimum size
    lines_needed = int(lines_needed * 1.05)

    with open(file_path, "w", encoding="utf-8") as f:
        for i in range(lines_needed):
            f.write(f"Line {i:06d}: {line_content}\n")

    return str(file_path)


def create_large_json_file(size_mb: int, file_path: Path) -> str:
    """Create a large JSON file of specified size."""
    # Create large JSON structure
    records = []
    record_size = 500  # Approximate bytes per record
    num_records = (size_mb * 1024 * 1024) // record_size

    # Add buffer to ensure we meet minimum size
    num_records = int(num_records * 1.1)  # Add 10% buffer for JSON formatting overhead

    for i in range(num_records):
        record = {
            "id": i,
            "name": f"Record {i:06d}",
            "description": f"This is a description for record number {i} with some additional content to make it larger.",
            "metadata": {
                "created": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z",
                "tags": [f"tag{j}" for j in range(i % 5)],
                "category": f"category_{i % 10}",
                "priority": i % 3,
            },
            "data": list(range(i % 20)),
        }
        records.append(record)

    data = {"records": records, "total": len(records)}

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return str(file_path)


def create_large_csv_file(size_mb: int, file_path: Path) -> str:
    """Create a large CSV file of specified size."""
    headers = ["ID", "Name", "Email", "Department", "Salary", "Start_Date", "Status", "Notes"]
    header_line = ",".join(headers) + "\n"

    # Sample row (approximate size)
    sample_row = "123456,John Doe Smith,john.doe.smith@company.com,Engineering Department,75000.50,2024-01-01,Active,Some notes about this employee\n"
    row_size = len(sample_row.encode("utf-8"))
    header_size = len(header_line.encode("utf-8"))

    # Calculate number of rows needed, accounting for header
    target_size_bytes = size_mb * 1024 * 1024
    num_rows = (target_size_bytes - header_size) // row_size

    # Add extra rows to ensure we meet the minimum size
    num_rows = int(num_rows * 1.15)  # Add 15% buffer

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(header_line)

        for i in range(num_rows):
            row = f"{i:06d},Employee {i:06d},emp{i:06d}@company.com,Dept {i % 10},{'${:,.2f}'.format(50000 + (i % 50000))},2024-01-{(i % 28) + 1:02d},{'Active' if i % 10 != 0 else 'Inactive'},Notes for employee {i:06d}\n"
            f.write(row)

    return str(file_path)


class TestLargeFilePerformance:
    """Test performance with large files."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_text_file_10mb(self, temp_dir):
        """Test performance with 10MB text file."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create large text file
        large_file = Path(temp_dir) / "large_text_10mb.txt"
        create_large_text_file(10, large_file)

        actual_size_mb = large_file.stat().st_size / (1024 * 1024)
        assert actual_size_mb >= 9, "File should be at least 9MB"

        monitor.start_monitoring()
        monitor.record_measurement("before_conversion")

        # Convert file
        request = MCPRequest(
            id="large-text-10mb",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        response = await server.handle_request(request)

        monitor.record_measurement("after_conversion")
        summary = monitor.get_summary()

        # Verify success
        assert_mcp_success_response(response, "large-text-10mb")

        # Performance assertions
        assert (
            summary["total_time"] < 60
        ), f"Conversion should complete within 60s, took {summary['total_time']:.2f}s"
        assert (
            summary["memory_delta_mb"] < 500
        ), f"Memory usage should be reasonable, used {summary['memory_delta_mb']:.2f}MB extra"

        # Verify content quality
        result_text = response.result["content"][0]["text"]
        assert "performance testing" in result_text
        assert "Line " in result_text

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_json_file_5mb(self, temp_dir):
        """Test performance with 5MB JSON file."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create large JSON file
        large_file = Path(temp_dir) / "large_json_5mb.json"
        create_large_json_file(5, large_file)

        actual_size_mb = large_file.stat().st_size / (1024 * 1024)
        assert actual_size_mb >= 4, "File should be at least 4MB"

        monitor.start_monitoring()

        # Convert file
        request = MCPRequest(
            id="large-json-5mb",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        response = await server.handle_request(request)
        summary = monitor.get_summary()

        # Verify success
        assert_mcp_success_response(response, "large-json-5mb")

        # Performance assertions
        assert (
            summary["total_time"] < 30
        ), f"JSON conversion should complete within 30s, took {summary['total_time']:.2f}s"
        assert (
            summary["memory_delta_mb"] < 300
        ), f"Memory usage should be reasonable, used {summary['memory_delta_mb']:.2f}MB extra"

        # Verify content quality
        result_text = response.result["content"][0]["text"]
        assert "records" in result_text
        assert "Record " in result_text

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_csv_file_8mb(self, temp_dir):
        """Test performance with 8MB CSV file."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create large CSV file
        large_file = Path(temp_dir) / "large_csv_8mb.csv"
        create_large_csv_file(8, large_file)

        actual_size_mb = large_file.stat().st_size / (1024 * 1024)
        assert actual_size_mb >= 7, f"File should be at least 7MB, got {actual_size_mb:.2f}MB"

        monitor.start_monitoring()

        # Convert file
        request = MCPRequest(
            id="large-csv-8mb",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        response = await server.handle_request(request)
        summary = monitor.get_summary()

        # Verify success
        assert_mcp_success_response(response, "large-csv-8mb")

        # Performance assertions
        assert (
            summary["total_time"] < 45
        ), f"CSV conversion should complete within 45s, took {summary['total_time']:.2f}s"
        assert (
            summary["memory_delta_mb"] < 400
        ), f"Memory usage should be reasonable, used {summary['memory_delta_mb']:.2f}MB extra"

        # Verify content quality
        result_text = response.result["content"][0]["text"]
        assert "Employee " in result_text
        assert "@company.com" in result_text

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_very_large_file_50mb(self, temp_dir):
        """Test performance with very large 50MB file."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create very large file
        large_file = Path(temp_dir) / "very_large_50mb.txt"
        create_large_text_file(50, large_file)

        actual_size_mb = large_file.stat().st_size / (1024 * 1024)
        assert actual_size_mb >= 45, "File should be at least 45MB"

        monitor.start_monitoring()

        # Convert file
        request = MCPRequest(
            id="very-large-50mb",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
        )

        response = await server.handle_request(request)
        summary = monitor.get_summary()

        # This might fail due to size - that's acceptable
        if response.result:
            # If successful, check performance
            assert (
                summary["total_time"] < 300
            ), f"Very large conversion should complete within 5min, took {summary['total_time']:.2f}s"
            assert (
                summary["memory_delta_mb"] < 1000
            ), f"Memory usage should be reasonable, used {summary['memory_delta_mb']:.2f}MB extra"

            result_text = response.result["content"][0]["text"]
            assert "performance testing" in result_text

        else:
            # If failed, should be graceful failure
            assert response.error is not None
            error_msg = response.error["message"].lower()
            acceptable_errors = ["size", "large", "memory", "timeout", "processing"]
            assert any(term in error_msg for term in acceptable_errors)


class TestMemoryEfficiency:
    """Test memory efficiency during file processing."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_cleanup_between_files(self, temp_dir):
        """Test that memory is cleaned up between file conversions."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create multiple medium-sized files
        file_size_mb = 2
        num_files = 5

        files = []
        for i in range(num_files):
            file_path = Path(temp_dir) / f"memory_test_{i}.txt"
            create_large_text_file(file_size_mb, file_path)
            files.append(str(file_path))

        monitor.start_monitoring()
        base_memory = monitor.record_measurement("baseline")["memory_mb"]

        peak_memories = []

        # Process each file and monitor memory
        for i, file_path in enumerate(files):
            request = MCPRequest(
                id=f"memory-cleanup-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": file_path}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"memory-cleanup-{i}")

            measurement = monitor.record_measurement(f"after_file_{i}")
            peak_memories.append(measurement["memory_mb"])

        monitor.get_summary()

        # Memory should not continuously grow
        max_memory_growth = max(peak_memories) - base_memory
        assert (
            max_memory_growth < 200
        ), f"Memory growth should be limited, grew {max_memory_growth:.2f}MB"

        # Final memory should not be much higher than baseline
        final_memory_growth = peak_memories[-1] - base_memory
        assert (
            final_memory_growth < 100
        ), f"Final memory should return near baseline, grew {final_memory_growth:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_base64_memory_efficiency(self, temp_dir):
        """Test memory efficiency with base64 content processing."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create content to encode (2MB)
        content = "Base64 memory efficiency test content.\n" * 50000  # ~2MB

        import base64

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

        monitor.start_monitoring()

        # Process base64 content multiple times
        for i in range(3):
            request = MCPRequest(
                id=f"base64-memory-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {
                        "file_content": encoded_content,
                        "filename": f"base64_test_{i}.txt",
                    },
                },
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"base64-memory-{i}")

            monitor.record_measurement(f"after_base64_{i}")

        summary = monitor.get_summary()

        # Memory usage should be reasonable for base64 processing
        assert (
            summary["memory_delta_mb"] < 150
        ), f"Base64 processing memory should be reasonable, used {summary['memory_delta_mb']:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_temporary_file_cleanup_memory(self):
        """Test that temporary files don't cause memory leaks."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create base64 content that creates temporary files
        import base64

        temp_content = "Temporary file cleanup test.\n" * 1000  # ~30KB
        encoded_content = base64.b64encode(temp_content.encode()).decode()

        monitor.start_monitoring()
        base_memory = monitor.record_measurement("baseline")["memory_mb"]

        # Process many base64 files to test temp file cleanup
        for i in range(20):
            request = MCPRequest(
                id=f"temp-cleanup-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {"file_content": encoded_content, "filename": f"temp_{i}.txt"},
                },
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"temp-cleanup-{i}")

        final_memory = monitor.record_measurement("final")["memory_mb"]
        memory_growth = final_memory - base_memory

        # Memory growth should be minimal despite processing many files
        assert (
            memory_growth < 50
        ), f"Temporary file processing should not cause memory growth, grew {memory_growth:.2f}MB"


class TestThroughputPerformance:
    """Test throughput and processing speed."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_small_files_throughput(self, temp_dir):
        """Test throughput with many small files."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create many small files
        num_files = 100
        files = []

        for i in range(num_files):
            file_path = Path(temp_dir) / f"small_{i:03d}.txt"
            content = f"Small file {i} for throughput testing.\nLine 2 of content.\n"
            file_path.write_text(content)
            files.append(str(file_path))

        monitor.start_monitoring()

        # Process all files
        for i, file_path in enumerate(files):
            request = MCPRequest(
                id=f"throughput-{i}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": file_path}},
            )

            response = await server.handle_request(request)
            assert_mcp_success_response(response, f"throughput-{i}")

        summary = monitor.get_summary()

        # Calculate throughput
        files_per_second = num_files / summary["total_time"]

        # Should process at least 10 small files per second
        assert files_per_second > 10, f"Should process >10 files/sec, got {files_per_second:.2f}"

        # Memory usage should be reasonable
        assert (
            summary["memory_delta_mb"] < 100
        ), f"Memory usage should be reasonable, used {summary['memory_delta_mb']:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_directory_processing_throughput(self, temp_dir):
        """Test directory processing throughput."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create directory with mixed file types
        source_dir = Path(temp_dir) / "throughput_test"
        source_dir.mkdir()
        output_dir = Path(temp_dir) / "throughput_output"

        # Create various file types
        file_types = [
            ("txt", "Text file content for throughput testing."),
            ("json", '{"key": "value", "number": 123}'),
            ("csv", "Name,Age\nJohn,30\nJane,25"),
            ("html", "<html><body><h1>Title</h1></body></html>"),
            ("md", "# Markdown\n\nContent here."),
        ]

        files_created = 0
        for i in range(20):  # 20 files of each type = 100 files total
            for ext, content in file_types:
                file_path = source_dir / f"file_{i:02d}.{ext}"
                file_path.write_text(content)
                files_created += 1

        monitor.start_monitoring()

        # Process directory
        request = MCPRequest(
            id="dir-throughput",
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
        summary = monitor.get_summary()

        # Verify success
        assert_mcp_success_response(response, "dir-throughput")

        # Calculate throughput
        files_per_second = files_created / summary["total_time"]

        # Should process at least 5 files per second in directory mode
        assert (
            files_per_second > 5
        ), f"Directory processing should be >5 files/sec, got {files_per_second:.2f}"

        # Verify all files were processed
        result_text = response.result["content"][0]["text"]
        assert f"Successfully converted: {files_created}" in result_text


class TestScalabilityLimits:
    """Test system scalability limits."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_maximum_file_size_handling(self, temp_dir):
        """Test handling of maximum reasonable file sizes."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Test with progressively larger files until we hit limits
        test_sizes = [20, 50, 100]  # MB

        for size_mb in test_sizes:
            large_file = Path(temp_dir) / f"max_size_{size_mb}mb.txt"
            create_large_text_file(size_mb, large_file)

            monitor.start_monitoring()

            request = MCPRequest(
                id=f"max-size-{size_mb}mb",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
            )

            response = await server.handle_request(request)
            summary = monitor.get_summary()

            if response.result:
                # If successful, verify reasonable performance
                assert summary["total_time"] < 600, f"{size_mb}MB file should complete within 10min"
                assert (
                    summary["memory_delta_mb"] < 2000
                ), f"Memory usage should be reasonable for {size_mb}MB file"

                print(
                    f"Successfully processed {size_mb}MB file in {summary['total_time']:.2f}s using {summary['memory_delta_mb']:.2f}MB extra memory"
                )

            else:
                # If failed, should be graceful
                print(f"Failed to process {size_mb}MB file: {response.error['message']}")
                break  # Stop testing larger sizes

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_directory_size_limits(self, temp_dir):
        """Test directory processing with many files."""
        server = MarkItDownMCPServer()
        monitor = PerformanceMonitor()

        # Create directory with many files
        large_dir = Path(temp_dir) / "large_directory"
        large_dir.mkdir()
        output_dir = Path(temp_dir) / "large_output"

        # Create many small files
        num_files = 500
        for i in range(num_files):
            file_path = large_dir / f"file_{i:04d}.txt"
            content = f"File {i} content for directory scaling test.\n"
            file_path.write_text(content)

        monitor.start_monitoring()

        request = MCPRequest(
            id="large-dir-test",
            method="tools/call",
            params={
                "name": "convert_directory",
                "arguments": {
                    "input_directory": str(large_dir),
                    "output_directory": str(output_dir),
                },
            },
        )

        response = await server.handle_request(request)
        summary = monitor.get_summary()

        if response.result:
            # If successful, verify performance
            files_per_second = num_files / summary["total_time"]
            assert files_per_second > 2, f"Should process >2 files/sec even with {num_files} files"

            result_text = response.result["content"][0]["text"]
            assert f"Successfully converted: {num_files}" in result_text

        else:
            # If failed, should be due to reasonable limits
            error_msg = response.error["message"].lower()
            acceptable_errors = ["too many", "limit", "size", "memory", "timeout"]
            assert any(term in error_msg for term in acceptable_errors)
