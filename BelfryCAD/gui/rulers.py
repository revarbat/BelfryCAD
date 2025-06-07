"""
Rulers Module for PyTkCAD

This module provides ruler widgets for the PyTkCAD application, translated from
the original TCL rulers.tcl implementation. Rulers show measurement scales
along the edges of the drawing canvas.
"""

import math
from typing import Tuple, Callable
from PySide6.QtWidgets import QWidget, QGraphicsView
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont


class RulerWidget(QWidget):
    """
    A ruler widget that displays measurement scales along canvas edges.

    Translated from the TCL rulers.tcl implementation to provide the same
    functionality with PySide6/Qt.
    """

    def __init__(self, canvas: QGraphicsView,
                 orientation: str, parent=None,
                 dpi=96.0, scale_factor=1.0):
        """
        Initialize the ruler widget.

        Args:
            canvas: The QGraphicsView to track
            orientation: "horizontal" or "vertical"
            parent: Parent widget
        """
        super().__init__(parent)
        self.canvas = canvas
        self.dpi = dpi
        self.scale_factor = scale_factor
        self.orientation = orientation
        self.ruler_width = 32.0
        self.position = 0.0

        # Ruler appearance settings
        self.ruler_font = QFont("Helvetica", 8)
        self.ruler_bg = QColor("white")
        self.ruler_fg = QColor("black")
        self.position_color = QColor("#ff4fff")  # Magenta

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

    def get_grid_info(self) -> \
            Tuple[float, float, float, float, float, str, str, float]:
        """
        Get grid information from the canvas using dynamic TCL-compatible
        logic.

        This method replicates the logic from cadobjects_grid_info in the TCL
        implementation, providing adaptive grid spacing based on current zoom
        and DPI settings.

        Returns:
            Tuple of (minorspacing, majorspacing, superspacing, labelspacing,
                     divisor, units, formatfunc, conversion)
        """

        # Get DPI and scale factor
        dpi = self.get_dpi()
        scalefactor = self.get_scale_factor()

        # Get unit system information
        # For now, using default unit system - this would come from preferences
        unittype = "Inches"
        isfract = True  # Fractions vs decimal
        conversion = 1.0  # Conversion factor
        abbrev = '"'

        # Set format function based on fractions preference
        if isfract:
            formatfunc = self.format_fractions
        else:
            formatfunc = self.format_decimal

        divisor = 1.0

        # Set up significant spacing values based on unit type
        if unittype == "Inches":
            if isfract:
                significants = [
                    0.00390625,  # 1/256 inch
                    0.015625,  # 1/64 inch
                    0.0625,  # 1/16 inch
                    0.25,   # 1/4 inch
                    1.0,    # 1 inch
                    12.0,   # 1 ft
                    120.0,  # 10 ft
                    1200.0  # 100 ft
                ]
                unit = '"'
            else:
                significants = [
                    0.001,  # 1/1000 inch
                    0.01,   # 1/100 inch
                    0.1,    # 1/10 inch
                    1.0,    # 1 inch
                    12.0,   # 1 ft
                    120.0,  # 10 ft
                    1200.0  # 100 ft
                ]
                unit = '"'
        elif unittype == "Feet":
            # Proposed:
            #   10ft, 1ft, 1in, 1/4in, 1/16in, 1/64in, 1/256in
            significants = [
                0.000325520833333,  # 1/256 inch
                0.001302083333333,  # 1/64 inch
                0.005208333333333,  # 1/16 inch
                0.020833333333333,  # 1/4 inch
                0.083333333333333,  # 1 inch
                1.0,   # 1 ft
                10.0,  # 10 ft
                100.0  # 100 ft
            ]
            formatfunc = self.format_fractions
            unit = "'"
        else:
            # Metric
            # Proposed: 10m, 1m, 1dm, 1cm, 1mm, 0.1mm
            significants = [
                0.0001,  # 100 nm
                0.001,   # 1 µm
                0.01,    # 10 µm
                0.1,     # 100 µm
                1.0,     # 1 mm
                10.0,    # 1 cm
                100.0,   # 10 cm
                1000.0,   # 1 m
                10000.0,  # 10 m
                100000.0  # 100 m
            ]
            unit = "mm"
            formatfunc = self.format_decimal
            if unittype == "Centimeters":
                unit = "cm"
            elif unittype == "Meters":
                unit = "m"

        # Calculate scale multiplier
        scalemult = dpi * scalefactor / conversion

        # Initialize spacing values
        minorspacing = 0
        majorspacing = 0
        superspacing = 0
        labelspacing = 0

        # Find appropriate spacing values based on pixel thresholds
        for val in significants:
            if minorspacing == 0 and scalemult * val >= 8.0:
                minorspacing = val
            if labelspacing == 0 and scalemult * val >= 30.0:
                labelspacing = val
            if majorspacing == 0 and minorspacing != 0 and val / minorspacing > 2.99:
                majorspacing = val
            if superspacing == 0 and majorspacing != 0 and val / majorspacing > 1.99:
                superspacing = val
                break

        # Adjust labelspacing if it would be too dense
        while labelspacing * scalemult > 100.0:
            labelspacing = labelspacing / 2.0

        return (minorspacing, majorspacing, superspacing, labelspacing,
                divisor, unit, formatfunc, conversion)

    def get_dpi(self) -> float:
        """Get DPI setting from scene or use default."""
        if self.canvas:
            return self.dpi
        return 96.0  # Standard screen DPI fallback

    def set_dpi(self, dpi: float):
        """Set DPI for the ruler widget."""
        self.dpi = dpi
        self.update()

    def get_scale_factor(self) -> float:
        """Get current scale factor from scene or use default."""
        if self.canvas:
            return self.scale_factor
        return 1.0  # No zoom fallback

    def set_scale_factor(self, scale_factor: float):
        """Set scale factor for the ruler widget."""
        self.scale_factor = scale_factor
        self.update()

    def paintEvent(self, event):
        """Paint the ruler widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

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
            scene_rect = self.canvas.mapToScene(
                self.canvas.viewport().rect()
                ).boundingRect()
            srx0 = scene_rect.left()
            sry0 = scene_rect.top()
            srx1 = scene_rect.right()
            sry1 = scene_rect.bottom()
        else:
            return  # No canvas available, skip drawing

        # Set up drawing tools
        painter.setFont(self.ruler_font)
        tick_pen = QPen(self.ruler_fg)
        text_pen = QPen(self.ruler_fg)

        if self.orientation == "vertical":
            self._draw_vertical_ruler(
                painter, QRectF(rect), scalemult, srx0, sry0, srx1, sry1,
                minorspacing, majorspacing, labelspacing,
                divisor, units, formatfunc, tick_pen, text_pen)
        else:
            self._draw_horizontal_ruler(
                painter, QRectF(rect), scalemult, srx0, sry0, srx1, sry1,
                minorspacing, majorspacing, labelspacing,
                divisor, units, formatfunc, tick_pen, text_pen)

        # Draw position indicator
        self._draw_position_indicator(
            painter, QRectF(rect), scalemult, srx0, sry0)

    def _draw_vertical_ruler(
            self, painter: QPainter, rect: QRectF, scalemult: float,
            srx0: float, sry0: float, srx1: float, sry1: float,
            minorspacing: float, majorspacing: float, labelspacing: float,
            divisor: float, units: str, formatfunc: Callable,
            tick_pen: QPen, text_pen: QPen
    ):
        """Draw vertical ruler ticks and labels."""
        ystart = sry0 / scalemult
        yend = sry1 / scalemult

        bw = math.floor(rect.width() - 1 + 0.5)
        bh = math.floor(rect.height() + 0.5)

        # Draw border line
        painter.setPen(tick_pen)
        painter.drawLine(int(bw), 0, int(bw), int(bh))
        painter.drawLine(int(bw), int(bh), 0, int(bh))
        painter.drawLine(0, int(bh), 0, 0)

        # Draw tick marks
        ys = math.floor(ystart / minorspacing + 1e-6) * minorspacing
        while ys <= yend:
            ypos = -scalemult * ys - sry0

            # Convert to widget coordinates
            widget_y = ypos
            if 0 <= widget_y <= rect.height():
                # Determine tick length based on spacing
                if abs(math.floor(ys / labelspacing + 1e-6) - ys / labelspacing) < 1e-3:
                    # Major tick with label
                    ticklen = 6
                    xpos = rect.width() - ticklen - 1

                    # Format and draw label
                    majortext = formatfunc(ys / divisor, units)
                    majortext = majortext.strip()
                    painter.setPen(text_pen)
                    painter.drawText(
                        int(xpos - 30), int(widget_y - 5), 30, 10,
                        (Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter),
                        majortext)
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

    def _draw_horizontal_ruler(
            self, painter: QPainter, rect: QRectF, scalemult: float,
            srx0: float, sry0: float, srx1: float, sry1: float,
            minorspacing: float, majorspacing: float, labelspacing: float,
            divisor: float, units: str, formatfunc: Callable,
            tick_pen: QPen, text_pen: QPen
    ):
        """Draw horizontal ruler ticks and labels."""
        xstart = srx0 / scalemult
        xend = srx1 / scalemult

        # Draw border line
        painter.setPen(tick_pen)
        painter.drawLine(0, int(rect.height() - 1), int(rect.width()),
                         int(rect.height() - 1))
        painter.drawLine(int(rect.width()), int(rect.height() - 1),
                         int(rect.width()), 0)
        painter.drawLine(int(rect.width()), 0, 0, 0)

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
                    majortext = formatfunc(xs / divisor, units)
                    majortext = majortext.strip()
                    painter.setPen(text_pen)
                    painter.drawText(
                        int(widget_x - 15), int(ypos - 15), 30, 15,
                        (Qt.AlignmentFlag.AlignCenter |
                         Qt.AlignmentFlag.AlignBottom),
                        majortext)
                elif abs(math.floor(xs / majorspacing + 1e-6) - xs / majorspacing) < 1e-3:
                    # Medium tick
                    ticklen = 4
                else:
                    # Minor tick
                    ticklen = 2

                # Draw tick mark
                ypos = rect.height() - ticklen
                painter.setPen(tick_pen)
                painter.drawLine(
                    int(widget_x), int(rect.height()), int(widget_x), int(ypos))

            xs += minorspacing

    def _draw_position_indicator(
            self, painter: QPainter, rect: QRectF, scalemult: float,
            srx0: float, sry0: float
    ):
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

    def set_dpi(self, dpi: float):
        """
        Set DPI for both rulers.

        Args:
            dpi: The new DPI value
        """
        self.horizontal_ruler.set_dpi(dpi)
        self.vertical_ruler.set_dpi(dpi)

    def set_scale_factor(self, scale_factor: float):
        """
        Set scale factor for both rulers.
        Args:
            scale_factor: The new scale factor value
        """
        self.horizontal_ruler.set_scale_factor(scale_factor)
        self.vertical_ruler.set_scale_factor(scale_factor)

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
