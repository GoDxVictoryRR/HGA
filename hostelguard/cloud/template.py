"""
hostelguard/cloud/template.py
Combines modular templates for the HostelGuard Security Dashboard.

Designed for live academic demonstrations and examiner vivas.
All CSS and JS are self-contained so the dashboard functions completely offline.
"""

from hostelguard.cloud.template_base import BASE_HTML_TOP, BASE_HTML_BOTTOM
from hostelguard.cloud.template_ops import TEMPLATE_OPS
from hostelguard.cloud.template_arena import TEMPLATE_ARENA
from hostelguard.cloud.template_diagrams import TEMPLATE_DIAGRAMS

DASHBOARD_HTML_TEMPLATE = (
    BASE_HTML_TOP
    + TEMPLATE_OPS
    + TEMPLATE_ARENA
    + TEMPLATE_DIAGRAMS
    + BASE_HTML_BOTTOM
)
