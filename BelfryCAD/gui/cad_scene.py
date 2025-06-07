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

from .drawing_manager import DrawingManager, DrawingContext
from .rulers import RulerManager
from .cad_graphics_view import CADGraphicsView


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

        # Initialize tagging system
        self._tagged_items = {}  # tag -> [items]
        self._item_tags = {}     # item -> [tags]
        
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

        # Initialize drawing context
        self.drawing_context = DrawingContext(
            scene=self.scene,
            dpi=72.0,
            scale_factor=1.0,
            show_grid=True,
            show_origin=True
        )

        # Initialize drawing manager
        self.drawing_manager = DrawingManager(self.drawing_context)
        
        # Set this CadScene as the scene for tagged item creation
        self.drawing_manager.set_cad_scene(self)

        # Connect drawing manager to document's layer manager
        if self.document and hasattr(self.document, 'layers'):
            self.drawing_manager.set_layer_manager(self.document.layers)

        # Set drawing manager on canvas for coordinate transformations
        self.canvas.set_drawing_manager(self.drawing_manager)

        # Create ruler manager
        self.ruler_manager = RulerManager(self.canvas, self)
        self.ruler_manager.set_drawing_context(self.drawing_context)

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
        self._add_axis_lines()
        self._redraw_grid()

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
            self.update_mouse_position(scene_pos.x(), scene_pos.y())

        # Replace the mouse move event handler
        self.canvas.mouseMoveEvent = enhanced_mouse_move

        # Also connect scene changes to ruler updates
        self.scene.sceneRectChanged.connect(self._update_rulers_and_grid)

    def _add_axis_lines(self):
        """Add coordinate system axis lines at X=0 and Y=0."""
        # X-axis (red, horizontal line at Y=0)
        x_pen = QPen(QColor(255, 0, 0), 1.0)
        x_axis = self.scene.addLine(-1000, 0, 1000, 0, x_pen)
        x_axis.setZValue(-10)  # Behind other elements

        # Y-axis (green, vertical line at X=0)
        y_pen = QPen(QColor(0, 255, 0), 1.0)
        y_axis = self.scene.addLine(0, -1000, 0, 1000, y_pen)
        y_axis.setZValue(-10)  # Behind other elements

    def _redraw_grid(self):
        """Redraw the grid using the drawing manager."""
        self.drawing_manager.redraw_grid()

    def _update_rulers_and_grid(self):
        """Update both rulers and grid when the view changes."""
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.update_rulers()

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

    def get_drawing_context(self) -> DrawingContext:
        """Get the drawing context."""
        return self.drawing_context

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for the canvas."""
        self.canvas.set_tool_manager(tool_manager)

    def set_dpi(self, dpi: float):
        """Set the DPI setting."""
        self.drawing_context.dpi = dpi
        self._redraw_grid()
        self.ruler_manager.update_rulers()

    def set_scale_factor(self, scale_factor: float):
        """Set the scale factor (zoom level)."""
        self.drawing_context.scale_factor = scale_factor
        self._redraw_grid()
        self.ruler_manager.update_rulers()
        self.scale_changed.emit(scale_factor)

    def set_grid_visibility(self, visible: bool):
        """Set grid visibility."""
        self.drawing_context.show_grid = visible
        self._redraw_grid()

    def set_origin_visibility(self, visible: bool):
        """Set origin axis visibility."""
        self.drawing_context.show_origin = visible
        self._redraw_grid()

    def update_mouse_position(self, scene_x: float, scene_y: float):
        """Update mouse position on rulers."""
        self.ruler_manager.update_mouse_position(scene_x, scene_y)
        self.mouse_position_changed.emit(scene_x, scene_y)

    def redraw_all(self):
        """Redraw all scene content."""
        self.drawing_manager.redraw()

    def clear_scene(self):
        """Clear all drawable content from the scene."""
        # Note: This would clear objects but preserve grid/axes
        pass

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
            all: If True, items must have ALL tags; if False, items need ANY tag

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
            all: If True, items must have ALL tags; if False, items need ANY tag

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
            all: If True, items must have ALL tags; if False, items need ANY tag

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
            all: If True, items must have ALL tags; if False, items need ANY tag

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
            all: If True, items must have ALL tags; if False, items need ANY tag

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

    # QGraphicsScene add* methods with tagging support

    def addItem(self, item: QGraphicsItem, tags: Optional[List[str]] = None,
                z: Optional[float] = None, data: Optional[Any] = None):
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
        self.addTags(item, tags)

    def addLine(self, x1, y1, x2, y2, pen=None,
                tags: Optional[List[str]] = None, z: Optional[float] = None,
                data: Optional[Any] = None):
        """
        Add a line to the scene with optional tags.

        Args:
            x1, y1, x2, y2: Line coordinates
            pen: Optional QPen for the line
            tags: Optional list of tag strings to associate with the line
            z: Optional z-value for the line (controls layering/depth)
            data: Optional data to associate with the line
        """
        if pen is None:
            pen = QPen()
        line = self.scene.addLine(x1, y1, x2, y2, pen)
        if z is not None:
            line.setZValue(z)
        if data is not None:
            line.setData(0, data)
        self.addTags(line, tags)
        return line

    def addRect(self, *args, pen=None, brush=None,
                tags: Optional[List[str]] = None, z: Optional[float] = None,
                data: Optional[Any] = None):
        """
        Add a rectangle to the scene with optional tags.

        Args:
            rect: QRectF or (x, y, width, height) as separate args
            pen: Optional QPen for the rectangle
            brush: Optional QBrush for the rectangle fill
            tags: Optional list of tag strings to associate with the rectangle
            z: Optional z-value for the rectangle (controls layering/depth)
            data: Optional data to associate with the rectangle
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()
        
        if len(args) == 1:
            rect = args[0]
        elif len(args) == 4:
            rect = QRectF(args[0], args[1], args[2], args[3])
        else:
            raise ValueError("Invalid arguments for addRect")
            
        rectangle = self.scene.addRect(rect, pen, brush)
        if z is not None:
            rectangle.setZValue(z)
        if data is not None:
            rectangle.setData(0, data)
        self.addTags(rectangle, tags)
        return rectangle

    def addEllipse(self, *args, pen=None, brush=None,
                   tags: Optional[List[str]] = None, z: Optional[float] = None,
                   data: Optional[Any] = None):
        """
        Add an ellipse to the scene with optional tags.

        Args:
            rect: QRectF or (x, y, width, height) as separate args
            pen: Optional QPen for the ellipse
            brush: Optional QBrush for the ellipse fill
            tags: Optional list of tag strings to associate with the ellipse
            z: Optional z-value for the ellipse (controls layering/depth)
            data: Optional data to associate with the ellipse
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()
            
        if len(args) == 1:
            rect = args[0]
        elif len(args) == 4:
            rect = QRectF(args[0], args[1], args[2], args[3])
        else:
            raise ValueError("Invalid arguments for addEllipse")
            
        ellipse = self.scene.addEllipse(rect, pen, brush)
        if z is not None:
            ellipse.setZValue(z)
        if data is not None:
            ellipse.setData(0, data)
        self.addTags(ellipse, tags)
        return ellipse

    def addPolygon(self, polygon: Union[QPolygonF, List], pen=None,
                   brush=None, tags: Optional[List[str]] = None,
                   z: Optional[float] = None, data: Optional[Any] = None):
        """
        Add a polygon to the scene with optional tags.

        Args:
            polygon: QPolygonF or list of points [(x1, y1), (x2, y2), ...]
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
            polygon = QPolygonF([QPointF(x, y) for x, y in polygon])
        poly_item = self.scene.addPolygon(polygon, pen, brush)
        if z is not None:
            poly_item.setZValue(z)
        if data is not None:
            poly_item.setData(0, data)
        self.addTags(poly_item, tags)
        return poly_item

    def addPixmap(self, pixmap: QPixmap, tags: Optional[List[str]] = None,
                  z: Optional[float] = None, data: Optional[Any] = None):
        """
        Add a pixmap item to the scene with optional tags.

        Args:
            pixmap: QPixmap to add
            tags: Optional list of tag strings to associate with the pixmap
            z: Optional z-value for the pixmap (controls layering/depth)
            data: Optional data to associate with the pixmap
        """
        pixmap_item = self.scene.addPixmap(pixmap)
        if z is not None:
            pixmap_item.setZValue(z)
        if data is not None:
            pixmap_item.setData(0, data)
        self.addTags(pixmap_item, tags)
        return pixmap_item

    def addPath(self, path: QPainterPath, pen=None,
                tags: Optional[List[str]] = None, z: Optional[float] = None,
                data: Optional[Any] = None):
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
        self.addTags(path_item, tags)
        return path_item

    def addText(self, text: str, font=None, tags: Optional[List[str]] = None,
                z: Optional[float] = None, data: Optional[Any] = None):
        """
        Add a text item to the scene with optional tags.

        Args:
            text: The text string to add
            font: Optional QFont for the text
            tags: Optional list of tag strings to associate with the text
            z: Optional z-value for the text (controls layering/depth)
            data: Optional data to associate with the text
        """
        if font is not None:
            text_item = self.scene.addText(text, font)
        else:
            text_item = self.scene.addText(text)
        if z is not None:
            text_item.setZValue(z)
        if data is not None:
            text_item.setData(0, data)
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
