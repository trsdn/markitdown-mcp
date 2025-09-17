#!/usr/bin/env python3
"""
Generate MCP tool schemas for validation and breaking change detection.

This script generates JSON schemas for all MCP tools exposed by the server,
which can be used for:
1. Schema validation in CI
2. Breaking change detection
3. API documentation
4. Client SDK generation
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to sys.path so we can import the server
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from markitdown_mcp.server import MarkItDownMCPServer, MCPRequest


async def generate_tool_schemas() -> Dict[str, Any]:
    """Generate schemas for all MCP tools."""
    server = MarkItDownMCPServer()

    # Get tools via proper MCP interface
    request = MCPRequest(id="schema-gen", method="tools/list", params={})
    response = await server.handle_request(request)

    if not response.result or "tools" not in response.result:
        raise RuntimeError("Failed to get tools from MCP server")

    tools = response.result["tools"]

    # Create comprehensive schema document
    schema_doc = {
        "version": "2024-11-05",  # MCP protocol version
        "generated_at": "auto-generated",
        "server_info": {
            "name": "markitdown-mcp",
            "version": "1.0.0",
            "description": "MCP server for document to Markdown conversion",
        },
        "tools": tools,
        "tool_schemas": {},
        "stats": {
            "total_tools": len(tools),
            "tool_names": [tool["name"] for tool in tools],
        }
    }

    # Extract individual tool schemas
    for tool in tools:
        schema_doc["tool_schemas"][tool["name"]] = {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["inputSchema"],
            "required_args": tool["inputSchema"].get("required", []),
            "optional_args": [
                prop for prop in tool["inputSchema"].get("properties", {}).keys()
                if prop not in tool["inputSchema"].get("required", [])
            ]
        }

    return schema_doc


def validate_schemas(schemas: Dict[str, Any]) -> bool:
    """Validate generated schemas are correct."""
    try:
        from jsonschema import Draft7Validator

        # Validate each tool schema
        errors = []
        for tool_name, tool_schema in schemas["tool_schemas"].items():
            try:
                # Check that input schema is valid JSON Schema
                Draft7Validator.check_schema(tool_schema["input_schema"])

                # Check required fields
                if "name" not in tool_schema or not tool_schema["name"]:
                    errors.append(f"Tool {tool_name} missing name")

                if "description" not in tool_schema or not tool_schema["description"]:
                    errors.append(f"Tool {tool_name} missing description")

            except Exception as e:
                errors.append(f"Tool {tool_name} schema validation failed: {e}")

        if errors:
            print("❌ Schema validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        print(f"✅ All {len(schemas['tool_schemas'])} tool schemas are valid")
        return True

    except ImportError:
        print("⚠️  jsonschema not available, skipping validation")
        return True


def compare_with_previous(new_schemas: Dict[str, Any], schemas_file: Path) -> None:
    """Compare with previous schemas to detect breaking changes."""
    if not schemas_file.exists():
        print("📝 No previous schemas found, this is the first generation")
        return

    try:
        with open(schemas_file) as f:
            old_schemas = json.load(f)

        breaking_changes = []
        warnings = []

        # Check for removed tools
        old_tools = set(old_schemas.get("tool_schemas", {}).keys())
        new_tools = set(new_schemas["tool_schemas"].keys())

        removed_tools = old_tools - new_tools
        added_tools = new_tools - old_tools

        if removed_tools:
            breaking_changes.extend([f"Removed tool: {tool}" for tool in removed_tools])

        if added_tools:
            warnings.extend([f"Added tool: {tool}" for tool in added_tools])

        # Check for schema changes in existing tools
        for tool_name in old_tools & new_tools:
            old_schema = old_schemas["tool_schemas"][tool_name]
            new_schema = new_schemas["tool_schemas"][tool_name]

            # Check required arguments changes
            old_required = set(old_schema.get("required_args", []))
            new_required = set(new_schema.get("required_args", []))

            added_required = new_required - old_required
            removed_required = old_required - new_required

            if added_required:
                breaking_changes.append(f"Tool {tool_name}: Added required args: {added_required}")

            if removed_required:
                warnings.append(f"Tool {tool_name}: Removed required args: {removed_required}")

        # Report findings
        if breaking_changes:
            print("🚨 BREAKING CHANGES detected:")
            for change in breaking_changes:
                print(f"  - {change}")

        if warnings:
            print("⚠️  Schema changes (non-breaking):")
            for warning in warnings:
                print(f"  - {warning}")

        if not breaking_changes and not warnings:
            print("✅ No breaking changes detected")

    except Exception as e:
        print(f"⚠️  Could not compare with previous schemas: {e}")


async def main():
    """Main entry point."""
    # Ensure schemas directory exists
    schemas_dir = project_root / "schemas"
    schemas_dir.mkdir(exist_ok=True)

    # Generate schemas
    print("🔧 Generating MCP tool schemas...")
    schemas = await generate_tool_schemas()

    # Validate schemas
    if not validate_schemas(schemas):
        sys.exit(1)

    # Output file
    schemas_file = schemas_dir / "mcp-tools.json"

    # Compare with previous version
    compare_with_previous(schemas, schemas_file)

    # Write schemas to file
    with open(schemas_file, "w") as f:
        json.dump(schemas, f, indent=2, sort_keys=True)

    print(f"📄 Schemas written to {schemas_file}")

    # Create individual schema files for each tool
    tools_dir = schemas_dir / "tools"
    tools_dir.mkdir(exist_ok=True)

    for tool_name, tool_schema in schemas["tool_schemas"].items():
        tool_file = tools_dir / f"{tool_name}.json"
        with open(tool_file, "w") as f:
            json.dump(tool_schema, f, indent=2)

    print(f"📁 Individual tool schemas written to {tools_dir}")

    # Print summary
    print("\n📊 Schema Generation Summary:")
    print(f"  - Total tools: {schemas['stats']['total_tools']}")
    print(f"  - Tools: {', '.join(schemas['stats']['tool_names'])}")
    print(f"  - Output: {schemas_file}")


if __name__ == "__main__":
    asyncio.run(main())