"""
Base class for custom CAD graphics items with proper selection indication.

This module provides a base class that handles selection indication by drawing
a thicker outline in the selection color behind the normal shape.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QApplication

class CadGraphicsItemBase(QAbstractGraphicsShapeItem):
    """Base class for custom CAD graphics items with selection indication."""

    def __init__(self, pen: Optional[QPen] = None, brush: Optional[QBrush] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self._setup_selection_flags()

    def _setup_selection_flags(self):
        """Configure this item to be selectable and focusable."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        # ItemIsMovable is intentionally NOT set — body drag is handled at the scene level
        # (CadScene.mouseMoveEvent) so that model coordinates stay authoritative.

    def mousePressEvent(self, event):
        """Accept the press so this item becomes the mouse grabber."""
        event.accept()
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        """
        Override itemChange to validate viewmodel before selection changes.

        This prevents segfaults when Qt's C++ code tries to access item.data(0)
        during setSelected() if the viewmodel has been destroyed.
        """
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            viewmodel_valid = False
            try:
                viewmodel = self.data(0)
                if viewmodel is not None:
                    try:
                        _ = viewmodel.objectName()
                        if hasattr(viewmodel, '_cad_object'):
                            _ = viewmodel.is_selected
                            viewmodel_valid = True
                    except (RuntimeError, AttributeError, TypeError):
                        try:
                            self.setData(0, None)
                        except:
                            pass
                        viewmodel_valid = False
                else:
                    viewmodel_valid = False
            except (RuntimeError, AttributeError, TypeError):
                try:
                    self.setData(0, None)
                except:
                    pass
                viewmodel_valid = False

            if not viewmodel_valid and value is True:
                return self.isSelected()

        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        """Paint the graphics item with selection indication if selected."""
        if self.isSelected():
            painter.save()
            selection_pen = QPen(QColor("#00bfff"), 3.0)
            selection_pen.setCosmetic(True)
            selection_pen.setDashPattern([2, 2])
            selection_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            selection_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            scene = self.scene()
            if scene and hasattr(scene, '_selection_dash_offset'):
                dash_offset = scene._selection_dash_offset
            else:
                dash_offset = 0.0
            selection_pen.setDashOffset(dash_offset)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            shape = self.shape()
            painter.drawPath(shape)
            painter.restore()

        self._draw_shape_geometry(painter)

    def _draw_shape_geometry(self, painter):
        """
        Draw the specific shape geometry.

        This method must be implemented by subclasses to draw their specific
        shape (line, circle, etc.) using the current pen and brush.
        """
        raise NotImplementedError("Subclasses must implement _draw_shape_geometry()")
