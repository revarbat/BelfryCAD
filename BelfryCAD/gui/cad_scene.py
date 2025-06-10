"""
CadScene - A reusable CAD drawing scene component

This module provides a CadScene class that encapsulates the drawing canvas,
rulers, grid system, and drawing manager functionality into a reusable
component.
"""

from typing import List, Union, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QGraphicsScene, QGraphicsItem
)
from PySide6.QtCore import Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPen, QColor, QPixmap, QBrush, QPainterPath, QPolygonF, QTransform
)

from .drawing_manager import DrawingManager
from .rulers import RulerManager
from .cad_graphics_view import CADGraphicsView
from .colors import Colors


class GridTags:
    """Grid drawing tags for organization and selection"""
    GRID = "Grid"
    GRID_LINE = "GridLine"
    GRID_UNIT_LINE = "GridUnitLine"
    GRID_ORIGIN = "GridOrigin"


class CadScene(QWidget):
    """
    A reusable CAD scene component that encapsulates canvas, rulers, and
    drawing functionality with integrated tagging system.

    This class combines:
    - QGraphicsScene for the drawing canvas
    - CADGraphicsView for custom view behavior
    - RulerManager for horizontal and vertical rulers
    - DrawingManager for object drawing and grid management
    - Tagging system for object organization and selection
    """

    # Signals
    mouse_position_changed = Signal(float, float)  # scene_x, scene_y
    scale_changed = Signal(float)  # new scale factor

    def __init__(self, document=None, parent=None):
        """
        Initialize the CAD scene.

        Args:
            document: The document object for layer management
            parent: Parent widget
        """
        super().__init__(parent)

        self.document = document

        # Initialize drawing context fields directly
        self.show_grid: bool = True
        self.show_origin: bool = True
        self.grid_color: str = "#00ffff"
        self.origin_color_x: str = "#ff0000"
        self.origin_color_y: str = "#00ff00"

        # Initialize tagging system
        self._tagged_items = {}  # tag -> [items]
        self._item_tags = {}     # item -> [tags]

        # Initialize cursor position tracking
        self._cursor_x = 0.0
        self._cursor_y = 0.0

        self._setup_ui()
        self._connect_events()

    def _setup_ui(self):
        """Set up the user interface layout."""
        # Create layout with no spacing or margins
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create graphics scene with large virtual area
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

        # Create custom graphics view
        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)

        # Initialize drawing manager
        self.drawing_manager = DrawingManager()
        self.drawing_manager.set_cad_scene(self)

        # Connect drawing manager to document's layer manager
        if self.document and hasattr(self.document, 'layers'):
            self.drawing_manager.set_layer_manager(self.document.layers)

        # Set drawing manager on canvas for coordinate transformations
        self.canvas.set_drawing_manager(self.drawing_manager)

        # Connect view position changes to ruler updates
        if hasattr(self.canvas, 'view_position_changed'):
            self.canvas.view_position_changed.connect(self._on_view_position_changed)

        # Create ruler manager
        self.ruler_manager = RulerManager(self.canvas, self)
        self.ruler_manager.set_dpi(self.dpi)
        self.ruler_manager.set_scale_factor(self.scale_factor)

        # Get ruler widgets
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        vertical_ruler = self.ruler_manager.get_vertical_ruler()

        # Create corner widget
        corner_widget = QWidget()
        corner_widget.setFixedSize(32, 32)
        corner_widget.setStyleSheet(
            "background-color: white; border: 1px solid black;"
        )

        # Layout rulers and canvas:
        # [corner] [horizontal_ruler]
        # [vertical_ruler] [canvas]
        layout.addWidget(corner_widget, 0, 0)
        layout.addWidget(horizontal_ruler, 0, 1)
        layout.addWidget(vertical_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)

        # Set stretch factors so canvas takes remaining space
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

        # Style the canvas
        self.canvas.setContentsMargins(0, 0, 0, 0)
        self.canvas.setStyleSheet("""
            QGraphicsView {
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        # Initialize grid and axis
        self._draw_grid_origin(self.dpi, self.scale_factor)
        self.redraw_grid()

    @property
    def dpi(self) -> float:
        """Get DPI from the canvas."""
        return self.canvas.get_dpi()

    @property
    def scale_factor(self) -> float:
        """Get scale factor from the canvas."""
        return self.canvas.get_scale_factor()

    def _connect_events(self):
        """Connect internal events."""
        # Connect canvas scroll and mouse events to rulers
        self._connect_ruler_events()

    def _connect_ruler_events(self):
        """Connect canvas events to ruler updates."""
        # Connect scroll events to update rulers when viewport changes
        self.canvas.horizontalScrollBar().valueChanged.connect(
            self._update_rulers_and_grid
        )
        self.canvas.verticalScrollBar().valueChanged.connect(
            self._update_rulers_and_grid
        )

        # Override the canvas mouse move event to update ruler positions
        original_mouse_move = self.canvas.mouseMoveEvent

        def enhanced_mouse_move(event):
            # Call the original mouse move handler first
            original_mouse_move(event)

            # Update ruler mouse position indicators
            scene_pos = self.canvas.mapToScene(event.pos())
            print(f"Debug: Mouse move - scene pos: {scene_pos.x():.4f}, " +
                  f"{scene_pos.y():.4f}")
            # Pass scene coordinates directly - update_mouse_position will handle conversion
            self.update_mouse_position(scene_pos.x(), scene_pos.y())

        # Replace the mouse move event handler
        self.canvas.mouseMoveEvent = enhanced_mouse_move

        # Also connect scene changes to ruler updates
        self.scene.sceneRectChanged.connect(self._update_rulers_and_grid)

    def _update_rulers_and_grid(self):
        """Update both rulers and grid when the view changes."""
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.set_dpi(self.dpi)
            self.ruler_manager.set_scale_factor(self.scale_factor)
            self.ruler_manager.update_rulers()

    # Grid drawing methods (moved from DrawingManager)

    def _get_grid_info(self):
        """Calculate grid spacing info - calls ruler's method"""
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        return horizontal_ruler.get_grid_info()

    def _draw_grid_origin(self, dpi, scale_factor):
        """Draw origin lines with consistent 1.0 pixel width"""
        # Get scene bounds
        scene_rect = self.scene.sceneRect()
        x0, y0 = scene_rect.left(), scene_rect.top()
        x1, y1 = scene_rect.right(), scene_rect.bottom()

        # Origin colors (default if not configured)
        x_color = self.origin_color_x
        y_color = self.origin_color_y

        # Calculate line width that will be 1.0 pixel after view scaling
        # The view applies a scaling transform, so we need to compensate
        view_scale = scale_factor
        pixel_width = 1.0 / view_scale if view_scale > 0 else 1.0

        # Draw X-axis origin line (horizontal)
        y_scene = 0  # Origin Y in CAD coordinates becomes 0 in scene
        if y0 <= y_scene <= y1:  # Origin is visible
            pen = QPen(QColor(x_color))
            pen.setWidthF(pixel_width)
            pen.setCosmetic(True)  # Maintain constant pixel width
            line_item = self.addLine(x0, y_scene, x1, y_scene, pen)
            line_item.setZValue(-5)  # Behind everything but grid lines
            self.addTags(line_item, [GridTags.GRID_ORIGIN])

        # Draw Y-axis origin line (vertical)
        x_scene = 0  # Origin X in CAD coordinates becomes 0 in scene
        if x0 <= x_scene <= x1:  # Origin is visible
            pen = QPen(QColor(y_color))
            pen.setWidthF(pixel_width)
            pen.setCosmetic(True)  # Maintain constant pixel width
            line_item = self.addLine(x_scene, y0, x_scene, y1, pen)
            line_item.setZValue(-5)  # Behind everything but grid lines
            self.addTags(line_item, [GridTags.GRID_ORIGIN])

    def _draw_grid_lines(
            self, xstart, xend, ystart, yend,
            minorspacing, majorspacing,
            superspacing, labelspacing, scalemult,
            scale_factor, srx0, srx1, sry0, sry1
    ):
        """Draw multi-level grid lines with consistent 1.0 pixel width"""

        def quantize(value, spacing):
            """Quantize value to nearest multiple of spacing"""
            return round(value / spacing) * spacing

        def approx(x, y, epsilon=1e-6):
            """Check if two floats are approximately equal"""
            return abs(x - y) < epsilon

        # Calculate colors
        if self.grid_color:
            super_grid_color = Colors.parse(self.grid_color)
        else:
            super_grid_color = Colors.from_hsv(180.0, 1.0, 1.0)
        major_grid_color = Colors.adjust_saturation(super_grid_color, 0.75)
        minor_grid_color = Colors.adjust_saturation(major_grid_color, 0.4)

        # Calculate line width that will be 1.0 pixel after view scaling
        view_scale = scale_factor
        pixel_width = 1.0 / view_scale if view_scale > 0 else 1.0

        # Minor grid lines (most frequent)
        if minorspacing > 0:
            # Vertical minor lines
            x = quantize(xstart, minorspacing)
            while x <= xend:
                x_scene = x * scalemult
                if srx0 <= x_scene <= srx1:
                    tags = [GridTags.GRID]
                    if (superspacing > 0 and
                            approx(x, quantize(x, superspacing))):
                        pen = QPen(super_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_UNIT_LINE)
                        z_val = -6
                    elif (majorspacing > 0 and
                          approx(x, quantize(x, majorspacing))):
                        pen = QPen(major_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_UNIT_LINE)
                        z_val = -7
                    else:
                        pen = QPen(minor_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_LINE)
                        z_val = -8

                    line_item = self.addLine(
                        x, sry0/scalemult, x, sry1/scalemult,
                        pen, z=z_val, tags=tags)
                x += minorspacing

            # Horizontal minor lines
            y = quantize(ystart, minorspacing)
            while y <= yend:
                y_scene = -y * scalemult  # Y-axis flip
                if sry0 <= y_scene <= sry1:
                    tags = [GridTags.GRID]
                    if (superspacing > 0 and
                            approx(y, quantize(y, superspacing))):
                        pen = QPen(super_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_UNIT_LINE)
                        z_val = -6
                    elif (majorspacing > 0 and
                            approx(y, quantize(y, majorspacing))):
                        pen = QPen(major_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_UNIT_LINE)
                        z_val = -7
                    else:
                        pen = QPen(minor_grid_color)
                        pen.setWidthF(pixel_width)
                        pen.setCosmetic(True)  # Maintain constant pixel width
                        tags.append(GridTags.GRID_LINE)
                        z_val = -8

                    line_item = self.addLine(
                        srx0/scalemult, y, srx1/scalemult, y, pen)
                    line_item.setZValue(z_val)
                    self.addTags(line_item, tags)
                y += minorspacing

    def redraw_grid(self):
        """Redraw the grid - main grid drawing method"""
        # Remove existing grid items (both tagged and old Z-value items)
        self.removeItemsByTags([GridTags.GRID])

        # Get grid info
        grid_info = self._get_grid_info()
        if not grid_info:
            return

        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        dpi = self.dpi
        scalefactor = self.scale_factor

        scalemult = dpi * scalefactor / conversion

        # Get visible scene rectangle
        scene_rect = self.scene.sceneRect()
        srx0, sry0 = scene_rect.left(), scene_rect.top()
        srx1, sry1 = scene_rect.right(), scene_rect.bottom()

        # Calculate CAD coordinate ranges (descale from scene coordinates)
        xstart = srx0 / scalemult
        xend = srx1 / scalemult
        ystart = sry1 / (-scalemult)  # Y-axis flip
        yend = sry0 / (-scalemult)    # Y-axis flip

        # Draw origin if enabled
        if self.show_origin:
            self._draw_grid_origin(dpi, scalefactor)

        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid_lines(
                xstart, xend, ystart, yend,
                minorspacing, majorspacing,
                superspacing, labelspacing, scalemult,
                scalefactor, srx0, srx1, sry0, sry1)

    # Public API methods

    def get_scene(self) -> QGraphicsScene:
        """Get the graphics scene."""
        return self.scene

    def get_canvas(self) -> CADGraphicsView:
        """Get the graphics view (canvas)."""
        return self.canvas

    def get_drawing_manager(self) -> DrawingManager:
        """Get the drawing manager."""
        return self.drawing_manager

    def get_ruler_manager(self) -> RulerManager:
        """Get the ruler manager."""
        return self.ruler_manager

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for the canvas."""
        self.canvas.set_tool_manager(tool_manager)

    def set_dpi(self, dpi: float):
        """Set the DPI setting."""
        self.canvas.set_dpi(dpi)
        self.redraw_grid()
        self.ruler_manager.set_dpi(dpi)
        self.ruler_manager.update_rulers()

    def set_scale_factor(
            self,
            scale_factor: float,
            defer_grid_redraw: bool = False
    ):
        """Set the scale factor (zoom level).

        Args:
            scale_factor: The new scale factor
            defer_grid_redraw: If True, skip grid redraw for performance
                              during continuous operations
        """
        self.canvas.set_scale_factor(scale_factor)
        
        # Always redraw grid when scale changes to maintain 1.0 pixel width
        # Only defer during continuous gestures for performance
        if not defer_grid_redraw:
            self.redraw_grid()
        
        self.ruler_manager.set_scale_factor(scale_factor)
        self.ruler_manager.update_rulers()
        self.scale_changed.emit(scale_factor)

    def set_grid_visibility(self, visible: bool):
        """Set grid visibility."""
        self.show_grid = visible
        self.redraw_grid()

    def set_origin_visibility(self, visible: bool):
        """Set origin axis visibility."""
        self.show_origin = visible
        self.redraw_grid()

    def get_current_unit(self) -> str:
        """
        Get the current unit string for display.

        Returns:
            Unit string (e.g., "", "mm", "in")
        """
        grid_info = self._get_grid_info()
        if grid_info:
            # Extract units from grid info tuple
            # (minorspacing, majorspacing, superspacing, labelspacing,
            #  divisor, units, formatfunc, conversion)
            return grid_info[5]  # units is at index 5
        return ""

    def update_mouse_position(self, scene_x: float, scene_y: float):
        """Update mouse position on rulers and store current coordinates."""
        # Convert scene coordinates back to CAD coordinates
        # Scene coordinates are already in the correct CAD coordinate system
        # We just need to account for the Y-axis flip that was applied
        cad_x = scene_x
        cad_y = -scene_y  # Y-axis flip to convert from Qt (Y-down) to CAD (Y-up)

        self._cursor_x = cad_x
        self._cursor_y = cad_y
        print("Debug: CadScene mouse position - scene: " +
              f"({scene_x:.4f}, {scene_y:.4f}), " +
              f"CAD: ({cad_x:.4f}, {cad_y:.4f})")
        self.ruler_manager.update_mouse_position(scene_x, scene_y)
        self.mouse_position_changed.emit(cad_x, cad_y)

    def redraw_all(self):
        """Redraw all scene content."""
        self.drawing_manager.redraw()

    def get_cursor_coords(self) -> tuple[float, float]:
        """
        Get the current mouse cursor coordinates in CAD coordinates.

        Returns:
            Tuple of (cad_x, cad_y) coordinates
        """
        return (self._cursor_x, self._cursor_y)

    def clear_scene(self):
        """Clear all drawable content from the scene."""
        self.removeItemsByTags(["Actual"])

    # Tagging system methods

    def addTag(self, item: QGraphicsItem, tag: str):
        """
        Add a tag to an item.

        Args:
            item: The QGraphicsItem to tag
            tag: The tag string to add
        """
        if item not in self._item_tags:
            self._item_tags[item] = []
        if tag not in self._item_tags[item]:
            self._item_tags[item].append(tag)

        if tag not in self._tagged_items:
            self._tagged_items[tag] = []
        if item not in self._tagged_items[tag]:
            self._tagged_items[tag].append(item)

    def addTags(self, item: QGraphicsItem, tags: Optional[List[str]]):
        """
        Apply a list of tags to an item.

        Args:
            item: The QGraphicsItem to tag
            tags: Optional list of tag strings to apply
        """
        if tags:
            for tag in tags:
                self.addTag(item, tag)

    def removeTag(self, item: QGraphicsItem, tag: str):
        """
        Remove a tag from an item.

        Args:
            item: The QGraphicsItem to untag
            tag: The tag string to remove
        """
        if item in self._item_tags and tag in self._item_tags[item]:
            self._item_tags[item].remove(tag)
            if not self._item_tags[item]:
                del self._item_tags[item]

        if tag in self._tagged_items and item in self._tagged_items[tag]:
            self._tagged_items[tag].remove(item)
            if not self._tagged_items[tag]:
                del self._tagged_items[tag]

    def clearTags(self, item: QGraphicsItem):
        """
        Clear all tags from an item.

        Args:
            item: The QGraphicsItem to clear tags from
        """
        if item in self._item_tags:
            for tag in self._item_tags[item]:
                if tag in self._tagged_items:
                    self._tagged_items[tag].remove(item)
            del self._item_tags[item]

    def getTags(self, item: QGraphicsItem) -> List[str]:
        """
        Get the list of tags for an item.

        Args:
            item: The QGraphicsItem to query

        Returns:
            List of tag strings associated with the item
        """
        return self._item_tags.get(item, [])

    def getItemsByTag(self, tag: str) -> List[QGraphicsItem]:
        """
        Get the list of items associated with a tag.

        Args:
            tag: The tag string to query

        Returns:
            List of QGraphicsItem associated with the tag
        """
        return self._tagged_items.get(tag, [])

    def clearAllTags(self):
        """Clear all tags from all items."""
        self._tagged_items.clear()
        self._item_tags.clear()

    def getItemsByTags(self, tags: List[str],
                       all: bool = True) -> List[QGraphicsItem]:
        """
        Get all graphics items that have the specified tags.

        Args:
            tags: List of tag strings that items must have
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            List of QGraphicsItem that have the specified tags
        """
        if not tags:
            return []

        if all:
            # Items must have ALL tags (intersection)
            # Start with items that have the first tag
            if tags[0] not in self._tagged_items:
                return []

            items_with_all_tags = set(self._tagged_items[tags[0]])

            # Filter by remaining tags - keep only items that have all tags
            for tag in tags[1:]:
                if tag not in self._tagged_items:
                    # If any tag doesn't exist, no items can have all tags
                    return []
                items_with_all_tags &= set(self._tagged_items[tag])

            return list(items_with_all_tags)
        else:
            # Items need ANY tag (union)
            items_with_any_tag = set()

            for tag in tags:
                if tag in self._tagged_items:
                    items_with_any_tag |= set(self._tagged_items[tag])

            return list(items_with_any_tag)

    def removeItemsByTags(self, tags: List[str], all: bool = True) -> int:
        """
        Remove all graphics items that have the specified tags.

        Args:
            tags: List of tag strings that items must have
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            Number of items that were removed
        """
        # Find all items that have the specified tags
        items_to_remove = self.getItemsByTags(tags, all=all)

        # Remove each item from the scene and clean up tags
        for item in items_to_remove:
            # Remove from the graphics scene
            self.scene.removeItem(item)
            # Clean up all tags for this item
            self.clearTags(item)

        return len(items_to_remove)

    def moveItemsByTags(self, tags: List[str], dx: float,
                        dy: float, all: bool = True) -> int:
        """
        Move all graphics items that have the specified tags.

        Args:
            tags: List of tag strings that items must have
            dx: Horizontal distance to move items
            dy: Vertical distance to move items
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            Number of items that were moved
        """
        # Find all items that have the specified tags
        items_to_move = self.getItemsByTags(tags, all=all)

        # Move each item by the specified distance
        for item in items_to_move:
            item.moveBy(dx, dy)

        return len(items_to_move)

    def scaleItemsByTags(self, tags: List[str], sx: float,
                         sy: float, all: bool = True) -> int:
        """
        Scale all graphics items that have the specified tags.

        Args:
            tags: List of tag strings that items must have
            sx: Horizontal scale factor
            sy: Vertical scale factor
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            Number of items that were scaled
        """
        # Find all items that have the specified tags
        items_to_scale = self.getItemsByTags(tags, all=all)

        # Scale each item by the specified factors
        for item in items_to_scale:
            # Get current transform and apply scaling
            current_transform = item.transform()
            current_transform.scale(sx, sy)
            item.setTransform(current_transform)

        return len(items_to_scale)

    def rotateItemsByTags(self, tags: List[str], angle: float,
                          origin_x: Optional[float] = None,
                          origin_y: Optional[float] = None,
                          all: bool = True) -> int:
        """
        Rotate all graphics items that have the specified tags.

        Args:
            tags: List of tag strings that items must have
            angle: Rotation angle in degrees (positive = counterclockwise)
            origin_x: X coordinate of rotation origin (None = use item center)
            origin_y: Y coordinate of rotation origin (None = use item center)
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            Number of items that were rotated
        """
        # Find all items that have the specified tags
        items_to_rotate = self.getItemsByTags(tags, all=all)

        # Rotate each item by the specified angle
        for item in items_to_rotate:
            if origin_x is not None and origin_y is not None:
                # Rotate around specified origin point
                current_transform = item.transform()
                # Translate to origin, rotate, then translate back
                current_transform.translate(origin_x, origin_y)
                current_transform.rotate(angle)
                current_transform.translate(-origin_x, -origin_y)
                item.setTransform(current_transform)
            else:
                # Rotate around item's own center (default Qt behavior)
                current_transform = item.transform()
                current_transform.rotate(angle)
                item.setTransform(current_transform)

        return len(items_to_rotate)

    def transformItemsByTags(self, tags: List[str], transform: QTransform,
                             all: bool = True) -> int:
        """
        Apply a QTransform transformation matrix to all graphics items that
        have the specified tags.

        This method provides a way to apply complex transformations using a
        QTransform matrix to items selected by tags. The transformation matrix
        can include rotation, scaling, translation, shearing, and combinations
        of these operations.

        Args:
            tags: List of tag strings that items must have
            transform: QTransform matrix to apply to each item using
                      setTransform
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            Number of items that were transformed

        Examples:
            # Create a transformation matrix that rotates 45° and scales 150%
            transform = QTransform()
            transform.rotate(45)
            transform.scale(1.5, 1.5)
            count = scene.transformItemsByTags(["movable", "geometry"],
                                               transform)

            # Complex transformation with multiple operations
            transform = QTransform()
            transform.translate(50, 25)  # Move first
            transform.rotate(30)         # Then rotate
            transform.scale(0.8, 1.2)    # Then scale
            count = scene.transformItemsByTags(["shape"], transform)

            # Apply transformation to items with ANY of the specified tags
            transform = QTransform().scale(2.0, 2.0)
            count = scene.transformItemsByTags(["scalable", "resizable"],
                                               transform, all=False)
        """
        # Find all items that have the specified tags
        items_to_transform = self.getItemsByTags(tags, all=all)

        # Apply the transformation matrix to each item
        for item in items_to_transform:
            item.setTransform(transform)

        return len(items_to_transform)

    # Graphics item creation methods with direct CAD coordinates
    def addItem(
            self, item: QGraphicsItem,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ):
        """
        Add an item to the scene with optional tags.

        Args:
            item: The QGraphicsItem to add
            tags: Optional list of tag strings to associate with the item
            z: Optional z-value for the item (controls layering/depth)
            data: Optional data to associate with the item
        """
        self.scene.addItem(item)
        if z is not None:
            item.setZValue(z)
        if data is not None:
            item.setData(0, data)
        if tags:
            self.addTags(item, tags)

    def addLine(
            self,
            x1, y1, x2, y2,
            pen=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ):
        """
        Add a line to the scene with optional tags.

        Args:
            x1, y1, x2, y2: Line coordinates in CAD space
            pen: Optional QPen for the line
            tags: Optional list of tag strings to associate with the line
            z: Optional z-value for the line (controls layering/depth)
            data: Optional data to associate with the line
        """
        if pen is None:
            pen = QPen()
        # Use direct CAD coordinates - view transform handles scaling/flipping
        line = self.scene.addLine(x1, y1, x2, y2, pen)
        if z is not None:
            line.setZValue(z)
        if data is not None:
            line.setData(0, data)
        if tags:
            self.addTags(line, tags)
        return line

    def addRect(
            self, *args,
            pen=None, brush=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ):
        """
        Add a rectangle to the scene with optional tags.

        Args:
            rect: QRectF or (x, y, width, height) as separate args in CAD space
            pen: Optional QPen for the rectangle
            brush: Optional QBrush for the rectangle fill
            tags: Optional list of tag strings to associate with the rectangle
            z: Optional z-value for the rectangle (controls layering/depth)
            data: Optional data to associate with the rectangle
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        if len(args) == 1:
            rect = args[0]
            # Use direct CAD coordinates - view transform handles conversion
            rectangle = self.scene.addRect(rect, pen, brush)
        elif len(args) == 4:
            # Use direct CAD coordinates - view transform handles conversion
            x, y, width, height = args
            rect = QRectF(x, y, width, height)
            rectangle = self.scene.addRect(rect, pen, brush)
        else:
            raise ValueError("Invalid arguments for addRect")

        # Apply rotation if specified
        if rotation != 0.0:
            rectangle.setRotation(rotation)

        if z is not None:
            rectangle.setZValue(z)
        if data is not None:
            rectangle.setData(0, data)
        if tags:
            self.addTags(rectangle, tags)
        return rectangle

    def addEllipse(
            self, *args, pen=None, brush=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ):
        """
        Add an ellipse to the scene with optional tags.

        Args:
            rect: QRectF or (x, y, width, height) as separate args in CAD space
            pen: Optional QPen for the ellipse
            brush: Optional QBrush for the ellipse fill
            tags: Optional list of tag strings to associate with the ellipse
            z: Optional z-value for the ellipse (controls layering/depth)
            data: Optional data to associate with the ellipse
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        if len(args) == 1:
            rect = args[0]
            # Use direct CAD coordinates - view transform handles conversion
            ellipse = self.scene.addEllipse(rect, pen, brush)
        elif len(args) == 4:
            # Use direct CAD coordinates - view transform handles conversion
            x, y, width, height = args
            rect = QRectF(x, y, width, height)
            ellipse = self.scene.addEllipse(rect, pen, brush)
        else:
            raise ValueError("Invalid arguments for addEllipse")

        # Apply rotation if specified
        if rotation != 0.0:
            ellipse.setRotation(rotation)

        if z is not None:
            ellipse.setZValue(z)
        if data is not None:
            ellipse.setData(0, data)
        if tags:
            self.addTags(ellipse, tags)
        return ellipse

    def addPolygon(
            self, polygon: Union[QPolygonF, List],
            pen=None, brush=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ):
        """
        Add a polygon to the scene with optional tags.

        Args:
            polygon: QPolygonF or list of points [(x1, y1), (x2, y2), ...]
                     in CAD space
            pen: Optional QPen for the polygon
            brush: Optional QBrush for the polygon fill
            tags: Optional list of tag strings to associate with the polygon
            z: Optional z-value for the polygon (controls layering/depth)
            data: Optional data to associate with the polygon
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        if isinstance(polygon, list):
            # Convert list of points to QPolygonF - use direct CAD coordinates
            points = []
            for x, y in polygon:
                points.append(QPointF(x, y))
            polygon = QPolygonF(points)
        # If already QPolygonF, use directly - view transform handles
        # conversion

        poly_item = self.scene.addPolygon(polygon, pen, brush)
        if z is not None:
            poly_item.setZValue(z)
        if data is not None:
            poly_item.setData(0, data)
        if tags:
            self.addTags(poly_item, tags)
        return poly_item

    def addPixmap(
            self, pixmap: QPixmap,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ):
        """
        Add a pixmap item to the scene with optional tags and rotation.

        Args:
            pixmap: QPixmap to add
            tags: Optional list of tag strings to associate with the pixmap
            z: Optional z-value for the pixmap (controls layering/depth)
            data: Optional data to associate with the pixmap
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        pixmap_item = self.scene.addPixmap(pixmap)

        # Apply rotation if specified
        if rotation != 0.0:
            pixmap_item.setRotation(rotation)

        if z is not None:
            pixmap_item.setZValue(z)
        if data is not None:
            pixmap_item.setData(0, data)
        if tags:
            self.addTags(pixmap_item, tags)
        return pixmap_item

    def addPath(
            self, path: QPainterPath, pen=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ):
        """
        Add a painter path to the scene with optional tags.

        Args:
            path: QPainterPath to add
            pen: Optional QPen for the path stroke
            tags: Optional list of tag strings to associate with the path
            z: Optional z-value for the path (controls layering/depth)
            data: Optional data to associate with the path
        """
        if pen is None:
            pen = QPen()
        path_item = self.scene.addPath(path, pen)
        if z is not None:
            path_item.setZValue(z)
        if data is not None:
            path_item.setData(0, data)
        if tags:
            self.addTags(path_item, tags)
        return path_item

    def addText(
            self, text: str, font=None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ):
        """
        Add a text item to the scene with optional tags and rotation.

        Args:
            text: The text string to add
            font: Optional QFont for the text
            tags: Optional list of tag strings to associate with the text
            z: Optional z-value for the text (controls layering/depth)
            data: Optional data to associate with the text
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        if font is not None:
            text_item = self.scene.addText(text, font)
        else:
            text_item = self.scene.addText(text)

        # Apply rotation if specified
        if rotation != 0.0:
            text_item.setRotation(rotation)

        if z is not None:
            text_item.setZValue(z)
        if data is not None:
            text_item.setData(0, data)
        if tags:
            self.addTags(text_item, tags)
        return text_item

    # Example method to demonstrate tagged item retrieval
    def example_tagged_item_usage(self):
        """Example usage of adding, tagging, and retrieving items."""
        # Add items with multiple tags
        self.addLine(0, 0, 100, 100, tags=["line_tag", "geometry", "layer1"])
        self.addRect(50, 50, 200, 100, tags=["rect_tag", "geometry", "layer1"])
        self.addEllipse(150, 150, 100, 50,
                        tags=["ellipse_tag", "geometry", "layer2"])

        # Add items with different tag combinations
        self.addLine(200, 200, 300, 300, tags=["construction", "helper"])
        self.addText("Sample Text", tags=["text", "annotation", "layer2"])

        # Retrieve items by specific tags
        lines = self.getItemsByTag("line_tag")
        all_geometry = self.getItemsByTag("geometry")
        layer1_items = self.getItemsByTag("layer1")
        layer2_items = self.getItemsByTag("layer2")
        construction_items = self.getItemsByTag("construction")

        # Example usage patterns:
        # - Hide all items in layer1:
        #   for item in layer1_items: item.setVisible(False)
        # - Change color of all geometry:
        #   for item in all_geometry: modify styling
        # - Select all construction items:
        #   for item in construction_items: item.setSelected(True)

        # Demonstrate tag management
        if lines:
            line_item = lines[0]
            # Add another tag to an existing item
            self.addTag(line_item, "selected")
            # Remove a tag
            self.removeTag(line_item, "layer1")
            # Check current tags
            _ = self.getTags(line_item)  # Example tag retrieval

        return {
            "lines": len(lines),
            "geometry": len(all_geometry),
            "layer1": len(layer1_items),
            "layer2": len(layer2_items),
            "construction": len(construction_items)
        }

    def _on_view_position_changed(self, scene_x: float, scene_y: float):
        """Handle view position changes from the graphics view."""
        # Update rulers when view position changes
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.update_rulers()
        
        # Note: Grid doesn't need to be redrawn on scroll/pan, only on zoom
        # Grid lines are in scene coordinates and don't change with view position
