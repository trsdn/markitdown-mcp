API Reference
=============

This section contains the complete API reference for markitdown-mcp.

.. contents:: Table of Contents
   :local:
   :depth: 2

Core Server Module
------------------

.. automodule:: markitdown_mcp.server
   :members:
   :undoc-members:
   :show-inheritance:

MCP Server Class
----------------

.. autoclass:: markitdown_mcp.server.MarkItDownMCPServer
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:

   .. automethod:: get_tools
   .. automethod:: handle_request
   .. automethod:: convert_file
   .. automethod:: convert_directory
   .. automethod:: list_supported_formats

MCP Protocol Types
------------------

.. autoclass:: markitdown_mcp.server.MCPRequest
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: markitdown_mcp.server.MCPResponse
   :members:
   :undoc-members:
   :show-inheritance:

Security Functions
------------------

Path Validation
~~~~~~~~~~~~~~~

.. autofunction:: markitdown_mcp.server.validate_and_sanitize_path
.. autofunction:: markitdown_mcp.server.get_safe_working_directories

Content Sanitization
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: markitdown_mcp.server.sanitize_unicode_text
.. autofunction:: markitdown_mcp.server.validate_xml_security
.. autofunction:: markitdown_mcp.server.validate_json_security
.. autofunction:: markitdown_mcp.server.validate_csv_security
.. autofunction:: markitdown_mcp.server.validate_file_content_security

Security Utilities
~~~~~~~~~~~~~~~~~~

.. autofunction:: markitdown_mcp.server.secure_compare
.. autofunction:: markitdown_mcp.server.normalize_timing
.. autofunction:: markitdown_mcp.server.validate_base64

Conversion Functions
--------------------

.. autofunction:: markitdown_mcp.server.safe_convert_with_limits
.. autofunction:: markitdown_mcp.server.extract_text_from_binary

Decorators
----------

.. autofunction:: markitdown_mcp.server.with_timeout

Exceptions
----------

.. autoexception:: markitdown_mcp.server.SecurityError
   :members:
   :show-inheritance:

.. autoexception:: markitdown_mcp.server.TimeoutError
   :members:
   :show-inheritance:

Tool Schemas
------------

convert_file
~~~~~~~~~~~~

.. code-block:: json

   {
     "name": "convert_file",
     "description": "Convert a file to Markdown format",
     "inputSchema": {
       "type": "object",
       "properties": {
         "file_path": {
           "type": "string",
           "description": "Path to the file to convert"
         }
       },
       "required": ["file_path"]
     }
   }

convert_directory
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "name": "convert_directory",
     "description": "Convert all supported files in a directory to Markdown",
     "inputSchema": {
       "type": "object",
       "properties": {
         "input_directory": {
           "type": "string",
           "description": "Path to input directory"
         },
         "output_directory": {
           "type": "string",
           "description": "Path to output directory"
         },
         "recursive": {
           "type": "boolean",
           "description": "Process subdirectories recursively",
           "default": false
         }
       },
       "required": ["input_directory", "output_directory"]
     }
   }

list_supported_formats
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "name": "list_supported_formats",
     "description": "List all supported file formats",
     "inputSchema": {
       "type": "object",
       "properties": {}
     }
   }