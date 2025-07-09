# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = '熊猫乐园'
copyright = '2025, zhaojiedi1992@outlook.com'
author = 'zhaojiedi1992@outlook.com'
release = 'v1.0.0'
language = 'zh_CN'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_comments_zhaojiedi', 
   #   'sphinx_tabs.tabs',  # 替代 sphinx-panels 的卡片布局
    # ... 其他扩展
]

exclude_patterns = []




# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
templates_path = ['_templates']
html_css_files = ['custom.css']

comments_config = {
   "utterances": {
      "repo": "zhaojiedi1992/My_Study_MC",
        "issue-term": "pathname",
        "theme": "github-light",
        "crossorigin": "anonymous" ,
   }
}




