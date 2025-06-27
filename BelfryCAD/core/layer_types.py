"""
Layer type definitions for BelfryCad.

This module provides the base Layer class and related types.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Layer:
    """Represents a drawing layer with its properties and contained objects."""

    name: str
    visible: bool = True
    locked: bool = False
    color: str = "black"
    cut_bit: int = 0
    cut_depth: float = 0.0
    objects: List[int] = field(default_factory=list)

    def __hash__(self) -> int:
        """Make Layer hashable based on its instance identity."""
        return id(self)

    def __eq__(self, other: object) -> bool:
        """Compare Layer objects for equality based on instance identity."""
        if not isinstance(other, Layer):
            return NotImplemented
        return self is other