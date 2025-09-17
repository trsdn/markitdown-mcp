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