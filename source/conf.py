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

comments_config = {
   "utterances": {
      "repo": "zhaojiedi1992/My_Study_MC",
        "issue-term": "pathname",
        "theme": "github-light",
        "crossorigin": "anonymous" ,
   }
}


html_theme_options = {
    'navigation_depth': 4,         # 控制导航层级
    'includehidden': True,         # 显示隐藏页面
    'titles_only': False,          # 是否仅显示标题
    'collapse_navigation': False,  # 禁止自动折叠导航
    'sticky_navigation': True,     # 固定导航栏
    # 'display_version': True,       # 显示版本号（如果项目有版本）
}