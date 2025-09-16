#!/usr/bin/env python3
"""
Simple script to run the MarkItDown MCP server for testing
"""

def main():
    print(f"Starting MarkItDown MCP Server...")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        from markitdown_mcp.server import main as server_main
        server_main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except ImportError:
        print("Please install the package first: pip install -e .")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()