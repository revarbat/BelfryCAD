"""
CadRectangleGraphicsItem - A custom graphics item for drawing rectangles.
"""

from typing import Optional
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QGraphicsItem

from .cad_graphics_items_base import CadGraphicsItemBase


class CadRectangleGraphicsItem(CadGraphicsItemBase):
    """A custom graphics item for drawing rectangles."""

    def __init__(self, corner_point: QPointF, width: float, height: float,
                 pen: Optional[QPen] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent=parent)
        self._corner_point = corner_point
        self._width = width
        self._height = height
        if pen is not None:
            self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def _draw_shape_geometry(self, painter):
        """Draw the rectangle geometry using the current pen."""
        painter.save()
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRect(QRectF(self._corner_point, QPointF(
            self._corner_point.x() + self._width,
            self._corner_point.y() + self._height
        )))
        painter.restore()

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle."""
        pen_width = self.pen().widthF()
        margin = pen_width / 2.0
        return QRectF(
            self._corner_point.x() - margin,
            self._corner_point.y() - margin,
            self._width + 2 * margin,
            self._height + 2 * margin
        )

    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        path = QPainterPath()
        path.addRect(QRectF(self._corner_point, QPointF(
            self._corner_point.x() + self._width,
            self._corner_point.y() + self._height
        )))
        return path

    @property
    def corner_point(self) -> QPointF:
        return self._corner_point

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    @property
    def center_point(self) -> QPointF:
        return QPointF(
            self._corner_point.x() + self._width / 2,
            self._corner_point.y() + self._height / 2
        )

    @property
    def opposite_corner(self) -> QPointF:
        return QPointF(
            self._corner_point.x() + self._width,
            self._corner_point.y() + self._height
        )

    def setCornerPoint(self, point: QPointF):
        self.prepareGeometryChange()
        self._corner_point = point
        self.update()

    def setWidth(self, width: float):
        self.prepareGeometryChange()
        self._width = width
        self.update()

    def setHeight(self, height: float):
        self.prepareGeometryChange()
        self._height = height
        self.update()
