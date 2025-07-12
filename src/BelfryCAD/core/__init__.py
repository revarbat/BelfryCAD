"""
Core functionality for BelfryCad.

This package contains the core data structures and management classes
for the CAD application, including document management, layers,
preferences, and CAD object handling.
"""

from .document import Document
from .layers import LayerManager, Layer
from .cad_objects import *


__all__ = [
    'Document',
    'LayerManager',
    'Layer',
]
