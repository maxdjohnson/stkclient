"""Sphinx configuration."""

from datetime import datetime
from importlib.metadata import version as package_version

project = "Send To Kindle"
author = "Max Johnson"
copyright = f"{datetime.now().year}, {author}"
release = version = package_version("stkclient")
language = "en"
exclude_patterns = ["_build"]
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinxarg.ext",
]
autodoc_typehints = "description"
html_theme = "furo"
