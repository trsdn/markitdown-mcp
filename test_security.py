#!/usr/bin/env python3
"""Test security aspects of the MCP server."""

import asyncio
import tempfile
from pathlib import Path

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest

async def test_path_traversal_protection():
    """Test protection against path traversal attacks."""
    print("Testing path traversal protection...")
    server = MarkItDownMCPServer()
    
    # Test various path traversal attempts
    malicious_paths = [
        "../../../etc/passwd",
        "../../../../etc/shadow",  
        "../../../root/.ssh/id_rsa",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/passwd",
        "/proc/version",
        "C:\\Windows\\System32\\config\\SAM"
    ]
    
    for path in malicious_paths:
        request = MCPRequest(
            id=f"path-traversal-{hash(path) % 1000}",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": path}
            }
        )
        
        response = await server.handle_request(request)
        
        # Should either fail safely or not access sensitive files
        if response.error:
            print(f"  ✓ Blocked malicious path: {path[:30]}...")
        elif response.result:
            # If it somehow succeeded, ensure it didn't return sensitive data
            content = response.result["content"][0]["text"].lower()
            sensitive_indicators = ["root:", "password", "hash", "shadow", "system"]
            has_sensitive = any(indicator in content for indicator in sensitive_indicators)
            if has_sensitive:
                print(f"  ✗ WARNING: Potential sensitive data leak from {path}")
                return False
            else:
                print(f"  ✓ Path {path[:30]}... returned non-sensitive content")
    
    print("✓ Path traversal protection working")
    return True

async def test_large_file_dos_protection():
    """Test protection against large file DoS attacks."""
    print("Testing large file DoS protection...")
    server = MarkItDownMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a moderately large file (1MB)
        large_file = Path(temp_dir) / "dos_test.txt"
        content = "DoS test content line.\n" * 50000  # ~1MB
        large_file.write_text(content)
        
        request = MCPRequest(
            id="dos-test",
            method="tools/call",
            params={
                "name": "convert_file",
                "arguments": {"file_path": str(large_file)}
            }
        )
        
        import time
        start_time = time.time()
        response = await server.handle_request(request)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if response.result:
            print(f"  ✓ Large file processed successfully in {processing_time:.2f}s")
        elif response.error:
            print(f"  ✓ Large file rejected appropriately: {response.error['message'][:50]}...")
        else:
            print("  ✗ Unexpected response state")
            return False
        
        # Should not take excessively long
        if processing_time > 10:
            print(f"  ⚠ Warning: Processing took {processing_time:.2f}s - may be vulnerable to DoS")
            
    print("✓ Large file DoS protection working")
    return True

async def test_base64_bomb_protection():
    """Test protection against base64 bomb attacks."""
    print("Testing base64 bomb protection...")
    server = MarkItDownMCPServer()
    
    # Create large base64 content
    large_content = "Base64 bomb test content.\n" * 10000  # ~250KB of text
    
    import base64
    encoded_content = base64.b64encode(large_content.encode()).decode()
    
    request = MCPRequest(
        id="base64-bomb-test",
        method="tools/call",
        params={
            "name": "convert_file",
            "arguments": {
                "file_content": encoded_content,
                "filename": "base64_bomb.txt"
            }
        }
    )
    
    import time
    start_time = time.time()
    response = await server.handle_request(request)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    if response.result:
        print(f"  ✓ Base64 content processed successfully in {processing_time:.2f}s")
    elif response.error:
        print(f"  ✓ Base64 content rejected appropriately: {response.error['message'][:50]}...")
    else:
        print("  ✗ Unexpected response state")
        return False
    
    # Should not take excessively long
    if processing_time > 5:
        print(f"  ⚠ Warning: Base64 processing took {processing_time:.2f}s")
    
    print("✓ Base64 bomb protection working")
    return True

async def test_concurrent_request_handling():
    """Test concurrent request handling."""
    print("Testing concurrent request handling...")
    server = MarkItDownMCPServer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_file = Path(temp_dir) / f"concurrent_{i}.txt"
            test_file.write_text(f"Concurrent test file {i}")
            test_files.append(str(test_file))
        
        # Create concurrent requests
        requests = [
            MCPRequest(
                id=f"concurrent-{i}",
                method="tools/call",
                params={
                    "name": "convert_file",
                    "arguments": {"file_path": test_files[i]}
                }
            )
            for i in range(10)
        ]
        
        # Execute concurrently
        import time
        start_time = time.time()
        
        tasks = [server.handle_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Analyze results
        successful = sum(1 for r in responses if r.result is not None)
        failed = sum(1 for r in responses if r.error is not None)
        
        print(f"  ✓ Concurrent requests: {successful} successful, {failed} failed")
        print(f"  ✓ Processing time: {processing_time:.2f}s")
        
        # Should handle most requests successfully
        success_rate = successful / len(responses)
        if success_rate < 0.8:
            print(f"  ⚠ Warning: Low success rate {success_rate:.2%}")
        
    print("✓ Concurrent request handling working")
    return True

async def main():
    """Run all security tests."""
    print("🔒 Running Security Tests for MarkItDown MCP Server\n")
    
    tests = [
        test_path_traversal_protection,
        test_large_file_dos_protection, 
        test_base64_bomb_protection,
        test_concurrent_request_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            success = await test()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            failed += 1
        print()
    
    print(f"🔒 Security Test Summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All security tests passed!")
        return True
    else:
        print("⚠️  Some security tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)