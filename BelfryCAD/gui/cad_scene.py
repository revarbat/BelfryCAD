"""
CadScene - A reusable CAD drawing scene component

This module provides a CadScene class that encapsulates the drawing canvas,
rulers, grid system, and drawing manager functionality into a reusable
component.
"""

from typing import List, Union, Optional, Any, Dict

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsPixmapItem, QGraphicsPathItem, QLabel
)
from PySide6.QtCore import (
    Signal, QPointF, QRectF, Qt, QLineF, QLine, QRect
)
from PySide6.QtGui import (
    QPen, QColor, QPixmap, QBrush, QImage, QGradient,
    QPolygonF, QPolygon, QPainterPath
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


class CadGraphicsScene(QGraphicsScene):
    """
    A CAD-specific graphics scene that extends QGraphicsScene with CAD-specific
    functionality including tagging system and CAD coordinate handling.
    """

    def __init__(self, parent=None):
        """Initialize the CAD graphics scene."""
        super().__init__(parent)

        # Initialize tagging system
        self._tagged_items: Dict[str, List[QGraphicsItem]] = {}  # tag -> [items]
        self._item_tags: Dict[QGraphicsItem, List[str]] = {}     # item -> [tags]

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

    def addTags(self, item: QGraphicsItem, tags: List[str]):
        """
        Add multiple tags to an item.

        Args:
            item: The QGraphicsItem to tag
            tags: List of tag strings to add
        """
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

    def removeTags(self, item: QGraphicsItem, tags: List[str]):
        """
        Remove multiple tags from an item.

        Args:
            item: The QGraphicsItem to untag
            tags: List of tag strings to remove
        """
        for tag in tags:
            self.removeTag(item, tag)

    def getTags(self, item: QGraphicsItem) -> List[str]:
        """
        Get all tags for an item.

        Args:
            item: The QGraphicsItem to get tags for

        Returns:
            List of tag strings
        """
        return self._item_tags.get(item, [])

    def getItemsByTag(self, tag: str) -> List[QGraphicsItem]:
        """
        Get all items with a specific tag.

        Args:
            tag: The tag string to search for

        Returns:
            List of QGraphicsItems with the tag
        """
        return self._tagged_items.get(tag, [])

    def getItemsByTags(self, tags: List[str], all: bool = True) -> List[QGraphicsItem]:
        """
        Get all items with specific tags.

        Args:
            tags: List of tag strings to search for
            all: If True, items must have ALL tags; if False, items need ANY tag

        Returns:
            List of QGraphicsItems matching the tag criteria
        """
        if not tags:
            return []

        if all:
            # Items must have all tags
            items = set(self.getItemsByTag(tags[0]))
            for tag in tags[1:]:
                items &= set(self.getItemsByTag(tag))
            return list(items)
        else:
            # Items can have any tag
            items = set()
            for tag in tags:
                items.update(self.getItemsByTag(tag))
            return list(items)

    def hasTag(self, item: QGraphicsItem, tag: str) -> bool:
        """
        Check if an item has a specific tag.

        Args:
            item: The QGraphicsItem to check
            tag: The tag string to look for

        Returns:
            True if the item has the tag, False otherwise
        """
        return item in self._item_tags and tag in self._item_tags[item]

    def hasAllTags(self, item: QGraphicsItem, tags: List[str]) -> bool:
        """
        Check if an item has all specified tags.

        Args:
            item: The QGraphicsItem to check
            tags: List of tag strings to look for

        Returns:
            True if the item has all tags, False otherwise
        """
        return all(self.hasTag(item, tag) for tag in tags)

    def hasAnyTags(self, item: QGraphicsItem, tags: List[str]) -> bool:
        """
        Check if an item has any of the specified tags.

        Args:
            item: The QGraphicsItem to check
            tags: List of tag strings to look for

        Returns:
            True if the item has any of the tags, False otherwise
        """
        return any(self.hasTag(item, tag) for tag in tags)

    def removeItemsByTags(self, tags: List[str]):
        """
        Remove all items with specified tags.

        Args:
            tags: List of tag strings to remove items for
        """
        items = self.getItemsByTags(tags)
        for item in items:
            self.removeItem(item)

    def tagAsControlPoint(
            self,
            items: List[QGraphicsItem],
            obj: Optional[Any] = None,
            node: Optional[int] = None
    ):
        """
        Add "CP" and "Construction" tags to an item.  This is used to mark
        items that are control points in a CAD object, such as vertices or
        control points in a spline or polyline.
        Args:
            items: List of QGraphicsItem to tag as control points
            obj: Optional CADObject to associate with the control points
            node: Optional node index to associate with the control points
        """
        for item in items:
            self.addTag(item, "CP")
            self.addTag(item, "Construction")
            if obj:
                self.addTag(item, f"Obj_{obj.object_id}")
            if node is not None:
                self.addTag(item, f"Node_{node}")

    def tagAsConstruction(
            self,
            items: List[QGraphicsItem],
            obj: Optional[Any] = None
    ):
        """
        Add "Construction" tags to an item.  This is used to mark items that
        are used for construction lines or temporary items that are not part
        of the final geometry.
        Args:
            items: List of QGraphicsItem to tag as construction
            obj: Optional CADObject to associate with the construction items
        """
        for item in items:
            self.addTag(item, "Construction")
            if obj:
                self.addTag(item, f"Obj_{obj.object_id}")

    def tagAsObject(
            self,
            obj: Any,
            items: List[QGraphicsItem]
    ):
        """
        Add "Actual" and object-specific tags to items associated with a CADObject.
        Args:
            obj: The CADObject to associate with the items
            items: List of QGraphicsItem to tag as actual objects
        """
        for item in items:
            self.addTag(item, "Actual")
            self.addTag(item, f"Obj_{obj.object_id}")

    def itemsNearPoint(
            self,
            point: QPointF,
            radius: float = 5.0,
            tags: Optional[List[str]] = None,
            all: bool = True,
            use_scene: bool = False
    ) -> List[QGraphicsItem]:
        """
        Find all objects near a point within a specified radius.

        Args:
            point: QPointF representing the center point to search around
            radius: Search radius in CAD coordinates
            tags: Optional list of tag strings that items must have
            all: If True, items must have ALL tags; if False, items need
                 ANY tag

        Returns:
            List of QGraphicsItem that are near the specified point
        """
        hit_box = QRectF(
            point.x() - radius, point.y() - radius,
            radius * 2, radius * 2
        )
        hit_box_item = QGraphicsRectItem(hit_box)
        hit_box_item.setVisible(False)  # Invisible item for collision test

        mode = Qt.ItemSelectionMode.IntersectsItemShape
        items = self.items(hit_box, mode=mode)

        nearby_items = []
        for item in items:
            if (
                item.isVisible() and
                item.boundingRect().intersects(hit_box) and
                item.collidesWithItem(hit_box_item, mode=mode)
            ):
                if (
                    not tags or
                    (all and self.hasAllTags(item, tags)) or
                    (not all and self.hasAnyTags(item, tags))
                ):
                    nearby_items.append(item)
        return nearby_items

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
        super().addItem(item)
        if z is not None:
            item.setZValue(z)
        if data is not None:
            item.setData(0, data)
        if tags:
            self.addTags(item, tags)

    def addLineWithTags(
            self,
            line: Union[QLineF, QLine],
            pen: Optional[Union[QPen, QColor]] = None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ) -> QGraphicsLineItem:
        """
        Add a line to the scene with optional tags.

        Args:
            line: QLineF or QLine in CAD space
            pen: Optional QPen, PenStyle, or QColor for the line
            tags: Optional list of tag strings to associate with the line
            z: Optional z-value for the line (controls layering/depth)
            data: Optional data to associate with the line
        """
        if pen is None:
            pen = QPen()
        line_item = super().addLine(line, pen)
        if z is not None:
            line_item.setZValue(z)
        if data is not None:
            line_item.setData(0, data)
        if tags:
            self.addTags(line_item, tags)
        return line_item

    def addRectWithTags(
            self,
            rect: Union[QRectF, QRect],
            pen: Optional[Union[QPen, QColor]] = None,
            brush: Optional[Union[QBrush, QColor, QGradient, QImage, QPixmap]] = None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ) -> QGraphicsRectItem:
        """
        Add a rectangle to the scene with optional tags.

        Args:
            rect: QRectF or QRect in CAD space
            pen: Optional QPen, PenStyle, or QColor for the rectangle
            brush: Optional QBrush, BrushStyle, GlobalColor, QColor, QGradient, QImage, or QPixmap for the rectangle fill
            tags: Optional list of tag strings to associate with the rectangle
            z: Optional z-value for the rectangle (controls layering/depth)
            data: Optional data to associate with the rectangle
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        rectangle = super().addRect(rect, pen, brush)

        if rotation != 0.0:
            rectangle.setRotation(rotation)

        if z is not None:
            rectangle.setZValue(z)
        if data is not None:
            rectangle.setData(0, data)
        if tags:
            self.addTags(rectangle, tags)
        return rectangle

    def addEllipseWithTags(
            self,
            rect: Union[QRectF, QRect],
            pen: Optional[Union[QPen, QColor]] = None,
            brush: Optional[Union[QBrush, QColor, QGradient, QImage, QPixmap]] = None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ) -> QGraphicsEllipseItem:
        """
        Add an ellipse to the scene with optional tags.

        Args:
            rect: QRectF or QRect in CAD space
            pen: Optional QPen, PenStyle, or QColor for the ellipse
            brush: Optional QBrush, BrushStyle, GlobalColor, QColor, QGradient, QImage, or QPixmap for the ellipse fill
            tags: Optional list of tag strings to associate with the ellipse
            z: Optional z-value for the ellipse (controls layering/depth)
            data: Optional data to associate with the ellipse
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        ellipse = super().addEllipse(rect, pen, brush)

        if rotation != 0.0:
            ellipse.setRotation(rotation)

        if z is not None:
            ellipse.setZValue(z)
        if data is not None:
            ellipse.setData(0, data)
        if tags:
            self.addTags(ellipse, tags)
        return ellipse

    def addPolygonWithTags(
            self,
            polygon: Union[QPolygonF, QPolygon, QRectF],
            pen: Optional[Union[QPen, QColor]] = None,
            brush: Optional[Union[QBrush, QColor, QGradient, QImage, QPixmap]] = None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ) -> QGraphicsPolygonItem:
        """
        Add a polygon to the scene with optional tags.

        Args:
            polygon: QPolygonF, QPolygon, or QRectF in CAD space
            pen: Optional QPen, PenStyle, or QColor for the polygon
            brush: Optional QBrush, BrushStyle, GlobalColor, QColor, QGradient, QImage, or QPixmap for the polygon fill
            tags: Optional list of tag strings to associate with the polygon
            z: Optional z-value for the polygon (controls layering/depth)
            data: Optional data to associate with the polygon
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()

        poly_item = super().addPolygon(polygon, pen, brush)
        if z is not None:
            poly_item.setZValue(z)
        if data is not None:
            poly_item.setData(0, data)
        if tags:
            self.addTags(poly_item, tags)
        return poly_item

    def addPixmapWithTags(
            self,
            pixmap: Union[QPixmap, QImage],
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None,
            rotation: float = 0.0
    ) -> QGraphicsPixmapItem:
        """
        Add a pixmap item to the scene with optional tags and rotation.

        Args:
            pixmap: QPixmap or QImage to add
            tags: Optional list of tag strings to associate with the pixmap
            z: Optional z-value for the pixmap (controls layering/depth)
            data: Optional data to associate with the pixmap
            rotation: Rotation angle in degrees (positive = counterclockwise)
        """
        pixmap_item = super().addPixmap(pixmap)

        if rotation != 0.0:
            pixmap_item.setRotation(rotation)

        if z is not None:
            pixmap_item.setZValue(z)
        if data is not None:
            pixmap_item.setData(0, data)
        if tags:
            self.addTags(pixmap_item, tags)
        return pixmap_item

    def addPathWithTags(
            self,
            path: QPainterPath,
            pen: Optional[Union[QPen, Qt.PenStyle, QColor]] = None,
            brush: Optional[Union[QBrush, Qt.BrushStyle, Qt.GlobalColor, QColor, QGradient, QImage, QPixmap]] = None,
            tags: Optional[List[str]] = None,
            z: Optional[float] = None,
            data: Optional[Any] = None
    ) -> QGraphicsPathItem:
        """
        Add a painter path to the scene with optional tags.

        Args:
            path: QPainterPath to add
            pen: Optional QPen, PenStyle, or QColor for the path stroke
            brush: Optional QBrush, BrushStyle, GlobalColor, QColor, QGradient, QImage, or QPixmap for the path fill
            tags: Optional list of tag strings to associate with the path
            z: Optional z-value for the path (controls layering/depth)
            data: Optional data to associate with the path
        """
        if pen is None:
            pen = QPen()
        if brush is None:
            brush = QBrush()
        path_item = super().addPath(path, pen, brush)
        if z is not None:
            path_item.setZValue(z)
        if data is not None:
            path_item.setData(0, data)
        if tags:
            self.addTags(path_item, tags)
        return path_item

    def addControlPoint(
            self,
            object_id: int,
            x: float,
            y: float,
            node: int
    ) -> QGraphicsEllipseItem:
        """
        Add a control point to the scene.
        """
        pen = QPen()
        pen.setColor(QColor("#ff0000"))
        pen.setWidth(0)
        brush = QBrush()
        brush.setColor(QColor("#ff0000"))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        cp = super().addEllipse(x-1.5, y-1.5, 3, 3, pen=pen, brush=brush)
        self.tagAsControlPoint([cp], object_id, node)
        return cp


class CadCanvas(QWidget):
    """
    A reusable CAD canvas component that encapsulates canvas, rulers, and
    drawing functionality with integrated tagging system.

    This class combines:
    - CadGraphicsScene for the drawing canvas
    - CADGraphicsView for custom view behavior
    - RulerManager for horizontal and vertical rulers
    - DrawingManager for object drawing and grid management
    """

    # Signals
    mouse_position_changed = Signal(float, float)  # scene_x, scene_y
    scale_changed = Signal(float)  # new scale factor

    def __init__(self, main_window, document=None, parent=None):
        """
        Initialize the CAD canvas.

        Args:
            main_window: The main window instance this canvas belongs to
            document: The document object for layer management
            parent: Parent widget
        """
        super().__init__(parent)

        self.main_window = main_window
        self.document = document

        # Initialize drawing context fields directly
        self.show_grid: bool = True
        self.show_origin: bool = True
        self.grid_color: str = "#00ffff"
        self.origin_color_x: str = "#ff0000"
        self.origin_color_y: str = "#00ff00"

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
        self.scene = CadGraphicsScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

        # Create custom graphics view
        self.canvas = CADGraphicsView(self.main_window)
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
            self.canvas.view_position_changed.connect(
                self._on_view_position_changed)

        # Create ruler manager
        self.ruler_manager = RulerManager(self.canvas, self)
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

        # Create mouse position label
        self.mouse_pos_label = QLabel()
        self.mouse_pos_label.setStyleSheet(
            "background-color: white; padding: 2px;")

        # Layout rulers and canvas:
        # [corner]   [h-ruler]
        # [v-ruler]  [canvas]
        #            [mouse pos]
        layout.addWidget(corner_widget, 0, 0)
        layout.addWidget(horizontal_ruler, 0, 1)
        layout.addWidget(vertical_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)
        layout.addWidget(self.mouse_pos_label, 2, 1)

    def _connect_events(self):
        """Connect event handlers."""
        # Connect mouse position tracking
        self.canvas.mouseMoveEvent = self._on_mouse_move

    def _on_mouse_move(self, event):
        """Handle mouse movement events."""
        # Get mouse position in scene coordinates
        pos = event.pos()
        scene_pos = self.canvas.mapToScene(pos)

        # Update mouse position display
        self.mouse_pos_label.setText(
            f"X: {scene_pos.x():.3f}, Y: {scene_pos.y():.3f}      {self.scale_factor:.3f}"
        )

        # Emit signal with mouse position
        self.mouse_position_changed.emit(scene_pos.x(), scene_pos.y())

    def _on_view_position_changed(self, scene_x: float, scene_y: float):
        """Handle view position changes from the graphics view."""
        # Update rulers when view position changes
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.update_rulers()

        # Note: Grid doesn't need to be redrawn on scroll/pan, only on zoom
        # Grid lines are in scene coordinates and don't change with view
        # position

    def update_mouse_position(self, scene_x: float, scene_y: float):
        """Update mouse position on rulers and store current coordinates."""
        # Convert scene coordinates back to CAD coordinates
        # Scene coordinates are already in the correct CAD coordinate system
        # We just need to account for the Y-axis flip that was applied
        cad_x = scene_x
        cad_y = -scene_y  # Y-axis flip for Qt coords.

        self._cursor_x = cad_x
        self._cursor_y = cad_y
        print("Debug: CadCanvas mouse position - scene: " +
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
        self.scene.removeItemsByTags(["Actual"])

    # Public API methods

    def get_scene(self) -> CadGraphicsScene:
        """Get the graphics scene."""
        return self.scene

    def get_canvas(self) -> CADGraphicsView:
        """Get the graphics view (canvas)."""
        return self.canvas
    
    def views(self) -> List[CADGraphicsView]:
        """Get the graphics view (canvas)."""
        return [self.canvas]

    def get_drawing_manager(self) -> DrawingManager:
        """Get the drawing manager."""
        return self.drawing_manager

    def get_ruler_manager(self) -> RulerManager:
        """Get the ruler manager."""
        return self.ruler_manager

    @property
    def scale_factor(self) -> float:
        """Get scale factor from the canvas."""
        return self.canvas.get_scale_factor()

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for the canvas."""
        self.canvas.set_tool_manager(tool_manager)

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
            self.redraw_all()

        self.ruler_manager.set_scale_factor(scale_factor)
        self.ruler_manager.update_rulers()
        self.scale_changed.emit(scale_factor)

    def set_grid_visibility(self, visible: bool):
        """Set grid visibility."""
        self.show_grid = visible
        self.redraw_all()

    def set_origin_visibility(self, visible: bool):
        """Set origin axis visibility."""
        self.show_origin = visible
        self.redraw_all()

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

    def redraw_grid(self):
        """Redraw the grid - main grid drawing method"""
        try:
            # Remove existing grid items (both tagged and old Z-value items)
            self.scene.removeItemsByTags([GridTags.GRID])
        except RuntimeError:
            # If items are already deleted, just continue
            pass

        # Get grid info
        grid_info = self._get_grid_info()
        if not grid_info:
            return

        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        dpi = self.physicalDpiX()
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
            self._draw_grid_origin(scalefactor)

        # Draw grid if enabled
        if self.show_grid:
            self._draw_grid_lines(
                xstart, xend, ystart, yend,
                minorspacing, majorspacing,
                superspacing, labelspacing, scalemult,
                scalefactor, srx0, srx1, sry0, sry1)

    def _get_grid_info(self):
        """Calculate grid spacing info - calls ruler's method"""
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        return horizontal_ruler.get_grid_info()

    def _draw_grid_origin(self, scale_factor):
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
        tags = [GridTags.GRID, GridTags.GRID_ORIGIN]

        # Draw X-axis origin line (horizontal)
        y_scene = 0  # Origin Y in CAD coordinates becomes 0 in scene
        if y0 <= y_scene <= y1:  # Origin is visible
            pen = QPen(QColor(x_color))
            pen.setWidthF(pixel_width)
            pen.setCosmetic(True)  # Maintain constant pixel width
            line_item = self.scene.addLineWithTags(
                QLineF(x0, y_scene, x1, y_scene),
                pen=pen, z=-5, tags=tags)

        # Draw Y-axis origin line (vertical)
        x_scene = 0  # Origin X in CAD coordinates becomes 0 in scene
        if x0 <= x_scene <= x1:  # Origin is visible
            pen = QPen(QColor(y_color))
            pen.setWidthF(pixel_width)
            pen.setCosmetic(True)  # Maintain constant pixel width
            line_item = self.scene.addLineWithTags(
                QLineF(x_scene, y0, x_scene, y1),
                pen=pen, z=-5, tags=tags)

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

                    line_item = self.scene.addLineWithTags(
                        QLineF(x_scene, sry0, x_scene, sry1),
                        pen=pen,
                        tags=tags,
                        z=z_val)
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

                    line_item = self.scene.addLineWithTags(
                        QLineF(srx0, y_scene, srx1, y_scene),
                        pen=pen,
                        tags=tags,
                        z=z_val)
                y += minorspacing
