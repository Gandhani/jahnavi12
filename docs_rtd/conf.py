#
# great_expectations documentation build configuration file, created by
# sphinx-quickstart on Thu Jun  8 23:00:19 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import sys
import uuid

from sphinx.ext.autodoc import between

sys.path.insert(0, os.path.abspath("../"))  # noqa: PTH100


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # 'sphinx_rtd_theme',
    # "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    # 'sphinx.ext.mathjax'
    "sphinx.ext.napoleon",
    "sphinxcontrib.contentui",
    "sphinx_gitstamp",
    # "sphinx.ext.autosectionlabel",
    "sphinxcontrib.discourse",
    "autoapi.extension",
]

autoapi_type = "python"
autoapi_dirs = ["../great_expectations"]
autoapi_add_toctree_entry = False
# autoapi_keep_files = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# discourse url connect
discourse_url = "https://discuss.greatexpectations.io/"

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
index_doc = "index"

# General information about the project.
project = "great_expectations"
copyright = "2020, The Great Expectations Team. "
author = "The Great Expectations Team"
gitstamp_fmt = "%d %b %Y"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ""
# The full version, including alpha/beta/rc tags.
release = ""

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "paraiso-dark"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "logo_only": True,
    "collapse_navigation": False,
    "navigation_depth": 4,
}

html_static_path = [
    "_static",
    "_static/style.css",
    "_static/hk-grotesk-pro/HKGroteskPro-Bold.woff2",
    "_static/hk-grotesk-pro/HKGroteskPro-Regular.woff2",
    "_static/hk-grotesk-pro/HKGroteskPro-SemiBold.woff2",
    "_static/hk-grotesk-pro/HKGroteskPro-Medium.woff2",
    "_static/header-logo.png",
    "_static/discuss-logo.png",
]
html_css_files = ["style.css"]

# html_logo = '../static/img/pip-logo.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".


# -- Options for Napoleon Extension --------------------------------------------

# Parse Google style docstrings.
# See http://google.github.io/styleguide/pyguide.html
napoleon_google_docstring = True

# Parse NumPy style docstrings.
# See https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
napoleon_numpy_docstring = True

# Should special members (like __membername__) and private members
# (like _membername) members be included in the documentation if they
# have docstrings.
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# If True, docstring sections will use the ".. admonition::" directive.
# If False, docstring sections will use the ".. rubric::" directive.
# One may look better than the other depending on what HTML theme is used.
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False

# If True, use Sphinx :ivar: directive for instance variables:
#     :ivar attr1: Description of attr1.
#     :type attr1: type
# If False, use Sphinx .. attribute:: directive for instance variables:
#     .. attribute:: attr1
#
#        *type*
#
#        Description of attr1.
napoleon_use_ivar = False

# If True, use Sphinx :param: directive for function parameters:
#     :param arg1: Description of arg1.
#     :type arg1: type
# If False, output function parameters using the :parameters: field:
#     :parameters: **arg1** (*type*) -- Description of arg1.
napoleon_use_param = True

# If True, use Sphinx :rtype: directive for the return type:
#     :returns: Description of return value.
#     :rtype: type
# If False, output the return type inline with the return description:
#     :returns: *type* -- Description of return value.
napoleon_use_rtype = True


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "great_expectationsdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        index_doc,
        "great_expectations.tex",
        "great_expectations Documentation",
        "The Great Expectations Team",
        "manual",
    ),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(index_doc, "great_expectations", "great_expectations Documentation", [author], 1)]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        index_doc,
        "great_expectations",
        "great_expectations Documentation",
        author,
        "great_expectations",
        "Always know what to expect from your data.",
        "Miscellaneous",
    ),
]


autodoc_member_order = "bysource"


def process_docstring(app, what, name, obj, options, lines):  # noqa: PLR0913
    from docs_rtd.feature_annotation_parser import parse_feature_annotation

    docstring = "\n".join(lines)
    annotation_list = parse_feature_annotation(docstring)

    process_between = between(marker="--ge-feature-maturity-info--", exclude=True)
    process_between(app, what, name, obj, options, lines)

    if not annotation_list:
        return

    feature_annotation_admonition = """
.. admonition:: `Feature Maturity <https://docs.greatexpectations.io/en/latest/features>`_

    """

    feature_annotation_template = """
    |   |icon-{icon_hash}| **{title}** - `How-to Guide <{how_to_guide_url}>`_
    |       {description}
    |       **Maturity**: {maturity}
    |       **Details**:
    |           **API Stability**: {maturity_details[api_stability]}
    |           **Implementation Completeness**: {maturity_details[implementation_completeness]}
    |           **Unit Test Coverage**: {maturity_details[unit_test_coverage]}
    |           **Integration Infrastructure/Test Coverage**: {maturity_details[integration_infrastructure_test_coverage]}
    |           **Documentation Completeness**: {maturity_details[documentation_completeness]}
    |           **Bug Risk**: {maturity_details[bug_risk]}\
"""  # noqa: E501
    expectation_completeness_template = """
    |           **Expectation Completeness**: {maturity_details[expectation_completeness]}\
"""
    icon_template = """
    .. |icon-{icon_hash}| image:: {icon}
              :height: 15px
"""

    for annotation in annotation_list:
        icon_hash = uuid.uuid1().hex
        annotation["icon_hash"] = icon_hash
        description = (
            annotation.get("description")
            or annotation.get("short_description")
            or f"*TODO: {annotation.get('title')} Description*"
        )
        how_to_guide_url = (
            annotation.get("how_to_guide_url")
            or "https://docs.greatexpectations.io/en/latest/how_to_guides.html"
        )
        annotation["how_to_guide_url"] = how_to_guide_url
        annotation["description"] = description

        if annotation["maturity_details"].get("expectation_completeness"):
            feature_annotation_admonition += (
                feature_annotation_template + expectation_completeness_template + icon_template
            ).format(**annotation)
        else:
            feature_annotation_admonition += (feature_annotation_template + icon_template).format(
                **annotation
            )

    lines += feature_annotation_admonition.splitlines()


def setup(app):
    app.connect("autodoc-process-docstring", process_docstring)
