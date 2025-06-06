"""
Rulers Module for PyTkCAD

This module provides ruler widgets for the PyTkCAD application, translated from
the original TCL rulers.tcl implementation. Rulers show measurement scales
along the edges of the drawing canvas.
"""

import math
from typing import Optional, Tuple, List
from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PySide6.QtCore import Signal


class RulerWidget(QWidget):
    """
    A ruler widget that displays measurement scales along canvas edges.
    
    Translated from the TCL rulers.tcl implementation to provide the same
    functionality with PySide6/Qt.
    """
    
    def __init__(self, canvas: QGraphicsView, orientation: str, parent=None):
        """
        Initialize the ruler widget.
        
        Args:
            canvas: The QGraphicsView to track
            orientation: "horizontal" or "vertical"
            parent: Parent widget
        """
        super().__init__(parent)
        self.canvas = canvas
        self.orientation = orientation
        self.ruler_width = 32.0
        self.position = 0.0
        
        # Ruler appearance settings
        self.font = QFont("Helvetica", 8)
        self.ruler_bg = QColor("white")
        self.ruler_fg = QColor("black")
        self.position_color = QColor("#ff4fff")  # Magenta for position indicator
        
        # Set fixed size based on orientation
        if orientation == "horizontal":
            self.setFixedHeight(int(self.ruler_width))
        else:
            self.setFixedWidth(int(self.ruler_width))
        
        # Enable mouse tracking for position updates
        self.setMouseTracking(True)
    
    def format_fractions(self, val: float, unit: str) -> str:
        """
        Format a value as fractions (translated from ruler_format_fractions).
        
        Args:
            val: The value to format
            unit: The unit string (e.g., '"', "'")
            
        Returns:
            Formatted string with fractions
        """
        out = ""
        if val < 0.0:
            out += "-"
            val = -val
        
        whole = int(abs(val) + 1e-6) if val >= 0 else -int(abs(val) + 1e-6)
        if out != "" or whole != 0 or abs(val) < 1e-6:
            # Show whole numbers or zero
            out += f"{whole:d}"
        
        if unit == "'":
            # Feet and inches formatting
            val = 12.0 * abs(val - whole)
            inches = int(1e-6 + val)
            denom = 512
            val = denom * abs(val - inches)
            numer = int(0.5 + val)
            
            if numer > 0.0 or inches != 0:
                if out != "":
                    out += unit
                
                # Reduce fraction to lowest terms
                while denom > 1 and numer % 2 == 0:
                    numer //= 2
                    denom //= 2
                
                fracstr = ""
                if numer > 0:
                    if inches != 0:
                        fracstr += " "
                    fracstr += f"{numer:d}/{denom:d}"
                
                if len(fracstr) > 3:
                    if inches != 0:
                        out += f" {inches:d}"
                    if fracstr != "":
                        out += "\n"
                else:
                    if inches != 0 or fracstr != "":
                        out += "\n"
                    if inches != 0:
                        out += f"{inches:d}"
                        if fracstr != "":
                            out += " "
                
                out += fracstr
                if fracstr != "" or inches != 0:
                    out += '"'
            else:
                out += unit + "\n"
        else:
            # Other units with fractional formatting
            denom = 512.0
            numer = int(0.5 + denom * abs(val - whole))
            if numer > 0.0:
                while denom > 1.0 and numer % 2 == 0:
                    numer //= 2
                    denom //= 2
                out += "\n"
                out += f"{numer:d}/{int(denom):d}"
                out += unit
            else:
                out += unit + "\n"
        
        return out
    
    def format_decimal(self, val: float, unit: str) -> str:
        """
        Format a value as decimal (translated from ruler_format_decimal).
        
        Args:
            val: The value to format
            unit: The unit string
            
        Returns:
            Formatted decimal string
        """
        if abs(val) < 1e-6:
            out = "0" + unit
            return out.strip()
        elif unit == "'":
            # Feet and inches decimal formatting
            whole = int(val)
            denom = 12.0
            numer = int(denom * abs(val - whole) + 0.5)
            
            out = ""
            if whole != 0 or abs(val) < 1e-6:
                out += f"{whole:d}" + unit
            out += " "
            if numer > 0.0:
                out += f'{int(numer):d}"'
            
            out = out.strip()
            if len(str(whole)) > 2:
                out = out.replace(" ", "\n")
        else:
            # General decimal formatting
            out = f"{val:.6g}"
            if len(unit.strip()) + len(out.strip()) <= 4:
                out += unit.strip()
            if len(out) > 6:
                out = out.replace(".", ".\n")
        
        return out
    
    def get_grid_info(self) -> Tuple[float, float, float, float, float, str, str, float]:
        """
        Get grid information from the canvas (placeholder implementation).
        
        In the original TCL implementation, this calls cadobjects_grid_info.
        This is a simplified version that returns reasonable defaults.
        
        Returns:
            Tuple of (minorspacing, majorspacing, superspacing, labelspacing, 
                     divisor, units, formatfunc, conversion)
        """
        # Default grid settings - these would come from the CAD system
        minorspacing = 0.125
        majorspacing = 1.0
        superspacing = 12.0
        labelspacing = 1.0
        divisor = 1.0
        units = '"'
        formatfunc = "decimal"  # or "fractions"
        conversion = 1.0
        
        return (minorspacing, majorspacing, superspacing, labelspacing,
                divisor, units, formatfunc, conversion)
    
    def get_dpi(self) -> float:
        """Get DPI setting (placeholder implementation)."""
        return 96.0  # Standard screen DPI
    
    def get_scale_factor(self) -> float:
        """Get current scale factor (placeholder implementation)."""
        return 1.0  # No zoom
    
    def paintEvent(self, event):
        """Paint the ruler widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        
        # Clear background
        painter.fillRect(rect, self.ruler_bg)
        
        # Get grid and scale information
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = self.get_grid_info()
        
        dpi = self.get_dpi()
        scalefactor = self.get_scale_factor()
        scalemult = dpi * scalefactor / conversion
        
        # Get visible area of canvas in scene coordinates
        if self.canvas and self.canvas.scene():
            scene_rect = self.canvas.mapToScene(self.canvas.viewport().rect()).boundingRect()
            srx0 = scene_rect.left()
            sry0 = scene_rect.top()
            srx1 = scene_rect.right()
            sry1 = scene_rect.bottom()
        else:
            # Fallback if no canvas
            srx0, sry0, srx1, sry1 = -100, -100, 100, 100
        
        # Set up drawing tools
        painter.setFont(self.font)
        tick_pen = QPen(self.ruler_fg)
        text_pen = QPen(self.ruler_fg)
        
        if self.orientation == "vertical":
            self._draw_vertical_ruler(painter, rect, scalemult, srx0, sry0, srx1, sry1,
                                    minorspacing, majorspacing, labelspacing,
                                    divisor, units, formatfunc, tick_pen, text_pen)
        else:
            self._draw_horizontal_ruler(painter, rect, scalemult, srx0, sry0, srx1, sry1,
                                      minorspacing, majorspacing, labelspacing,
                                      divisor, units, formatfunc, tick_pen, text_pen)
        
        # Draw position indicator
        self._draw_position_indicator(painter, rect, scalemult, srx0, sry0)
    
    def _draw_vertical_ruler(self, painter: QPainter, rect: QRectF, scalemult: float,
                           srx0: float, sry0: float, srx1: float, sry1: float,
                           minorspacing: float, majorspacing: float, labelspacing: float,
                           divisor: float, units: str, formatfunc: str,
                           tick_pen: QPen, text_pen: QPen):
        """Draw vertical ruler ticks and labels."""
        ystart = sry0 / scalemult
        yend = sry1 / scalemult
        
        # Draw border line
        painter.setPen(tick_pen)
        painter.drawLine(rect.width() - 1, 0, rect.width() - 1, rect.height())
        painter.drawLine(rect.width() - 1, rect.height(), 0, rect.height())
        painter.drawLine(0, rect.height(), 0, 0)
        
        # Draw tick marks
        ys = math.floor(ystart / minorspacing + 1e-6) * minorspacing
        while ys <= yend:
            ypos = scalemult * ys - sry0
            
            # Convert to widget coordinates
            widget_y = ypos
            if 0 <= widget_y <= rect.height():
                # Determine tick length based on spacing
                if abs(math.floor(ys / labelspacing + 1e-6) - ys / labelspacing) < 1e-3:
                    # Major tick with label
                    ticklen = 6
                    xpos = rect.width() - ticklen - 1
                    
                    # Format and draw label
                    if formatfunc == "fractions":
                        majortext = self.format_fractions(ys / divisor, units)
                    else:
                        majortext = self.format_decimal(ys / divisor, units)
                    
                    majortext = majortext.strip()
                    painter.setPen(text_pen)
                    painter.drawText(int(xpos - 30), int(widget_y - 5), 30, 10,
                                   Qt.AlignRight | Qt.AlignVCenter, majortext)
                elif abs(math.floor(ys / majorspacing + 1e-6) - ys / majorspacing) < 1e-3:
                    # Medium tick
                    ticklen = 4
                else:
                    # Minor tick
                    ticklen = 2
                
                # Draw tick mark
                xpos = rect.width() - ticklen
                painter.setPen(tick_pen)
                painter.drawLine(int(rect.width()), int(widget_y), int(xpos), int(widget_y))
            
            ys += minorspacing
    
    def _draw_horizontal_ruler(self, painter: QPainter, rect: QRectF, scalemult: float,
                             srx0: float, sry0: float, srx1: float, sry1: float,
                             minorspacing: float, majorspacing: float, labelspacing: float,
                             divisor: float, units: str, formatfunc: str,
                             tick_pen: QPen, text_pen: QPen):
        """Draw horizontal ruler ticks and labels."""
        xstart = srx0 / scalemult
        xend = srx1 / scalemult
        
        # Draw border line
        painter.setPen(tick_pen)
        painter.drawLine(0, rect.height() - 1, rect.width(), rect.height() - 1)
        painter.drawLine(rect.width(), rect.height() - 1, rect.width(), 0)
        painter.drawLine(rect.width(), 0, 0, 0)
        
        # Draw tick marks
        xs = math.floor(xstart / minorspacing + 1e-6) * minorspacing
        while xs <= xend:
            xpos = scalemult * xs - srx0
            
            # Convert to widget coordinates
            widget_x = xpos
            if 0 <= widget_x <= rect.width():
                # Determine tick length based on spacing
                if abs(math.floor(xs / labelspacing + 1e-6) - xs / labelspacing) < 1e-3:
                    # Major tick with label
                    ticklen = 6
                    ypos = rect.height() - ticklen
                    
                    # Format and draw label
                    if formatfunc == "fractions":
                        majortext = self.format_fractions(xs / divisor, units)
                    else:
                        majortext = self.format_decimal(xs / divisor, units)
                    
                    painter.setPen(text_pen)
                    painter.drawText(int(widget_x - 15), int(ypos - 15), 30, 15,
                                   Qt.AlignCenter | Qt.AlignBottom, majortext)
                elif abs(math.floor(xs / majorspacing + 1e-6) - xs / majorspacing) < 1e-3:
                    # Medium tick
                    ticklen = 4
                else:
                    # Minor tick
                    ticklen = 2
                
                # Draw tick mark
                ypos = rect.height() - ticklen
                painter.setPen(tick_pen)
                painter.drawLine(int(widget_x), int(rect.height()), int(widget_x), int(ypos))
            
            xs += minorspacing
    
    def _draw_position_indicator(self, painter: QPainter, rect: QRectF, scalemult: float,
                               srx0: float, sry0: float):
        """Draw the position indicator line."""
        painter.setPen(QPen(self.position_color, 2))
        
        if self.orientation == "vertical":
            # For vertical ruler, convert scene Y position to widget coordinates
            # Use the same transformation as the visible scene area
            if self.canvas and self.canvas.scene():
                # Map the position from scene coordinates to widget coordinates
                scene_point = self.canvas.mapFromScene(0, self.position)
                widget_y = scene_point.y()
                if 0 <= widget_y <= rect.height():
                    painter.drawLine(0, int(widget_y), int(rect.width()), int(widget_y))
        else:
            # For horizontal ruler, convert scene X position to widget coordinates
            if self.canvas and self.canvas.scene():
                # Map the position from scene coordinates to widget coordinates
                scene_point = self.canvas.mapFromScene(self.position, 0)
                widget_x = scene_point.x()
                if 0 <= widget_x <= rect.width():
                    painter.drawLine(int(widget_x), 0, int(widget_x), int(rect.height()))
    
    def update_mouse_position(self, pos: float):
        """
        Update the mouse position indicator (translated from ruler_update_mousepos).
        
        Args:
            pos: The position in scene coordinates
        """
        self.position = pos
        self.update()  # Trigger a repaint
    
    def set_canvas(self, canvas: QGraphicsView):
        """Set the canvas that this ruler tracks."""
        self.canvas = canvas
        self.update()


class RulerManager:
    """
    Manager class for horizontal and vertical rulers.
    
    This class manages both horizontal and vertical rulers and provides
    a unified interface for updating mouse positions and canvas references.
    """
    
    def __init__(self, canvas: QGraphicsView, parent=None):
        """
        Initialize the ruler manager.
        
        Args:
            canvas: The QGraphicsView to track
            parent: Parent widget for the rulers
        """
        self.canvas = canvas
        self.horizontal_ruler = RulerWidget(canvas, "horizontal", parent)
        self.vertical_ruler = RulerWidget(canvas, "vertical", parent)
    
    def get_horizontal_ruler(self) -> RulerWidget:
        """Get the horizontal ruler widget."""
        return self.horizontal_ruler
    
    def get_vertical_ruler(self) -> RulerWidget:
        """Get the vertical ruler widget."""
        return self.vertical_ruler
    
    def update_mouse_position(self, scene_x: float, scene_y: float):
        """
        Update mouse position on both rulers.
        
        Args:
            scene_x: X coordinate in scene coordinates
            scene_y: Y coordinate in scene coordinates
        """
        self.horizontal_ruler.update_mouse_position(scene_x)
        self.vertical_ruler.update_mouse_position(scene_y)
    
    def set_canvas(self, canvas: QGraphicsView):
        """
        Set the canvas for both rulers.
        
        Args:
            canvas: The new QGraphicsView to track
        """
        self.canvas = canvas
        self.horizontal_ruler.set_canvas(canvas)
        self.vertical_ruler.set_canvas(canvas)
    
    def update_rulers(self):
        """Force update of both rulers."""
        self.horizontal_ruler.update()
        self.vertical_ruler.update()
