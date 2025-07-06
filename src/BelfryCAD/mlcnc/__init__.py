"""
MLCNC (Machine Learning CNC) Utilities

This module provides machine learning utilities for CNC operations,
translated from the original TCL implementation in tksrc/lib/mlcnc.

This package includes:
- Feed rate optimization
- Cutting parameter prediction
- Tool path optimization
- Material property analysis
"""

__version__ = "1.0.0"
__author__ = "Converted from TCL to Python"

from .feed_optimizer import FeedOptimizer
from .cutting_params import CuttingParameterCalculator
from .tool_path import ToolPathOptimizer
from .material_db import MaterialDatabase

__all__ = [
    'FeedOptimizer',
    'CuttingParameterCalculator',
    'ToolPathOptimizer',
    'MaterialDatabase'
]