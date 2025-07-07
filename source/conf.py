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

extensions = [
    'sphinx-comments',  # 需要先安装 pip install sphinx-comments
    # ... 其他扩展
]

exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']


comments_config = {
   "utterances": {
      "repo": "zhaojiedi1992/My_Study_MC",
      "issue-term": "pathname",         
        "theme": "github-light",         
        "label": "comments",              
        "crossorigin": "anonymous"        
   }
}