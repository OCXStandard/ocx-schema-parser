# -*- coding: utf-8 -*-

#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# This file is execfile()d with the current directory set to its
# containing dir.

from __future__ import unicode_literals

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]
source_suffix = ".rst"
master_doc = "index"
project = "ocx_schema_parser"
year = "2023"
author = "3Docx.org"
copyright = "{0}, {1}".format(year, author)
version = "1.8.5"
release = version
pygments_style = "trac"
templates_path = ["_templates"]
extlinks = {
    "issue": ("https://github.com/OCXStandard/ocx-schema-parser/issues/%s", "#"),
    "pr": ("https://github.com/OCXStandard/ocx-schema-parser/pull/%s", "PR #"),
}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only set the theme if we're building docs locally
    html_theme = "sphinx_rtd_theme"

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_sidebars = {
    "**": ["searchbox.html", "globaltoc.html", "sourcelink.html"],
}
html_short_title = "%s-%s" % (project, version)
html_static_path = ["_static"]
napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
