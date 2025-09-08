#!/usr/bin/env python3
"""Investigate path traversal behavior."""

import asyncio
from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest

async def test_specific_path():
    """Test specific path to see what happens."""
    server = MarkItDownMCPServer()
    
    request = MCPRequest(
        id="path-test",
        method="tools/call",
        params={
            "name": "convert_file",
            "arguments": {"file_path": "/etc/passwd"}
        }
    )
    
    response = await server.handle_request(request)
    
    if response.result:
        print("SUCCESS - Content returned:")
        content = response.result["content"][0]["text"]
        print(content[:500])  # First 500 chars
        print(f"\n... (total length: {len(content)} chars)")
        
        # Check for sensitive indicators
        sensitive_terms = ["root:", "daemon:", "bin:", "sys:", "adm:"]
        found_sensitive = [term for term in sensitive_terms if term in content.lower()]
        
        if found_sensitive:
            print(f"\n⚠️ WARNING: Found sensitive content indicators: {found_sensitive}")
        else:
            print("\n✓ No obvious sensitive content detected")
            
    elif response.error:
        print("ERROR - Request blocked:")
        print(f"Code: {response.error['code']}")
        print(f"Message: {response.error['message']}")
    else:
        print("UNKNOWN - Neither result nor error")

if __name__ == "__main__":
    asyncio.run(test_specific_path())