"""Sphinx configuration."""
from datetime import datetime

project = "Send To Kindle"
author = "Max Johnson"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxarg.ext",
]
autodoc_typehints = "description"
html_theme = "furo"
