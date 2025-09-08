"""
Denial of Service (DoS) protection tests.
Tests server resilience against various DoS attack vectors.
"""

import asyncio
import base64
import json
import random
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_error_response, assert_mcp_success_response


class DoSAttackSimulator:
    """Simulate various DoS attack scenarios."""

    def __init__(self):
        self.server = MarkItDownMCPServer()
        self.attack_results = []

    async def simulate_request_flood(
        self, num_requests: int, delay: float = 0
    ) -> List[Dict[str, Any]]:
        """Simulate a flood of requests."""
        requests = []

        # Create many requests
        for i in range(num_requests):
            request = MCPRequest(id=f"flood-{i:04d}", method="initialize", params={})
            requests.append(request)

            if delay > 0:
                await asyncio.sleep(delay)

        # Send all requests concurrently
        start_time = time.time()

        tasks = [self.server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()

        # Analyze results
        results = []
        successful = 0
        failed = 0
        exceptions = 0

        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                exceptions += 1
                result = {
                    "request_id": f"flood-{i:04d}",
                    "success": False,
                    "exception": str(response),
                    "error": None,
                }
            else:
                if response.result:
                    successful += 1
                    result = {
                        "request_id": f"flood-{i:04d}",
                        "success": True,
                        "exception": None,
                        "error": None,
                    }
                else:
                    failed += 1
                    result = {
                        "request_id": f"flood-{i:04d}",
                        "success": False,
                        "exception": None,
                        "error": response.error,
                    }

            results.append(result)

        summary = {
            "total_requests": num_requests,
            "successful": successful,
            "failed": failed,
            "exceptions": exceptions,
            "total_time": end_time - start_time,
            "requests_per_second": (
                num_requests / (end_time - start_time) if end_time > start_time else 0
            ),
            "results": results,
        }

        self.attack_results.append(summary)
        return results

    async def simulate_resource_exhaustion_attack(
        self, attack_type: str, **kwargs
    ) -> Dict[str, Any]:
        """Simulate resource exhaustion attacks."""
        start_time = time.time()

        if attack_type == "large_files":
            return await self._large_file_attack(**kwargs)
        elif attack_type == "many_concurrent":
            return await self._concurrent_attack(**kwargs)
        elif attack_type == "base64_bomb":
            return await self._base64_bomb_attack(**kwargs)
        elif attack_type == "complex_processing":
            return await self._complex_processing_attack(**kwargs)
        else:
            raise ValueError(f"Unknown attack type: {attack_type}")

    async def _large_file_attack(
        self, file_size_mb: int = 50, temp_dir: str = None
    ) -> Dict[str, Any]:
        """Attack with very large files."""
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()

        # Create very large file
        large_file = Path(temp_dir) / f"dos_large_{file_size_mb}mb.txt"
        content = "DoS attack large file content.\n" * (file_size_mb * 1024 * 32)  # Approximate MB

        try:
            large_file.write_text(content)

            request = MCPRequest(
                id="dos-large-file",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(large_file)}},
            )

            start_time = time.time()
            response = await self.server.handle_request(request)
            end_time = time.time()

            return {
                "attack_type": "large_file",
                "file_size_mb": file_size_mb,
                "success": response.result is not None,
                "error": response.error,
                "processing_time": end_time - start_time,
                "completed": True,
            }

        except Exception as e:
            return {
                "attack_type": "large_file",
                "file_size_mb": file_size_mb,
                "success": False,
                "error": {"message": str(e)},
                "processing_time": time.time() - start_time,
                "completed": False,
                "exception": str(e),
            }
        finally:
            # Cleanup
            try:
                large_file.unlink()
            except:
                pass

    async def _concurrent_attack(
        self, num_concurrent: int = 100, file_size_kb: int = 100
    ) -> Dict[str, Any]:
        """Attack with many concurrent requests."""
        temp_dir = tempfile.mkdtemp()

        # Create test file
        test_file = Path(temp_dir) / "dos_concurrent.txt"
        content = "DoS concurrent attack test.\n" * (file_size_kb * 32)  # Approximate KB
        test_file.write_text(content)

        # Create many concurrent requests
        requests = []
        for i in range(num_concurrent):
            request = MCPRequest(
                id=f"dos-concurrent-{i:03d}",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(test_file)}},
            )
            requests.append(request)

        try:
            start_time = time.time()

            # Execute concurrently
            tasks = [self.server.handle_request(req) for req in requests]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()

            # Analyze results
            successful = sum(
                1 for r in responses if not isinstance(r, Exception) and r.result is not None
            )
            failed = sum(1 for r in responses if not isinstance(r, Exception) and r.result is None)
            exceptions = sum(1 for r in responses if isinstance(r, Exception))

            return {
                "attack_type": "concurrent",
                "num_concurrent": num_concurrent,
                "successful": successful,
                "failed": failed,
                "exceptions": exceptions,
                "success_rate": successful / num_concurrent if num_concurrent > 0 else 0,
                "processing_time": end_time - start_time,
                "completed": True,
            }

        except Exception as e:
            return {
                "attack_type": "concurrent",
                "num_concurrent": num_concurrent,
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "completed": False,
                "exception": str(e),
            }
        finally:
            # Cleanup
            try:
                test_file.unlink()
                Path(temp_dir).rmdir()
            except:
                pass

    async def _base64_bomb_attack(self) -> Dict[str, Any]:
        """Attack with large base64 content."""
        # Create large content
        large_content = "DoS base64 bomb attack.\n" * (5 * 1024 * 1024)  # 5MB of text
        encoded_content = base64.b64encode(large_content.encode()).decode()

        request = MCPRequest(
            id="dos-base64-bomb",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_content": encoded_content, "filename": "dos_base64_bomb.txt"},
            },
        )

        try:
            start_time = time.time()
            response = await self.server.handle_request(request)
            end_time = time.time()

            return {
                "attack_type": "base64_bomb",
                "content_size_mb": len(encoded_content) / (1024 * 1024),
                "success": response.result is not None,
                "error": response.error,
                "processing_time": end_time - start_time,
                "completed": True,
            }

        except Exception as e:
            return {
                "attack_type": "base64_bomb",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "completed": False,
                "exception": str(e),
            }

    async def _complex_processing_attack(self, temp_dir: str = None) -> Dict[str, Any]:
        """Attack with computationally complex files."""
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()

        # Create deeply nested JSON that's expensive to parse
        complex_data = {"level": 0, "data": "root"}
        for i in range(100):  # 100 levels deep
            complex_data = {
                "level": i + 1,
                "nested": complex_data,
                "array": [complex_data.copy() for _ in range(10)],  # Exponential growth
                "metadata": {
                    "index": i,
                    "description": f"Level {i} with complex nesting",
                    "references": list(range(100)),
                },
            }

        complex_file = Path(temp_dir) / "dos_complex.json"

        try:
            with open(complex_file, "w") as f:
                json.dump(complex_data, f)

            request = MCPRequest(
                id="dos-complex-processing",
                method="tools/call",
                params={"name": "convert_file", "arguments": {"file_path": str(complex_file)}},
            )

            start_time = time.time()
            response = await self.server.handle_request(request)
            end_time = time.time()

            return {
                "attack_type": "complex_processing",
                "file_size_mb": complex_file.stat().st_size / (1024 * 1024),
                "success": response.result is not None,
                "error": response.error,
                "processing_time": end_time - start_time,
                "completed": True,
            }

        except Exception as e:
            return {
                "attack_type": "complex_processing",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "completed": False,
                "exception": str(e),
            }
        finally:
            # Cleanup
            try:
                complex_file.unlink()
            except:
                pass


class TestRequestFloodProtection:
    """Test protection against request flooding attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_moderate_request_flood(self):
        """Test handling of moderate request flood."""
        simulator = DoSAttackSimulator()

        # Simulate moderate flood (50 requests)
        results = await simulator.simulate_request_flood(50)

        # Server should handle moderate load
        summary = simulator.attack_results[0]

        # Should handle most requests successfully
        success_rate = summary["successful"] / summary["total_requests"]
        assert success_rate > 0.8, f"Success rate too low under moderate load: {success_rate:.2%}"

        # Should not have exceptions (crashes)
        assert summary["exceptions"] == 0, f"Server crashed with {summary['exceptions']} exceptions"

        # Should complete in reasonable time
        assert (
            summary["total_time"] < 30
        ), f"Moderate flood took too long: {summary['total_time']:.2f}s"

    @pytest.mark.security
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_heavy_request_flood(self):
        """Test handling of heavy request flood."""
        simulator = DoSAttackSimulator()

        # Simulate heavy flood (200 requests)
        results = await simulator.simulate_request_flood(200)

        summary = simulator.attack_results[0]

        # Under heavy load, some failures are acceptable
        success_rate = summary["successful"] / summary["total_requests"]
        assert success_rate > 0.5, f"Success rate too low under heavy load: {success_rate:.2%}"

        # Should not crash completely
        assert summary["exceptions"] < summary["total_requests"] * 0.1, "Too many server exceptions"

        # Should complete without hanging
        assert (
            summary["total_time"] < 120
        ), f"Heavy flood took too long: {summary['total_time']:.2f}s"

        # Server should remain responsive
        assert (
            summary["requests_per_second"] > 2
        ), f"Server too slow: {summary['requests_per_second']:.2f} req/s"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_burst_vs_sustained_load(self):
        """Test difference between burst and sustained load."""
        simulator = DoSAttackSimulator()

        # Test burst load (all at once)
        burst_results = await simulator.simulate_request_flood(30, delay=0)
        burst_summary = simulator.attack_results[0]

        # Reset for sustained test
        simulator.attack_results.clear()

        # Test sustained load (with delays)
        sustained_results = await simulator.simulate_request_flood(30, delay=0.1)
        sustained_summary = simulator.attack_results[0]

        # Sustained load should perform better
        burst_success_rate = burst_summary["successful"] / burst_summary["total_requests"]
        sustained_success_rate = (
            sustained_summary["successful"] / sustained_summary["total_requests"]
        )

        # Either both should work well, or sustained should be better
        assert (
            sustained_success_rate >= burst_success_rate - 0.1
        ), f"Sustained load performed worse: {sustained_success_rate:.2%} vs burst {burst_success_rate:.2%}"

        # Both should avoid crashes
        assert burst_summary["exceptions"] == 0, "Burst load caused crashes"
        assert sustained_summary["exceptions"] == 0, "Sustained load caused crashes"


class TestResourceExhaustionProtection:
    """Test protection against resource exhaustion attacks."""

    @pytest.mark.security
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_file_dos_protection(self, temp_dir):
        """Test protection against large file DoS attacks."""
        simulator = DoSAttackSimulator()

        # Test with progressively larger files
        file_sizes = [10, 25, 50]  # MB

        for size_mb in file_sizes:
            result = await simulator.simulate_resource_exhaustion_attack(
                "large_files", file_size_mb=size_mb, temp_dir=temp_dir
            )

            # Should complete without hanging
            assert result["completed"], f"Large file attack {size_mb}MB didn't complete"

            # Should not take excessively long
            assert (
                result["processing_time"] < 180
            ), f"Large file {size_mb}MB took too long: {result['processing_time']:.2f}s"

            # If it fails, should fail gracefully
            if not result["success"]:
                assert (
                    result["error"] is not None
                ), f"Large file {size_mb}MB failed without error message"

                error_msg = result["error"]["message"].lower()
                acceptable_errors = ["size", "large", "memory", "timeout", "processing"]
                assert any(
                    term in error_msg for term in acceptable_errors
                ), f"Unexpected error for large file {size_mb}MB: {error_msg}"

    @pytest.mark.security
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_request_dos_protection(self):
        """Test protection against concurrent request DoS."""
        simulator = DoSAttackSimulator()

        # Test with high concurrency
        result = await simulator.simulate_resource_exhaustion_attack(
            "many_concurrent", num_concurrent=75, file_size_kb=50
        )

        # Should complete without crashing
        assert result["completed"], "Concurrent attack didn't complete"

        # Should handle reasonable percentage successfully
        success_rate = result["success_rate"]
        assert success_rate > 0.6, f"Concurrent attack success rate too low: {success_rate:.2%}"

        # Should not have too many exceptions
        exception_rate = result["exceptions"] / result["num_concurrent"]
        assert (
            exception_rate < 0.1
        ), f"Too many exceptions in concurrent attack: {exception_rate:.2%}"

        # Should complete in reasonable time
        assert (
            result["processing_time"] < 120
        ), f"Concurrent attack took too long: {result['processing_time']:.2f}s"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_base64_bomb_dos_protection(self):
        """Test protection against base64 bomb DoS."""
        simulator = DoSAttackSimulator()

        result = await simulator.simulate_resource_exhaustion_attack("base64_bomb")

        # Should complete without hanging
        assert result["completed"], "Base64 bomb attack didn't complete"

        # Should complete in reasonable time
        assert (
            result["processing_time"] < 60
        ), f"Base64 bomb took too long: {result['processing_time']:.2f}s"

        # If it fails, should fail gracefully with appropriate error
        if not result["success"]:
            error_msg = result["error"]["message"].lower()
            acceptable_errors = ["size", "large", "memory", "base64", "decode", "processing"]
            assert any(
                term in error_msg for term in acceptable_errors
            ), f"Unexpected error for base64 bomb: {error_msg}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_complex_processing_dos_protection(self, temp_dir):
        """Test protection against complex processing DoS."""
        simulator = DoSAttackSimulator()

        result = await simulator.simulate_resource_exhaustion_attack(
            "complex_processing", temp_dir=temp_dir
        )

        # Should complete without hanging
        assert result["completed"], "Complex processing attack didn't complete"

        # Should complete in reasonable time (complex processing may take longer)
        assert (
            result["processing_time"] < 120
        ), f"Complex processing took too long: {result['processing_time']:.2f}s"

        # If it fails, should fail with appropriate error
        if not result["success"]:
            error_msg = result["error"]["message"].lower()
            acceptable_errors = [
                "complex",
                "nested",
                "depth",
                "recursion",
                "size",
                "memory",
                "processing",
                "timeout",
            ]
            assert any(
                term in error_msg for term in acceptable_errors
            ), f"Unexpected error for complex processing: {error_msg}"


class TestTimeBasedDoSProtection:
    """Test protection against time-based DoS attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_slowloris_style_attack(self):
        """Test protection against slow request attacks."""
        server = MarkItDownMCPServer()

        # Create requests that might be processed slowly
        slow_requests = []

        # Mix of quick and potentially slow operations
        for i in range(20):
            if i % 3 == 0:
                # Quick operation
                request = MCPRequest(id=f"slow-attack-quick-{i}", method="initialize", params={})
            elif i % 3 == 1:
                # Format list (should be quick)
                request = MCPRequest(
                    id=f"slow-attack-formats-{i}",
                    method="tools/call",
                    params={"name": "list_supported_formats", "arguments": {}},
                )
            else:
                # File operation with non-existent file (should fail quickly)
                request = MCPRequest(
                    id=f"slow-attack-file-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": f"/nonexistent/slow_{i}.txt"},
                    },
                )

            slow_requests.append(request)

        # Process with artificial delays between requests
        start_time = time.time()
        results = []

        for i, request in enumerate(slow_requests):
            # Add small delay to simulate slow client
            if i > 0:
                await asyncio.sleep(0.05)  # 50ms delay

            response = await server.handle_request(request)
            results.append(response)

        end_time = time.time()
        total_time = end_time - start_time

        # Should handle slow requests without timing out
        assert total_time < 30, f"Slow request handling took too long: {total_time:.2f}s"

        # All requests should complete
        assert len(results) == len(slow_requests), "Not all slow requests completed"

        # Should handle different request types appropriately
        successful = sum(1 for r in results if r.result is not None)
        failed = sum(1 for r in results if r.error is not None)

        # Most should succeed (init and formats) or fail gracefully (non-existent files)
        assert successful + failed == len(results), "Some requests had neither result nor error"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_timeout_protection(self, temp_dir):
        """Test that processing has timeout protection."""
        server = MarkItDownMCPServer()

        # Create file that might take a while to process
        slow_file = Path(temp_dir) / "timeout_test.json"

        # Create large, complex JSON
        large_data = {"deeply_nested": {}, "large_array": []}

        # Create deep nesting
        current = large_data["deeply_nested"]
        for i in range(50):  # Deep but not excessive nesting
            current["level"] = i
            current["data"] = f"Level {i} data"
            current["nested"] = {}
            current = current["nested"]

        # Create large array
        large_data["large_array"] = [
            {"id": i, "data": f"Item {i}", "metadata": list(range(10))} for i in range(10000)
        ]

        with open(slow_file, "w") as f:
            json.dump(large_data, f)

        # Test with timeout expectation
        start_time = time.time()

        request = MCPRequest(
            id="timeout-test",
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": str(slow_file)}},
        )

        response = await server.handle_request(request)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete in reasonable time or fail with timeout
        assert (
            processing_time < 60
        ), f"Processing should timeout or complete quickly, took {processing_time:.2f}s"

        # Should either succeed or fail gracefully
        assert response.result is not None or response.error is not None

        if response.error:
            error_msg = response.error["message"].lower()
            # If it fails, might be due to size, complexity, or timeout
            acceptable_errors = ["timeout", "large", "complex", "processing", "memory", "size"]
            assert any(
                term in error_msg for term in acceptable_errors
            ), f"Unexpected error message: {error_msg}"


class TestRecoveryFromDoSAttacks:
    """Test server recovery after DoS attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_recovery_after_resource_exhaustion(self, temp_dir):
        """Test server recovery after resource exhaustion."""
        simulator = DoSAttackSimulator()

        # First, perform resource exhaustion attack
        exhaustion_result = await simulator.simulate_resource_exhaustion_attack(
            "large_files", file_size_mb=20, temp_dir=temp_dir
        )

        # Server should complete the attack (success or failure)
        assert exhaustion_result["completed"], "Resource exhaustion didn't complete"

        # Now test if server is still responsive
        recovery_requests = []
        for i in range(5):
            request = MCPRequest(id=f"recovery-{i}", method="initialize", params={})
            recovery_requests.append(request)

        # Test recovery
        recovery_start = time.time()
        recovery_tasks = [simulator.server.handle_request(req) for req in recovery_requests]
        recovery_responses = await asyncio.gather(*recovery_tasks, return_exceptions=True)
        recovery_time = time.time() - recovery_start

        # Server should recover quickly
        assert recovery_time < 10, f"Server recovery took too long: {recovery_time:.2f}s"

        # All recovery requests should succeed
        successful_recovery = sum(
            1 for r in recovery_responses if not isinstance(r, Exception) and r.result is not None
        )

        assert successful_recovery == len(
            recovery_requests
        ), f"Server didn't fully recover: {successful_recovery}/{len(recovery_requests)} requests succeeded"

        # Should not have exceptions during recovery
        recovery_exceptions = sum(1 for r in recovery_responses if isinstance(r, Exception))
        assert (
            recovery_exceptions == 0
        ), f"Server had {recovery_exceptions} exceptions during recovery"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_recovery_after_concurrent_attack(self):
        """Test server recovery after concurrent attack."""
        simulator = DoSAttackSimulator()

        # Perform concurrent attack
        concurrent_result = await simulator.simulate_resource_exhaustion_attack(
            "many_concurrent", num_concurrent=50, file_size_kb=25
        )

        assert concurrent_result["completed"], "Concurrent attack didn't complete"

        # Test immediate recovery
        recovery_request = MCPRequest(id="post-concurrent-recovery", method="tools/list", params={})

        recovery_start = time.time()
        recovery_response = await simulator.server.handle_request(recovery_request)
        recovery_time = time.time() - recovery_start

        # Should recover immediately
        assert recovery_time < 5, f"Post-concurrent recovery took too long: {recovery_time:.2f}s"

        # Should function normally
        assert_mcp_success_response(recovery_response, "post-concurrent-recovery")

        # Should return expected tools
        tools = recovery_response.result["tools"]
        assert (
            len(tools) == 3
        ), f"Server not fully functional after concurrent attack: {len(tools)} tools"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_graceful_degradation_under_load(self):
        """Test that server degrades gracefully under sustained load."""
        simulator = DoSAttackSimulator()

        # Create sustained load over time
        load_phases = [
            {"requests": 10, "delay": 0.1},  # Light load
            {"requests": 25, "delay": 0.05},  # Medium load
            {"requests": 50, "delay": 0.02},  # Heavy load
            {"requests": 10, "delay": 0.1},  # Back to light load
        ]

        phase_results = []

        for i, phase in enumerate(load_phases):
            print(f"Phase {i+1}: {phase['requests']} requests with {phase['delay']}s delay")

            phase_start = time.time()
            results = await simulator.simulate_request_flood(
                phase["requests"], delay=phase["delay"]
            )
            phase_time = time.time() - phase_start

            summary = simulator.attack_results[-1]  # Latest result

            phase_results.append(
                {
                    "phase": i + 1,
                    "requests": phase["requests"],
                    "success_rate": summary["successful"] / summary["total_requests"],
                    "avg_response_time": phase_time / phase["requests"],
                    "exceptions": summary["exceptions"],
                }
            )

            # Small delay between phases
            await asyncio.sleep(0.5)

        # Analyze graceful degradation
        for i, result in enumerate(phase_results):
            # Should not crash in any phase
            assert result["exceptions"] == 0, f"Phase {i+1} had {result['exceptions']} exceptions"

            # Should maintain reasonable success rates
            assert (
                result["success_rate"] > 0.7
            ), f"Phase {i+1} success rate too low: {result['success_rate']:.2%}"

            # Response times should be reasonable
            assert (
                result["avg_response_time"] < 2.0
            ), f"Phase {i+1} response time too high: {result['avg_response_time']:.2f}s"

        # Recovery phase should perform as well as initial phase
        initial_success = phase_results[0]["success_rate"]
        recovery_success = phase_results[-1]["success_rate"]

        assert (
            recovery_success >= initial_success - 0.1
        ), f"Server didn't recover to initial performance: {recovery_success:.2%} vs {initial_success:.2%}"


class TestDoSMitigationStrategies:
    """Test various DoS mitigation strategies."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_request_rate_handling(self):
        """Test how server handles different request rates."""
        server = MarkItDownMCPServer()

        # Test different request patterns
        patterns = [
            {"name": "steady", "requests": 20, "delay": 0.1},
            {"name": "burst", "requests": 20, "delay": 0.0},
            {"name": "slow", "requests": 10, "delay": 0.5},
        ]

        pattern_results = {}

        for pattern in patterns:
            requests = []
            for i in range(pattern["requests"]):
                request = MCPRequest(
                    id=f"{pattern['name']}-{i:02d}", method="initialize", params={}
                )
                requests.append(request)

            start_time = time.time()

            if pattern["delay"] > 0:
                # Sequential with delay
                responses = []
                for request in requests:
                    response = await server.handle_request(request)
                    responses.append(response)
                    await asyncio.sleep(pattern["delay"])
            else:
                # Concurrent
                tasks = [server.handle_request(req) for req in requests]
                responses = await asyncio.gather(*tasks)

            end_time = time.time()

            successful = sum(1 for r in responses if r.result is not None)
            success_rate = successful / len(responses)

            pattern_results[pattern["name"]] = {
                "success_rate": success_rate,
                "total_time": end_time - start_time,
                "avg_response_time": (end_time - start_time) / len(responses),
            }

        # All patterns should succeed
        for pattern_name, result in pattern_results.items():
            assert (
                result["success_rate"] > 0.9
            ), f"{pattern_name} pattern failed: {result['success_rate']:.2%}"

            # Response times should be reasonable
            assert (
                result["avg_response_time"] < 1.0
            ), f"{pattern_name} too slow: {result['avg_response_time']:.2f}s"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_error_handling_under_dos(self, temp_dir):
        """Test that error handling remains robust under DoS conditions."""
        server = MarkItDownMCPServer()

        # Create mix of valid and invalid requests under load
        requests = []

        # Valid requests
        valid_file = Path(temp_dir) / "valid_dos_test.txt"
        valid_file.write_text("Valid content for DoS test")

        for i in range(15):
            requests.append(
                MCPRequest(
                    id=f"dos-valid-{i}",
                    method="tools/call",
                    params={"name": "convert_file", "arguments": {"file_path": str(valid_file)}},
                )
            )

        # Invalid requests (should cause errors)
        for i in range(15):
            requests.append(
                MCPRequest(
                    id=f"dos-invalid-{i}",
                    method="tools/call",
                    params={
                        "name": "convert_file",
                        "arguments": {"file_path": f"/nonexistent/dos_{i}.txt"},
                    },
                )
            )

        # Unknown method requests
        for i in range(10):
            requests.append(MCPRequest(id=f"dos-unknown-{i}", method="unknown/method", params={}))

        # Shuffle to create realistic mixed load
        random.shuffle(requests)

        # Process all requests concurrently
        start_time = time.time()
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Analyze results
        successful = sum(
            1 for r in responses if not isinstance(r, Exception) and r.result is not None
        )
        errored = sum(1 for r in responses if not isinstance(r, Exception) and r.error is not None)
        exceptions = sum(1 for r in responses if isinstance(r, Exception))

        # Should handle mixed load without crashes
        assert exceptions == 0, f"DoS with errors caused {exceptions} exceptions"

        # Should have appropriate mix of success and errors
        expected_successful = 15  # Valid file requests
        expected_errors = 25  # Invalid file + unknown method requests

        # Allow some tolerance for DoS conditions
        assert (
            successful >= expected_successful * 0.8
        ), f"Too few successful requests under DoS: {successful}/{expected_successful}"

        assert (
            errored >= expected_errors * 0.8
        ), f"Error handling failed under DoS: {errored}/{expected_errors}"

        # Should complete in reasonable time even under mixed load
        assert (
            end_time - start_time < 60
        ), f"Mixed DoS load took too long: {end_time - start_time:.2f}s"

        # Error responses should still be properly formatted
        error_responses = [
            r for r in responses if not isinstance(r, Exception) and r.error is not None
        ]

        for error_response in error_responses[:5]:  # Check first 5
            assert error_response.error["code"] in [
                -32600,
                -32601,
                -32602,
                -32603,
            ], f"Invalid error code under DoS: {error_response.error}"

            assert "message" in error_response.error, "Error missing message under DoS"
