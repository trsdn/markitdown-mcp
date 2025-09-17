=======================================
MarkItDown MCP Documentation
=======================================

.. image:: https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue
   :alt: MCP Protocol

.. image:: https://img.shields.io/github/v/release/trsdn/markitdown-mcp
   :alt: Latest Release

Welcome to the MarkItDown MCP documentation! This Model Context Protocol (MCP) server provides
seamless document-to-Markdown conversion capabilities using Microsoft's MarkItDown library.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   README
   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   guides/usage
   guides/KNOWN_ISSUES
   guides/security

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index
   api/server
   api/tools
   api/security

.. toctree::
   :maxdepth: 2
   :caption: Development
   :hidden:

   development/CONTRIBUTING
   development/TESTING_STRATEGY
   development/CI_CD_SYSTEM
   development/ci-cd-architecture
   development/ci-cd-quick-reference
   development/architecture
   AGENTS
   CHANGELOG

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources
   :hidden:

   examples/index
   faq
   troubleshooting

Quick Links
-----------

* :doc:`Installation Guide <installation>` - Get started with markitdown-mcp
* :doc:`API Reference <api/index>` - Complete API documentation
* :doc:`Security Guide <guides/security>` - Security features and best practices
* :doc:`Contributing <development/CONTRIBUTING>` - How to contribute to the project

Features
--------

**Document Conversion**
   Convert various document formats to Markdown:

   * Microsoft Office (Word, Excel, PowerPoint)
   * PDF documents with text extraction
   * Images with OCR capabilities
   * HTML and XML files
   * Audio transcription (with optional dependencies)

**MCP Tools**
   Three powerful tools exposed via MCP:

   * ``convert_file`` - Convert individual files
   * ``convert_directory`` - Batch convert entire directories
   * ``list_supported_formats`` - Query supported file types

**Security Features**
   Built-in security protections:

   * Path traversal prevention
   * File size limits (configurable)
   * Timeout protection (30s default)
   * Safe directory restrictions
   * Input sanitization for XML/JSON/CSV

Installation
------------

Install via pip::

   pip install markitdown-mcp

Or with all optional dependencies::

   pip install markitdown-mcp[all]

Quick Example
-------------

Using the MCP server with Claude Desktop:

.. code-block:: json

   {
     "mcpServers": {
       "markitdown": {
         "command": "markitdown-mcp",
         "env": {
           "MAX_FILE_SIZE_MB": "100",
           "CONVERSION_TIMEOUT": "60"
         }
       }
     }
   }

Then in Claude::

   Please convert the file /path/to/document.pdf to Markdown

Architecture
------------

The server follows MCP protocol specifications:

1. **Request/Response Model** - JSON-RPC style communication
2. **Tool Discovery** - Clients can query available tools
3. **Type Safety** - Strict input/output validation
4. **Error Handling** - Structured error responses

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`