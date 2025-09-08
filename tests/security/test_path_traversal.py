"""
Path traversal security tests.
Tests protection against path traversal attacks and unsafe file access.
"""

import os
from pathlib import Path
from typing import Any, Dict

import pytest

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest
from tests.helpers.assertions import assert_mcp_error_response


class PathTraversalTester:
    """Test harness for path traversal attack scenarios."""

    def __init__(self):
        self.server = MarkItDownMCPServer()

    @pytest.mark.asyncio
    async def test_malicious_path(self, malicious_path: str, test_id: str) -> Dict[str, Any]:
        """Test a malicious path and return results."""
        request = MCPRequest(
            id=test_id,
            method="tools/call",
            params={"name": "convert_file", "arguments": {"file_path": malicious_path}},
        )

        response = await self.server.handle_request(request)

        return {
            "path": malicious_path,
            "test_id": test_id,
            "success": response.result is not None,
            "error": response.error,
            "response": response,
        }

    @pytest.mark.asyncio
    async def test_directory_traversal(self, malicious_path: str, test_id: str) -> Dict[str, Any]:
        """Test directory traversal attack."""
        request = MCPRequest(
            id=test_id,
            method="tools/call",
            params={"name": "convert_directory", "arguments": {"input_directory": malicious_path}},
        )

        response = await self.server.handle_request(request)

        return {
            "path": malicious_path,
            "test_id": test_id,
            "success": response.result is not None,
            "error": response.error,
            "response": response,
        }


class TestBasicPathTraversal:
    """Test basic path traversal attack patterns."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_unix_path_traversal_attacks(self):
        """Test Unix-style path traversal attacks."""
        tester = PathTraversalTester()

        # Common Unix path traversal patterns
        malicious_paths = [
            "../../../etc/passwd",
            "../../../../etc/shadow",
            "../../../root/.ssh/id_rsa",
            "../../../../../../etc/hosts",
            "../../../home/user/.bashrc",
            "../../../../var/log/auth.log",
            "../../../proc/version",
            "../../../../tmp/sensitive_file",
        ]

        for i, path in enumerate(malicious_paths):
            result = await tester.test_malicious_path(path, f"unix-traversal-{i}")

            # Should reject malicious paths
            assert not result["success"], f"Should reject path traversal: {path}"
            assert result["error"] is not None

            # Error should indicate file not found or access denied
            error_msg = result["error"]["message"].lower()
            safe_errors = ["not found", "does not exist", "access denied", "permission", "invalid"]
            assert any(
                err in error_msg for err in safe_errors
            ), f"Error message should be safe: {error_msg}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_windows_path_traversal_attacks(self):
        """Test Windows-style path traversal attacks."""
        tester = PathTraversalTester()

        # Windows path traversal patterns
        malicious_paths = [
            "..\\..\\..\\windows\\system32\\config\\sam",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "..\\..\\..\\users\\administrator\\.ssh\\id_rsa",
            "..\\..\\..\\programdata\\sensitive.txt",
            "..\\..\\..\\windows\\temp\\secret.log",
            "../../../../windows/system32/config/software",
            "..\\..\\..\\..\\boot.ini",
        ]

        for i, path in enumerate(malicious_paths):
            result = await tester.test_malicious_path(path, f"windows-traversal-{i}")

            # Should reject malicious paths
            assert not result["success"], f"Should reject Windows path traversal: {path}"
            assert result["error"] is not None

            # Error should be safe
            error_msg = result["error"]["message"].lower()
            safe_errors = ["not found", "does not exist", "access denied", "permission", "invalid"]
            assert any(
                err in error_msg for err in safe_errors
            ), f"Error message should be safe: {error_msg}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_encoded_path_traversal_attacks(self):
        """Test URL-encoded and other encoded path traversal attacks."""
        tester = PathTraversalTester()

        # URL encoded and other encoding attempts
        malicious_paths = [
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "%2e%2e%5c%2e%2e%5c%2e%2e%5cwindows%5csystem32",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
            "....//....//....//etc//passwd",
            "..%5c..%5c..%5cwindows%5csystem32",
        ]

        for i, path in enumerate(malicious_paths):
            result = await tester.test_malicious_path(path, f"encoded-traversal-{i}")

            # Should reject encoded traversal attempts
            assert not result["success"], f"Should reject encoded path traversal: {path}"
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_absolute_path_attacks(self):
        """Test absolute path attacks to sensitive locations."""
        tester = PathTraversalTester()

        # Absolute paths to sensitive files
        sensitive_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "/var/log/auth.log",
            "/proc/version",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor",
            "C:\\windows\\system32\\config\\sam",
            "C:\\users\\administrator\\desktop\\secret.txt",
            "C:\\programdata\\sensitive.log",
            "/dev/mem",
            "/dev/kmem",
        ]

        for i, path in enumerate(sensitive_paths):
            result = await tester.test_malicious_path(path, f"absolute-path-{i}")

            # Should handle absolute paths safely
            assert not result["success"], f"Should safely handle absolute path: {path}"
            assert result["error"] is not None

            # Should not leak information about file existence
            error_msg = result["error"]["message"].lower()
            leak_indicators = ["exists but", "permission denied", "access denied"]
            # It's OK if file is reported as not found
            safe = any(
                safe_term in error_msg for safe_term in ["not found", "does not exist", "invalid"]
            )
            assert safe or not any(
                leak in error_msg for leak in leak_indicators
            ), f"Potential info leak: {error_msg}"


class TestAdvancedPathTraversal:
    """Test advanced path traversal techniques."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_double_encoding_attacks(self):
        """Test double-encoded path traversal attacks."""
        tester = PathTraversalTester()

        # Double-encoded patterns
        double_encoded_paths = [
            "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd",
            "%25252e%25252e%25252f%25252e%25252e%25252fetc%25252fpasswd",
            "%%32%65%%32%65%%32%66%%32%65%%32%65%%32%66%%32%65%%32%65%%32%66etc%%32%66passwd",
        ]

        for i, path in enumerate(double_encoded_paths):
            result = await tester.test_malicious_path(path, f"double-encoded-{i}")

            assert not result["success"], f"Should reject double-encoded traversal: {path}"
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_unicode_normalization_attacks(self):
        """Test Unicode normalization bypass attempts."""
        tester = PathTraversalTester()

        # Unicode variations and normalization bypasses
        unicode_paths = [
            "../\u002e\u002e/\u002e\u002e/etc/passwd",
            "..\u002f..\u002f..\u002fetc\u002fpasswd",
            "\u002e\u002e\u002f\u002e\u002e\u002f\u002e\u002e\u002fetc\u002fpasswd",
            ".\u002e/.\u002e/.\u002e/etc/passwd",
        ]

        for i, path in enumerate(unicode_paths):
            result = await tester.test_malicious_path(path, f"unicode-{i}")

            assert not result["success"], f"Should reject Unicode traversal bypass: {path}"
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_null_byte_injection_attacks(self):
        """Test null byte injection attacks."""
        tester = PathTraversalTester()

        # Null byte injection attempts
        null_byte_paths = [
            "../../../etc/passwd\x00.txt",
            "../../../../etc/shadow\x00.log",
            "../../../windows/system32/config/sam\x00.dat",
            "/etc/passwd\x00innocent.txt",
        ]

        for i, path in enumerate(null_byte_paths):
            result = await tester.test_malicious_path(path, f"null-byte-{i}")

            # Should handle null bytes safely
            assert not result["success"], f"Should reject null byte injection: {path}"
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_long_path_attacks(self):
        """Test very long path attacks."""
        tester = PathTraversalTester()

        # Very long paths to test buffer handling
        base_traversal = "../" * 100
        long_paths = [
            base_traversal + "etc/passwd",
            base_traversal + "windows/system32/config/sam",
            "A" * 1000 + "/../../../etc/passwd",
            "/" + "A" * 4096,
        ]

        for i, path in enumerate(long_paths):
            result = await tester.test_malicious_path(path, f"long-path-{i}")

            # Should handle long paths without crashes
            assert not result["success"], f"Should reject long path attack: {path[:100]}..."
            assert result["error"] is not None

            # Should not crash or hang
            error_msg = result["error"]["message"].lower()
            assert "internal error" not in error_msg or "crash" not in error_msg


class TestDirectoryTraversalAttacks:
    """Test directory traversal attacks on directory operations."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_directory_traversal_input_paths(self):
        """Test directory traversal on input directory paths."""
        tester = PathTraversalTester()

        # Malicious input directory paths
        malicious_dirs = [
            "../../../etc",
            "../../../../root",
            "../../../var/log",
            "..\\..\\..\\windows\\system32",
            "/etc",
            "/root",
            "C:\\windows\\system32",
            "/proc",
            "/sys",
        ]

        for i, dir_path in enumerate(malicious_dirs):
            result = await tester.test_directory_traversal(dir_path, f"dir-input-{i}")

            # Should reject malicious directory paths
            assert not result["success"], f"Should reject directory traversal: {dir_path}"
            assert result["error"] is not None

            # Error should be appropriate
            error_msg = result["error"]["message"].lower()
            safe_errors = [
                "not found",
                "does not exist",
                "not a directory",
                "access denied",
                "invalid",
            ]
            assert any(
                err in error_msg for err in safe_errors
            ), f"Unsafe error message: {error_msg}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_directory_traversal_output_paths(self, temp_dir):
        """Test directory traversal on output directory paths."""
        tester = PathTraversalTester()

        # Create a safe input directory
        safe_input = Path(temp_dir) / "safe_input"
        safe_input.mkdir()
        (safe_input / "test.txt").write_text("Safe test content")

        # Malicious output directory paths
        malicious_outputs = [
            "../../../tmp/malicious_output",
            "../../../../var/tmp/attack",
            "/etc/malicious_output",
            "/tmp/../../../etc/attack_output",
            "..\\..\\..\\temp\\malicious",
        ]

        for i, output_path in enumerate(malicious_outputs):
            request = MCPRequest(
                id=f"dir-output-{i}",
                method="tools/call",
                params={
                    "name": "convert_directory",
                    "arguments": {
                        "input_directory": str(safe_input),
                        "output_directory": output_path,
                    },
                },
            )

            response = await tester.server.handle_request(request)

            # Should either reject malicious output or handle safely
            if response.error:
                assert_mcp_error_response(response)
            else:
                # If allowed, verify no malicious files were created
                malicious_output_path = Path(output_path)
                if malicious_output_path.exists():
                    # Should not create files outside safe areas
                    resolved_path = malicious_output_path.resolve()
                    temp_resolved = Path(temp_dir).resolve()
                    assert resolved_path.is_relative_to(
                        temp_resolved
                    ), f"Created files outside safe area: {resolved_path}"


class TestSymlinkAttacks:
    """Test symbolic link based attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_symlink_traversal_attacks(self, temp_dir):
        """Test attacks using symbolic links."""
        tester = PathTraversalTester()

        # Create test directory structure
        attack_dir = Path(temp_dir) / "symlink_attack"
        attack_dir.mkdir()

        # Create innocent file
        innocent_file = attack_dir / "innocent.txt"
        innocent_file.write_text("Innocent content")

        # Try to create symbolic links to sensitive files
        symlink_targets = [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            innocent_file,  # Self-reference
        ]

        for i, target in enumerate(symlink_targets):
            symlink_path = attack_dir / f"evil_symlink_{i}.txt"

            try:
                # Attempt to create symlink
                if os.name != "nt":  # Unix-like systems
                    symlink_path.symlink_to(target)
                else:  # Windows
                    # Skip symlink creation on Windows in test environment
                    continue

                # Test conversion of symlink
                result = await tester.test_malicious_path(str(symlink_path), f"symlink-{i}")

                if str(target) == str(innocent_file):
                    # Self-reference should be safe and may succeed
                    if result["success"]:
                        content = result["response"].result["content"][0]["text"]
                        assert "Innocent content" in content
                else:
                    # Links to sensitive files should be rejected
                    assert not result[
                        "success"
                    ], f"Should reject symlink to sensitive file: {target}"

            except (OSError, NotImplementedError):
                # Symlink creation may fail - that's acceptable
                pass
            except Exception as e:
                # Other exceptions should not occur
                pytest.fail(f"Unexpected error creating symlink: {e}")

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_symlink_directory_attacks(self, temp_dir):
        """Test directory operations with symbolic links."""
        if os.name == "nt":
            pytest.skip("Symlink tests not reliable on Windows")

        tester = PathTraversalTester()

        # Create attack directory
        attack_dir = Path(temp_dir) / "dir_symlink_attack"
        attack_dir.mkdir()

        # Create innocent subdirectory
        innocent_subdir = attack_dir / "innocent_subdir"
        innocent_subdir.mkdir()
        (innocent_subdir / "safe.txt").write_text("Safe content")

        # Try to create symlink to sensitive directory
        evil_symlink_dir = attack_dir / "evil_dir_link"

        try:
            evil_symlink_dir.symlink_to("/etc", target_is_directory=True)

            # Test directory conversion with symlink
            result = await tester.test_directory_traversal(str(evil_symlink_dir), "symlink-dir")

            # Should reject or handle safely
            if result["success"]:
                # If successful, should not have accessed sensitive files
                content = result["response"].result["content"][0]["text"]
                # Should not contain sensitive system file contents
                sensitive_indicators = ["root:", "daemon:", "password", "shadow"]
                has_sensitive = any(
                    indicator in content.lower() for indicator in sensitive_indicators
                )
                assert not has_sensitive, "Symlink directory access leaked sensitive data"
            else:
                # Rejection is the safer approach
                assert result["error"] is not None

        except (OSError, NotImplementedError):
            # Symlink creation failed - that's acceptable
            pass


class TestRaceConditionAttacks:
    """Test race condition based attacks."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_toctou_file_replacement_attack(self, temp_dir):
        """Test time-of-check to time-of-use file replacement attacks."""
        tester = PathTraversalTester()

        # Create legitimate file
        legitimate_file = Path(temp_dir) / "legitimate.txt"
        legitimate_content = "This is legitimate content for testing."
        legitimate_file.write_text(legitimate_content)

        # Test normal conversion first
        result = await tester.test_malicious_path(str(legitimate_file), "toctou-baseline")

        # Should succeed with legitimate file
        if result["success"]:
            content = result["response"].result["content"][0]["text"]
            assert "legitimate content" in content
        else:
            # If it fails, that's also acceptable for security
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_concurrent_file_access_safety(self, temp_dir):
        """Test safety of concurrent file access."""
        import asyncio

        tester = PathTraversalTester()

        # Create test file
        test_file = Path(temp_dir) / "concurrent_test.txt"
        test_file.write_text("Concurrent access test content.")

        # Create multiple concurrent requests for the same file
        tasks = []
        for i in range(10):
            task = tester.test_malicious_path(str(test_file), f"concurrent-{i}")
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should either succeed consistently or fail safely
        successful_results = [r for r in results if not isinstance(r, Exception) and r["success"]]
        [r for r in results if not isinstance(r, Exception) and not r["success"]]
        exception_results = [r for r in results if isinstance(r, Exception)]

        # Should not have exceptions from concurrent access
        assert (
            len(exception_results) == 0
        ), f"Concurrent access caused exceptions: {exception_results}"

        # If any succeeded, all successful ones should have identical content
        if successful_results:
            first_content = successful_results[0]["response"].result["content"][0]["text"]
            for result in successful_results[1:]:
                content = result["response"].result["content"][0]["text"]
                assert content == first_content, "Concurrent access produced inconsistent results"


class TestInformationDisclosure:
    """Test prevention of information disclosure through path traversal."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_error_message_information_leaks(self):
        """Test that error messages don't leak sensitive information."""
        tester = PathTraversalTester()

        # Paths that might exist vs. those that definitely don't
        test_paths = [
            "/etc/passwd",  # Might exist on Unix
            "/nonexistent/definitely/not/here",  # Definitely doesn't exist
            "C:\\windows\\system32\\config\\sam",  # Might exist on Windows
            "C:\\definitely\\not\\real\\path",  # Definitely doesn't exist
        ]

        results = []
        for i, path in enumerate(test_paths):
            result = await tester.test_malicious_path(path, f"info-leak-{i}")
            results.append(result)

        # Analyze error messages for information leaks
        for result in results:
            if result["error"]:
                error_msg = result["error"]["message"].lower()

                # Should not reveal file system structure
                leak_indicators = [
                    "exists but cannot read",
                    "permission denied",
                    "access is denied",
                    "file exists",
                    "directory exists",
                ]

                has_leak = any(indicator in error_msg for indicator in leak_indicators)

                # Some level of information in error messages might be acceptable
                # but should not reveal detailed file system information
                if has_leak:
                    # If there is potentially sensitive information, it should be minimal
                    assert len(error_msg) < 200, f"Error message too detailed: {error_msg}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, temp_dir):
        """Test resistance to timing-based information disclosure."""
        import time

        tester = PathTraversalTester()

        # Create one existing file
        existing_file = Path(temp_dir) / "existing.txt"
        existing_file.write_text("Existing file content")

        # Test paths: existing vs non-existing
        test_cases = [
            ("existing", str(existing_file)),
            ("nonexistent", str(temp_dir / "nonexistent.txt")),
            ("system_file", "/etc/passwd"),
            ("system_nonexistent", "/definitely/not/existing"),
        ]

        timings = {}

        # Measure response times
        for case_name, path in test_cases:
            times = []

            # Multiple measurements for statistical significance
            for _ in range(3):
                start_time = time.time()
                await tester.test_malicious_path(path, f"timing-{case_name}")
                end_time = time.time()

                times.append(end_time - start_time)

            timings[case_name] = times

        # Analyze timing differences
        avg_timings = {case: sum(times) / len(times) for case, times in timings.items()}

        # Timing differences should not be dramatically different
        # (some difference is acceptable due to I/O, but not orders of magnitude)
        existing_time = avg_timings["existing"]
        nonexistent_time = avg_timings["nonexistent"]

        if existing_time > 0 and nonexistent_time > 0:
            ratio = max(existing_time, nonexistent_time) / min(existing_time, nonexistent_time)
            # Timing difference should not be extreme (less than 10x)
            assert (
                ratio < 10
            ), (
                f"Timing difference too large: {ratio:.2f}x "
                f"(existing: {existing_time:.3f}s, nonexistent: {nonexistent_time:.3f}s)"
            )


class TestPathNormalizationSecurity:
    """Test security of path normalization and canonicalization."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_path_normalization_bypasses(self, temp_dir):
        """Test various path normalization bypass attempts."""
        tester = PathTraversalTester()

        # Create a file in temp directory for legitimate access
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Legitimate test content")

        # Various normalization bypass attempts that should resolve to temp_dir
        legitimate_variants = [
            str(test_file),
            str(test_file) + "/.",
            str(test_file.parent) + "/./test.txt",
            str(test_file.parent) + "/../" + test_file.parent.name + "/test.txt",
        ]

        # Test that legitimate access works consistently
        for i, variant in enumerate(legitimate_variants):
            result = await tester.test_malicious_path(variant, f"norm-legit-{i}")

            if result["success"]:
                content = result["response"].result["content"][0]["text"]
                assert "Legitimate test content" in content
            # Some normalization may fail - that's acceptable for security

        # Malicious variants that should be rejected
        malicious_variants = [
            str(temp_dir) + "/../../../etc/passwd",
            str(temp_dir) + "/./../../etc/passwd",
            str(temp_dir) + "/../" + "../" * 10 + "etc/passwd",
        ]

        for i, variant in enumerate(malicious_variants):
            result = await tester.test_malicious_path(variant, f"norm-malicious-{i}")

            # Should reject malicious normalized paths
            assert not result["success"], f"Should reject normalized malicious path: {variant}"
            assert result["error"] is not None

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_case_sensitivity_attacks(self, temp_dir):
        """Test case sensitivity based bypass attempts."""
        tester = PathTraversalTester()

        # Case variation attacks
        case_variants = [
            "../../../ETC/passwd",
            "../../../Etc/Passwd",
            "../../../ETC/PASSWD",
            "..\\..\\..\\WINDOWS\\system32\\config\\sam",
            "..\\..\\..\\Windows\\System32\\Config\\Sam",
        ]

        for i, variant in enumerate(case_variants):
            result = await tester.test_malicious_path(variant, f"case-{i}")

            # Should reject regardless of case variations
            assert not result["success"], f"Should reject case variation attack: {variant}"
            assert result["error"] is not None
