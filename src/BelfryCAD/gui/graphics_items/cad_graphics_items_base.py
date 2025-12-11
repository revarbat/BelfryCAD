"""
Base class for custom CAD graphics items with proper selection indication.

This module provides a base class that handles selection indication by drawing
a thicker outline in the selection color behind the normal shape.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QApplication
import time

class CadGraphicsItemBase(QAbstractGraphicsShapeItem):
    """Base class for custom CAD graphics items with selection indication."""
    
    def __init__(self, pen: Optional[QPen] = None, brush: Optional[QBrush] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        
        # Set up selection flags
        self._setup_selection_flags()
    
    def _setup_selection_flags(self):
        """Configure this item to be selectable and movable."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
    
    def itemChange(self, change, value):
        """
        Override itemChange to validate viewmodel before selection changes.
        
        This prevents segfaults when Qt's C++ code tries to access item.data(0)
        during setSelected() if the viewmodel has been destroyed.
        """
        # Intercept selection changes to validate viewmodel before Qt accesses it
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Check if viewmodel is valid before allowing selection change
            # Qt's C++ code will access item.data(0) and try to convert QVariant to Python
            # If the QObject is destroyed, this causes a segfault. We must clear it first.
            viewmodel_valid = False
            try:
                viewmodel = self.data(0)
                if viewmodel is not None:
                    # Try multiple property accesses to ensure QObject is fully valid
                    # Just checking objectName() isn't enough - Qt accesses other properties
                    try:
                        _ = viewmodel.objectName()
                        # Also check if it has the expected attributes
                        if hasattr(viewmodel, '_cad_object'):
                            # Try accessing a property that Qt might access
                            _ = viewmodel.is_selected
                            viewmodel_valid = True
                    except (RuntimeError, AttributeError, TypeError):
                        # QObject is destroyed or invalid - clear the reference immediately
                        try:
                            self.setData(0, None)
                        except:
                            pass
                        viewmodel_valid = False
                else:
                    viewmodel_valid = False
            except (RuntimeError, AttributeError, TypeError):
                # If accessing data(0) itself fails, clear it to prevent future crashes
                try:
                    self.setData(0, None)
                except:
                    pass
                viewmodel_valid = False
            
            # If viewmodel is invalid, prevent selection change to avoid segfault
            # Return current selection state instead of new value
            if not viewmodel_valid and value is True:
                # Return current selection state to prevent the change
                return self.isSelected()
        
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        """Paint the graphics item with selection indication if selected."""
        if self.isSelected():
            # Step 1: Draw selection outline (thicker, selection color) with animated dash offset
            painter.save()
            # selection_color = QApplication.palette().highlight().color()
            selection_pen = QPen(QColor("#00bfff"), 3.0)
            selection_pen.setCosmetic(True)
            selection_pen.setDashPattern([3, 3])
            selection_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            selection_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            # Animate dash offset based on time for pulsing effect
            dash_offset = (time.monotonic() * 100) % 6  # 6 = sum of dash pattern [3,3]
            selection_pen.setDashOffset(dash_offset)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill for selection outline
            shape = self.shape()
            painter.drawPath(shape)
            painter.restore()
        
        # Step 2: Draw normal shape (over the selection outline if selected)
        self._draw_shape_geometry(painter)
    
    def _draw_shape_geometry(self, painter):
        """
        Draw the specific shape geometry.
        
        This method must be implemented by subclasses to draw their specific
        shape (line, circle, etc.) using the current pen and brush.
        
        Args:
            painter: QPainter instance configured with the appropriate pen/brush
        """
        raise NotImplementedError("Subclasses must implement _draw_shape_geometry()")
    
