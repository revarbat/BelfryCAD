"""
CadArcGraphicsItem - A graphics item for drawing arcs with optional arrowheads and selection decorations.
"""

import math
from enum import Enum
from typing import Optional
from PySide6.QtCore import (
    Qt, QPointF, QRectF
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainterPath, QPainterPathStroker, QPolygonF
)
from PySide6.QtWidgets import (
    QAbstractGraphicsShapeItem, QGraphicsItem, QGraphicsPathItem,
    QGraphicsPolygonItem
)

from .cad_graphics_items_base import CadGraphicsItemBase


class CadArcArrowheadEndcaps(Enum):
    NONE = 0
    START = 1
    END = 2
    BOTH = 3


def _polar(rad, ang):
    ang_rad = math.radians(ang)
    return QPointF(math.cos(ang_rad), math.sin(ang_rad)) * rad


class CadArcGraphicsItem(CadGraphicsItemBase):
    """A graphics item for drawing arcs with optional arrowheads."""

    def __init__(
            self,
            center_point: QPointF,
            radius: float,
            start_degrees: float,
            span_degrees: float,
            arrowheads: CadArcArrowheadEndcaps = CadArcArrowheadEndcaps.NONE,
            parent: Optional[QGraphicsItem] = None,
            pen: QPen = QPen(QColor(0, 0, 0), 1.0)
    ):
        """
        Initialize the CadArcGraphicsItem.

        Args:
            center_point: The center point of the arc.
            radius: The radius of the arc.
            start_degrees: The start angle of the arc in degrees.
            span_degrees: The span angle of the arc in degrees.
            arrowheads: The arrowheads of the arc.
            parent: The parent item of the arc.
            pen: The pen used to draw the arc.
        """
        super().__init__(parent=parent, pen=pen)
        
        # Store arc parameters
        self._center_point = center_point
        self._radius = radius
        self._start_degrees = start_degrees
        self._span_degrees = span_degrees
        
        # Styling properties - will be set via setPen()
        self._arrowheads = arrowheads
        
        # Graphics items
        self._arc_item = None
        self._arrowhead_items = []
        
        # Set up the graphics item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        
        # Ensure the item is visible
        self.setVisible(True)
        self.setPen(pen)
        
        # Create the arc
        self._create_arc()

    def _draw_shape_geometry(self, painter):
        """Draw the polyline geometry using the current pen."""
        painter.save()
        painter.setPen(self.pen())
        # painter.drawPolyline(QPolygonF(self._points))
        painter.restore()

    def _create_arc(self):
        """
        Creates the arc graphics item.
        """
        # Calculate end angle
        start_degrees = self._start_degrees
        end_degrees = start_degrees + self._span_degrees
        
        # Calculate start and end points
        start_point = self._center_point + _polar(self._radius, start_degrees)
        end_point = self._center_point + _polar(self._radius, end_degrees)
        
        # Create arc path
        arc_path = QPainterPath()
        
        # Normalize span angle to -180 to 180 for Qt's arcTo
        span_degrees = self._span_degrees
        while span_degrees > 360:
            span_degrees -= 360
        while span_degrees < -360:
            span_degrees += 360
        
        scale = self.transform().m11()
        circum = 2 * math.pi * self._radius
        shy_span = 10 * scale / circum * 360

        trimmed_start_degrees = start_degrees
        trimmed_span_degrees = span_degrees
        trimmed_start_point = start_point

        if self._arrowheads in [CadArcArrowheadEndcaps.START, CadArcArrowheadEndcaps.BOTH]:
            trimmed_span_degrees -= shy_span * math.copysign(1.0, span_degrees)
            trimmed_start_degrees += shy_span * math.copysign(1.0, span_degrees)
            trimmed_start_point = self._center_point + _polar(self._radius, trimmed_start_degrees)
        if self._arrowheads in [CadArcArrowheadEndcaps.END, CadArcArrowheadEndcaps.BOTH]:
            trimmed_span_degrees -= shy_span * math.copysign(1.0, span_degrees)

        arc_path.moveTo(trimmed_start_point)

        # Draw the arc - Qt's arcTo uses degrees
        arc_path.arcTo(
            self._center_point.x() - self._radius,
            self._center_point.y() - self._radius,
            self._radius * 2,
            self._radius * 2,
            -trimmed_start_degrees,  # Qt uses degrees
            -trimmed_span_degrees    # Qt uses degrees, negative for clockwise
        )
        
        # Create arc graphics item
        self._arc_item = QGraphicsPathItem(arc_path, self)
        # Use the pen from the parent class (QAbstractGraphicsShapeItem)
        self._arc_item.setPen(self.pen())
        
        # Create arrowheads if requested
        if self._arrowheads != CadArcArrowheadEndcaps.NONE:
            self._create_arrowheads(start_point, end_point, start_degrees, end_degrees, span_degrees)

    def _create_arrowheads(self, start_point: QPointF, end_point: QPointF, 
                          start_degrees: float, end_degrees: float, span_degrees: float):
        """Create arrowheads at the start and end of the arc.
        
        Args:
            start_point: Start point of the arc
            end_point: End point of the arc  
            start_degrees: Start angle in degrees
            end_degrees: End angle in degrees
            span_degrees: Span angle in degrees
        """
        # Clear existing arrowheads
        for item in self._arrowhead_items:
            if item.scene():
                item.scene().removeItem(item)
        self._arrowhead_items.clear()
        
        scale = self.transform().m11()
        shy_span = 10 * scale / self._radius
        # Calculate arrow spin in degrees
        arrow_spin = 90 - shy_span / 2
        if span_degrees < 0:
            arrow_spin = -arrow_spin

        if self._arrowheads in [CadArcArrowheadEndcaps.START, CadArcArrowheadEndcaps.BOTH]:
            # Create start arrowhead (pointing outward from center)
            start_arrow_angle = start_degrees - arrow_spin
            start_arrow_vector = _polar(10, start_arrow_angle)
            self._create_arrowhead(start_point, start_arrow_vector)
        
        if self._arrowheads in [CadArcArrowheadEndcaps.END, CadArcArrowheadEndcaps.BOTH]:
            # Create end arrowhead (pointing outward from center)
            end_arrow_angle = end_degrees + arrow_spin
            end_arrow_vector = _polar(10, end_arrow_angle)
            self._create_arrowhead(end_point, end_arrow_vector)

    def _create_arrowhead(self, arrow_tip: QPointF, arrow_vector: QPointF):
        """Create an arrowhead at the specified position."""
        arrow_length = math.sqrt(arrow_vector.x()**2 + arrow_vector.y()**2)
        if arrow_length == 0:
            return
        
        arrow_unit = arrow_vector * (1.0 / arrow_length)
        arrow_pvec = QPointF(-arrow_unit.y(), arrow_unit.x())
        
        # Create arrowhead polygon
        pen_width = self.pen().widthF()
        poly = QPolygonF([
            arrow_tip,
            arrow_tip + arrow_pvec * (pen_width / 2 + arrow_length / 4) - arrow_vector,
            arrow_tip - arrow_pvec * (pen_width / 2 + arrow_length / 4) - arrow_vector
        ])
        
        arrowhead = QGraphicsPolygonItem(poly, self)
        # Use the pen color from the parent class
        pen = QPen(self.pen().color(), 0)
        brush = QBrush(self.pen().color())
        arrowhead.setPen(pen)
        arrowhead.setBrush(brush)
        self._arrowhead_items.append(arrowhead)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the arc."""
        if not self._arc_item:
            return QRectF()
        
        # Get the bounding rect of the arc
        rect = self._arc_item.boundingRect()
        
        # Include arrowheads if they exist
        for arrowhead in self._arrowhead_items:
            rect = rect.united(arrowhead.boundingRect())
        
        return rect

    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        if not self._arc_item:
            return QPainterPath()
        
        # Combine arc and arrowhead shapes
        shape = self._arc_item.shape()
        
        for arrowhead in self._arrowhead_items:
            shape.addPath(arrowhead.shape())
        
        stroker = QPainterPathStroker()
        stroker.setWidth(self.pen().widthF())
        stroker.setCapStyle(self.pen().capStyle())
        stroker.setJoinStyle(self.pen().joinStyle())
        shape = stroker.createStroke(shape)

        return shape

    # Property setters
    def setCenterPoint(self, center_point: QPointF):
        """Set the center point of the arc."""
        self._center_point = center_point
        self._recreate_arc()

    def setRadius(self, radius: float):
        """Set the radius of the arc."""
        self._radius = radius
        self._recreate_arc()

    def setStartAngle(self, start_degrees: float):
        """Set the start angle of the arc in degrees."""
        self._start_degrees = start_degrees
        self._recreate_arc()

    def setSpanAngle(self, span_degrees: float):
        """Set the span angle of the arc in degrees."""
        self._span_degrees = span_degrees
        self._recreate_arc()

    def setPen(self, pen):
        """Set the pen for the arc."""
        super().setPen(pen)
        self._update_style()

    def setArrowheads(self, arrowheads: CadArcArrowheadEndcaps):
        """Set the arrowheads of the arc."""
        self._arrowheads = arrowheads
        self._recreate_arc()

    def _recreate_arc(self):
        """Recreate the arc with current parameters."""
        # Remove existing items
        if self._arc_item:
            if self._arc_item.scene():
                self._arc_item.scene().removeItem(self._arc_item)
            self._arc_item = None
        
        for item in self._arrowhead_items:
            if item.scene():
                item.scene().removeItem(item)
        self._arrowhead_items.clear()
        
        # Create new arc
        self._create_arc()
        self.prepareGeometryChange()
        self.update()

    def _update_style(self):
        """Update the style of existing items."""
        if self._arc_item:
            self._arc_item.setPen(self.pen())
        
        for arrowhead in self._arrowhead_items:
            pen = QPen(self.pen().color(), 0)
            brush = QBrush(self.pen().color())
            arrowhead.setPen(pen)
            arrowhead.setBrush(brush)
        
        self.update()

    # Property getters
    @property
    def center_point(self) -> QPointF:
        """Get the center point of the arc."""
        return self._center_point

    @property
    def radius(self) -> float:
        """Get the radius of the arc."""
        return self._radius

    @property
    def start_degrees(self) -> float:
        """Get the start angle of the arc in degrees."""
        return self._start_degrees

    @property
    def span_degrees(self) -> float:
        """Get the span angle of the arc in degrees."""
        return self._span_degrees

    @property
    def end_degrees(self) -> float:
        """Get the end angle of the arc in degrees."""
        return self._start_degrees + self._span_degrees 

    @property
    def arrowheads(self) -> CadArcArrowheadEndcaps:
        """Get the arrowheads of the arc."""
        return self._arrowheads
    