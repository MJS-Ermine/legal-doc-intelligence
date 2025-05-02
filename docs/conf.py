import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = '法律文件智能處理平台'
copyright = '2024'
author = 'Legal AI Team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

language = 'zh_TW'
