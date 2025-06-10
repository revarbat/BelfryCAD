"""
Print System for BelfryCAD

This module provides comprehensive printing functionality for CAD drawings,
including print dialog, page setup, and PDF export capabilities.
"""

from typing import Optional
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QPainter, QTransform, QPen, QBrush, QColor
from PySide6.QtWidgets import QFileDialog
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPageSetupDialog


class CadPrintManager:
    """Manages printing operations for CAD drawings."""
    
    def __init__(self, parent_window, cad_scene, document):
        self.parent = parent_window
        self.cad_scene = cad_scene
        self.document = document
        
        # Default printer settings
        self._printer_settings = None
        self._setup_default_printer()
    
    def _setup_default_printer(self):
        """Set up default printer configuration."""
        from PySide6.QtGui import QPageLayout
        self._printer_settings = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        # Set page orientation through page layout
        page_layout = self._printer_settings.pageLayout()
        page_layout.setOrientation(QPageLayout.Orientation.Landscape)
        self._printer_settings.setPageLayout(page_layout)
        
        self._printer_settings.setColorMode(QPrinter.ColorMode.Color)
        
        # Set reasonable margins (0.5 inch all around)
        margins = self._printer_settings.pageLayout().margins()
        margins.setLeft(36)   # 0.5 inch in points
        margins.setRight(36)
        margins.setTop(36)
        margins.setBottom(36)
        
        page_layout = self._printer_settings.pageLayout()
        page_layout.setMargins(margins)
        self._printer_settings.setPageLayout(page_layout)
    
    def show_print_dialog(self) -> bool:
        """Show print dialog and print if accepted."""
        # Create a copy of printer settings for this print job
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if not printer:
            return False
        if (
            not self._printer_settings or
            not isinstance(self._printer_settings, QPrinter)
        ):
            self._setup_default_printer()
        if self._printer_settings:
            printer.setPageLayout(self._printer_settings.pageLayout())
            printer.setColorMode(self._printer_settings.colorMode())
        
        # Show print dialog
        print_dialog = QPrintDialog(printer, self.parent)
        print_dialog.setWindowTitle("Print CAD Drawing")
        
        # Enable print options
        print_dialog.setOptions(
            QPrintDialog.PrintDialogOption.PrintToFile |
            QPrintDialog.PrintDialogOption.PrintSelection |
            QPrintDialog.PrintDialogOption.PrintPageRange |
            QPrintDialog.PrintDialogOption.PrintCurrentPage
        )
        
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            return self._print_to_device(printer)
        
        return False
    
    def show_page_setup_dialog(self) -> bool:
        """Show page setup dialog."""
        if not isinstance(self._printer_settings, QPrinter):
            return False
        page_dialog = QPageSetupDialog(self._printer_settings, self.parent)
        return page_dialog.exec() == QPageSetupDialog.DialogCode.Accepted
    
    def export_to_pdf(self, filename: Optional[str] = None) -> bool:
        """Export the CAD drawing to PDF."""
        if not filename:
            filename, _ = QFileDialog.getSaveFileName(
                self.parent,
                "Export to PDF",
                "",
                "PDF files (*.pdf);;All files (*.*)"
            )
        if not filename:
            return False
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
            
        # Create PDF printer with current settings
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        if not printer:
            return False
        if not self._printer_settings:
            self._setup_default_printer()
        printer.setOutputFileName(filename)
        if self._printer_settings:
            printer.setPageLayout(self._printer_settings.pageLayout())
            printer.setColorMode(self._printer_settings.colorMode())
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        if not self._printer_settings:
            return False
        # Copy settings from the existing printer
        printer.setPageLayout(self._printer_settings.pageLayout())
        printer.setColorMode(self._printer_settings.colorMode())
        
        return self._print_to_device(printer)
    
    def _print_to_device(self, printer: QPrinter) -> bool:
        """Print the CAD scene to the specified device."""
        # Create painter for the printer
        painter = QPainter()
        if not painter.begin(printer):
            return False
        
        try:
            # Get printable content bounds
            scene_bounds = self._get_printable_scene_bounds()
            if scene_bounds.isEmpty():
                # Draw a message indicating no content
                self._draw_no_content_message(painter, printer)
                return True
            
            # Set up page and scaling
            self._setup_print_transform(painter, printer, scene_bounds)
            
            # Render the scene content
            self._render_scene_content(painter, scene_bounds)
            
            return True
            
        finally:
            painter.end()
    
    def _get_printable_scene_bounds(self) -> QRectF:
        """Calculate the bounds of all printable content."""
        bounds = QRectF()
        
        # Include all visible objects
        if hasattr(self.document, 'objects'):
            for obj_id, obj in self.document.objects.objects.items():
                if getattr(obj, 'visible', True) and obj.coords:
                    obj_bounds = self._calculate_object_bounds(obj)
                    if bounds.isEmpty():
                        bounds = obj_bounds
                    else:
                        bounds = bounds.united(obj_bounds)
        
        # Add padding around content (10% of content size or minimum 1 unit)
        if not bounds.isEmpty():
            padding = max(
                max(bounds.width(), bounds.height()) * 0.05,
                1.0
            )
            bounds.adjust(-padding, -padding, padding, padding)
        
        return bounds
    
    def _calculate_object_bounds(self, obj) -> QRectF:
        """Calculate the bounding rectangle for a CAD object."""
        if not obj.coords:
            return QRectF()
        
        # Get coordinate extents
        x_coords = [coord.x for coord in obj.coords]
        y_coords = [coord.y for coord in obj.coords]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Add line width and special object considerations
        line_width = obj.attributes.get('linewidth', 2)
        margin = line_width / 2
        
        # Special handling for circles
        if (
            hasattr(obj, 'object_type') and
            str(obj.object_type).upper() == 'CIRCLE'
        ):
            radius = obj.attributes.get('radius', 0)
            if radius > 0 and obj.coords:
                center = obj.coords[0]
                return QRectF(
                    center.x - radius - margin,
                    center.y - radius - margin,
                    2 * (radius + margin),
                    2 * (radius + margin)
                )
        
        # Default bounding box with margins
        return QRectF(
            min_x - margin, min_y - margin,
            max_x - min_x + 2 * margin,
            max_y - min_y + 2 * margin
        )
    
    def _setup_print_transform(
            self,
            painter: QPainter,
            printer: QPrinter, 
            scene_bounds: QRectF
    ):
        """Set up coordinate transformation for printing."""
        # Get printable page area
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        
        # Calculate scaling to fit content to page
        scale_x = page_rect.width() / scene_bounds.width()
        scale_y = page_rect.height() / scene_bounds.height()
        scale = min(scale_x, scale_y) * 0.85  # Use 85% to ensure margins
        
        # Calculate centering offset
        scaled_width = scene_bounds.width() * scale
        scaled_height = scene_bounds.height() * scale
        offset_x = (page_rect.width() - scaled_width) / 2
        offset_y = (page_rect.height() - scaled_height) / 2
        
        # Apply transformation
        transform = QTransform()
        transform.translate(offset_x + page_rect.x(), offset_y + page_rect.y())
        transform.scale(scale, scale)
        transform.translate(-scene_bounds.x(), -scene_bounds.y())
        
        painter.setTransform(transform)
        
        # Set high-quality rendering
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    
    def _render_scene_content(self, painter: QPainter, bounds: QRectF):
        """Render all visible CAD objects for printing."""
        if not hasattr(self.document, 'objects'):
            return
        
        # Render objects in order (background to foreground)
        for obj_id, obj in self.document.objects.objects.items():
            if getattr(obj, 'visible', True):
                self._render_object_for_print(painter, obj)
    
    def _render_object_for_print(self, painter: QPainter, obj):
        """Render a single CAD object optimized for printing."""
        if not obj.coords:
            return
        
        # Set up pen and brush for printing
        pen, brush = self._get_print_style(obj)
        painter.setPen(pen)
        painter.setBrush(brush)
        
        # Render based on object type
        obj_type = str(getattr(obj, 'object_type', '')).upper()
        
        if obj_type == 'LINE':
            self._render_line_for_print(painter, obj)
        elif obj_type == 'CIRCLE':
            self._render_circle_for_print(painter, obj)
        elif obj_type == 'POINT':
            self._render_point_for_print(painter, obj)
        elif obj_type == 'POLYLINE':
            self._render_polyline_for_print(painter, obj)
        elif obj_type == 'POLYGON':
            self._render_polygon_for_print(painter, obj)
        else:
            # Default rendering for unknown types
            self._render_generic_for_print(painter, obj)
    
    def _get_print_style(self, obj) -> tuple[QPen, QBrush]:
        """Get optimized pen and brush for printing."""
        # Convert colors to print-friendly versions
        color_name = obj.attributes.get('color', 'black')
        
        # Use black for better print contrast
        if color_name in ['white', 'yellow', 'cyan', 'magenta']:
            color = QColor(0, 0, 0)  # Black
        elif color_name == 'red':
            color = QColor(120, 120, 120)  # Dark gray
        elif color_name == 'blue':
            color = QColor(80, 80, 80)  # Darker gray
        elif color_name == 'green':
            color = QColor(100, 100, 100)  # Medium gray
        else:
            color = QColor(0, 0, 0)  # Black default
        
        # Scale line width appropriately for print resolution
        line_width = max(1, obj.attributes.get('linewidth', 2))
        
        pen = QPen(color, line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # Default to no fill for most objects
        brush = QBrush(Qt.BrushStyle.NoBrush)
        
        return pen, brush
    
    def _render_line_for_print(self, painter: QPainter, obj):
        """Render a line object for printing."""
        if len(obj.coords) >= 2:
            start = obj.coords[0]
            end = obj.coords[1]
            painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
    
    def _render_circle_for_print(self, painter: QPainter, obj):
        """Render a circle object for printing."""
        if len(obj.coords) >= 1 and 'radius' in obj.attributes:
            center = obj.coords[0]
            radius = obj.attributes['radius']
            painter.drawEllipse(QPointF(center.x, center.y), radius, radius)
    
    def _render_point_for_print(self, painter: QPainter, obj):
        """Render a point object for printing."""
        if len(obj.coords) >= 1:
            point = obj.coords[0]
            # Get current pen width for cross size
            pen_width = painter.pen().width()
            size = max(pen_width * 3, 6)  # Minimum visible size
            
            # Draw cross
            painter.drawLine(
                QPointF(point.x - size/2, point.y),
                QPointF(point.x + size/2, point.y)
            )
            painter.drawLine(
                QPointF(point.x, point.y - size/2),
                QPointF(point.x, point.y + size/2)
            )
    
    def _render_polyline_for_print(self, painter: QPainter, obj):
        """Render a polyline object for printing."""
        if len(obj.coords) >= 2:
            points = [QPointF(coord.x, coord.y) for coord in obj.coords]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
    
    def _render_polygon_for_print(self, painter: QPainter, obj):
        """Render a polygon object for printing."""
        if len(obj.coords) >= 3:
            points = [QPointF(coord.x, coord.y) for coord in obj.coords]
            # Close the polygon
            for i in range(len(points)):
                next_i = (i + 1) % len(points)
                painter.drawLine(points[i], points[next_i])
    
    def _render_generic_for_print(self, painter: QPainter, obj):
        """Generic rendering for unknown object types."""
        # Just draw lines connecting all coordinates
        if len(obj.coords) >= 2:
            points = [QPointF(coord.x, coord.y) for coord in obj.coords]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
    
    def _draw_no_content_message(self, painter: QPainter, printer: QPrinter):
        """Draw a message when there's no content to print."""
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        
        # Set up font and pen
        font = painter.font()
        font.setPointSize(24)
        painter.setFont(font)
        painter.setPen(QPen(QColor(128, 128, 128)))
        
        # Draw centered message
        message = "No printable content found"
        painter.drawText(page_rect, Qt.AlignmentFlag.AlignCenter, message)