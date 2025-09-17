"""
Sphinx documentation configuration for markitdown-mcp.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path("..").resolve()))

# Project information
project = "MarkItDown MCP"
copyright = f"{datetime.now(tz=timezone.utc).year}, MarkItDown MCP Contributors"
author = "MarkItDown MCP Contributors"

# The full version, including alpha/beta/rc tags
release = "1.0.0"
version = "1.0.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",  # Auto-generate docs from docstrings
    "sphinx.ext.napoleon",  # Support Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.intersphinx",  # Link to other project's documentation
    "sphinx.ext.githubpages",  # Create .nojekyll file for GitHub Pages
    "sphinx.ext.todo",  # Support TODO directives
    "sphinx_autodoc_typehints",  # Auto-document type hints
    "myst_parser",  # Support Markdown files
    "sphinx_copybutton",  # Add copy button to code blocks
]

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}

autodoc_typehints = "both"
autodoc_typehints_description_target = "documented"
autodoc_type_aliases = {
    "MCPRequest": "markitdown_mcp.server.MCPRequest",
    "MCPResponse": "markitdown_mcp.server.MCPResponse",
}

# Napoleon settings (for Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# MyST parser settings (for Markdown support)
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_image",
    "colon_fence",
    "smartquotes",
    "replacements",
    "linkify",
    "strikethrough",
]

# Source file patterns
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Master document
master_doc = "index"

# Exclude patterns
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/__pycache__",
    "**/*.pyc",
]

# HTML output settings
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_title = f"{project} v{release}"
html_short_title = project
html_static_path = ["_static"] if Path("_static").exists() else []
html_css_files = []
html_js_files = []

# Copy button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |> "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"

# Intersphinx mapping (link to other projects)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "markitdown": ("https://microsoft.github.io/markitdown/", None),
}

# TODO extension settings
todo_include_todos = True
todo_emit_warnings = True

# Suppress specific warnings
suppress_warnings = [
    "autodoc.import_object",  # Suppress import warnings for optional dependencies
]


# Custom setup
def setup(app):
    """Custom Sphinx setup."""
    app.add_css_file("custom.css") if Path("_static/custom.css").exists() else None

    # Add custom config values
    app.add_config_value("mcp_server_version", "1.0.0", "env")
    app.add_config_value("mcp_protocol_version", "2024-11-05", "env")
