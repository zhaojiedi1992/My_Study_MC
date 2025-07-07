# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'My_Study_MC'
copyright = '2025, zhaojiedi1992@outlook.com'
author = 'zhaojiedi1992@outlook.com'
release = 'v1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']



# def setup(app):
#     app.add_js_file('comments.js')

# html_sidebars = {
#     '**': [
#         'sidebarcomments.html',  # 你的自定义模板
#         'localtoc.html',
#         'relations.html',
#         'sourcelink.html',
#         'searchbox.html'
#     ]
# }

# html_js_files = ['comments.js']

comments_config = {
   "utterances": {
      "repo": "zhaojiedi1992/My_Study_MC",
    #   "optional": "config",
   }
}
