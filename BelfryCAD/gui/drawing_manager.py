"""
This module translates all the cadobjects_object_draw_* procedures from TCL
to Python, providing comprehensive object drawing functionality for the
pyTkCAD application.

The DrawingManager class serves as the main interface for all drawing
operations, maintaining compatibility with the original TCL implementation
while leveraging Qt's powerful graphics system.
"""

import math
import os
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainterPath, QPolygonF, QPixmap, QFont,
    QTransform, QPainter
)
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtSvg import QSvgRenderer

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from .colors import Colors


class ConstructionCADObject:
    """CAD-like object for construction items that don't have real
    CAD objects"""

    def __init__(self, object_id: str, object_type: ObjectType):
        self.object_id = object_id
        self.object_type = object_type


class DrawingTags(Enum):
    """Drawing tags for organization and selection"""
    ALL_DRAWN = "AllDrawn"
    ACTUAL = "Actual"
    FILLED = "FILLED"
    BEZIER = "BEZIER"
    TEXT = "TEXT"
    PTEXT = "PTEXT"
    PIMAGE = "PIMAGE"
    CP = "CP"  # Control Point
    CL = "CL"  # Control Line
    CONST_LINES = "ConstLines"
    CONSTRUCTION_PT = "ConstructionPt"
    GRID = "Grid"
    GRID_LINE = "GridLine"
    GRID_UNIT_LINE = "GridUnitLine"
    GRID_ORIGIN = "GridOrigin"
    SNAP_GUIDE = "SnapGuide"
    BG = "BG"


class NodeType(Enum):
    """Control point node types"""
    OVAL = "oval"
    DIAMOND = "diamond"
    RECTANGLE = "rectangle"
    ENDNODE = "endnode"


class DrawingManager:
    """
    Main drawing manager that translates TCL cadobjects drawing procedures
    to Python/Qt. Maintains compatibility with the original TCL
    cadobjects.tcl structure.
    """

    def __init__(self, cad_scene=None):
        self.construction_points: List[Point] = []
        self.node_images: Dict[NodeType, Dict[str, QPixmap]] = {}
        self._init_node_images()

        # Reference to CadScene for tagged item creation
        self.cad_scene = cad_scene

        # Layer management - will be set by main window
        self.layer_manager = None

    def set_cad_scene(self, cad_scene):
        """Set the CadScene reference for tagged item creation"""
        self.cad_scene = cad_scene

    def set_layer_manager(self, layer_manager):
        """Set the layer manager for accessing layer data"""
        self.layer_manager = layer_manager

    def get_layer_color(self, layer_id: int) -> Optional[str]:
        """Get the color of a layer by layer ID"""
        if not self.layer_manager:
            return None

        layer_data = self.layer_manager.get_layer_data(layer_id)
        if layer_data:
            return layer_data.get('color')
        return None

    def get_layer_visibility(self, layer_id: int) -> bool:
        """Get the visibility status of a layer"""
        if not self.layer_manager:
            return True  # Default to visible if no layer manager

        layer_data = self.layer_manager.get_layer_data(layer_id)
        if layer_data:
            return layer_data.get('visible', True)
        return True

    def get_layer_locked(self, layer_id: int) -> bool:
        """Get the lock status of a layer"""
        if not self.layer_manager:
            return False  # Default to unlocked if no layer manager

        layer_data = self.layer_manager.get_layer_data(layer_id)
        if layer_data:
            return layer_data.get('locked', False)
        return False

    def add_item_tag(self, item: QGraphicsItem, tag: str):
        """Add a tag to a graphics item"""
        if self.cad_scene:
            self.cad_scene.addTag(item, tag)
        else:
            # Fallback for cases where cad_scene is not set
            pass

    def remove_item_tag(self, item: QGraphicsItem, tag: str):
        """Remove a tag from a graphics item"""
        if self.cad_scene:
            self.cad_scene.removeTag(item, tag)
        else:
            # Fallback for cases where cad_scene is not set
            pass

    def get_items_by_tag(self, tag: str) -> List[QGraphicsItem]:
        """Get all graphics items with a specific tag"""
        if self.cad_scene:
            return self.cad_scene.scene.getItemsByTag(tag)
        else:
            return []

    def get_items_by_any_tag(self, tags: List[str]) -> List[QGraphicsItem]:
        """Get all graphics items that have any of the specified tags"""
        items = []
        for tag in tags:
            items.extend(self.get_items_by_tag(tag))
        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        return unique_items

    def get_items_by_all_tags(self, tags: List[str]) -> List[QGraphicsItem]:
        """Get all graphics items that have all of the specified tags"""
        if not tags:
            return []

        # Start with items that have the first tag
        items = set(self.get_items_by_tag(tags[0]))

        # Intersect with items that have each subsequent tag
        for tag in tags[1:]:
            items &= set(self.get_items_by_tag(tag))

        return list(items)

    def get_item_tags(self, item: QGraphicsItem) -> List[str]:
        """Get all tags for a graphics item"""
        if self.cad_scene:
            return self.cad_scene.getTags(item)
        else:
            return []

    def remove_items_by_tag(self, tag: str):
        """Remove all graphics items with a specific tag from the scene"""
        # Make a copy to avoid modification during iteration
        items = list(self.get_items_by_tag(tag))
        for item in items:
            # Remove all tags from this item
            # Also copy this list
            for tag_to_remove in list(self.get_item_tags(item)):
                self.remove_item_tag(item, tag_to_remove)
            # Remove from scene
            if self.cad_scene:
                self.cad_scene.removeItem(item)

    def clearAllTags(self):
        """Clear all tagging data"""
        if self.cad_scene:
            self.cad_scene.clearAllTags()
        else:
            # Fallback for cases where cad_scene is not set
            pass

    def _init_node_images(self):
        """Initialize node type images from SVG files"""

        # Get the directory containing this module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(module_dir, "..", "images")

        # Node type to filename mapping
        node_files = {
            NodeType.OVAL: "nodes-oval",
            NodeType.DIAMOND: "nodes-diamond",
            NodeType.RECTANGLE: "nodes-rectangle",
            NodeType.ENDNODE: "nodes-endnode"
        }

        self.node_images = {}
        for node_type, base_name in node_files.items():
            # Load unselected version
            unsel_path = os.path.join(images_dir, f"{base_name}.svg")
            sel_path = os.path.join(images_dir, f"{base_name}-sel.svg")

            node_data = {}

            # Load unselected SVG
            if os.path.exists(unsel_path):
                renderer = QSvgRenderer(unsel_path)
                pixmap = QPixmap(16, 16)  # Standard node size
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                node_data['unselected'] = pixmap
            else:
                # Fallback to simple colored circle if SVG not found
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setPen(QPen(QColor(0, 0, 255)))
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(2, 2, 12, 12)
                painter.end()
                node_data['unselected'] = pixmap

            # Load selected SVG
            if os.path.exists(sel_path):
                renderer = QSvgRenderer(sel_path)
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                node_data['selected'] = pixmap
            else:
                # Fallback to highlighted version if selected SVG not found
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setPen(QPen(QColor(255, 255, 0)))
                painter.setBrush(QBrush(QColor(255, 255, 0)))
                painter.drawEllipse(2, 2, 12, 12)
                painter.end()
                node_data['selected'] = pixmap
            self.node_images[node_type] = node_data

    def get_dpi(self) -> float:
        """Get DPI setting"""
        if self.cad_scene:
            return self.cad_scene.dpi
        return 96.0  # Default DPI

    def get_scale_factor(self) -> float:
        """Get current scale factor"""
        if self.cad_scene:
            return self.cad_scene.scale_factor
        return 1.0  # Default scale factor

    def scale_coords(self, coords: List[float]) -> List[float]:
        """Scale coordinates using CadGraphicsView scaling method"""
        if self.cad_scene and hasattr(self.cad_scene, 'view'):
            return self.cad_scene.view.scale_coords(coords)
        # Fallback implementation if no CadScene or view available
        return coords[:]

    def descale_coords(self, coords: List[float]) -> List[float]:
        """Descale coordinates using CadGraphicsView scaling method"""
        if self.cad_scene and hasattr(self.cad_scene, 'view'):
            return self.cad_scene.view.descale_coords(coords)
        # Fallback implementation if no CadScene or view available
        return coords[:]

    def get_stroke_width(self, obj: CADObject) -> float:
        """Calculate stroke width based on object properties and scale"""
        width = obj.attributes.get('linewidth', 1.0)

        # Handle special width values from TCL
        if isinstance(width, str):
            if width.lower() == "hairline":
                width = 0.0
            elif width.lower() == "thin":
                width = 0.0001
            else:
                try:
                    width = float(width)
                except ValueError:
                    width = 1.0

        # Apply only scale factor for zoom/pan operations
        # DPI is already handled in coordinate transformations
        scaled_width = width * self.get_scale_factor()

        # Minimum width for visibility
        if scaled_width < 0.5:
            scaled_width = 0.5

        return scaled_width

    def get_construction_line_width(self) -> float:
        """Calculate proper line width for construction lines and
        control lines"""
        # Construction lines should be scaled with DPI and scale_factor
        # for visibility
        # Based on TCL implementation that uses strokewidth 0.75 or width 1.0
        base_width = 1.0  # Base construction line width

        scaled_width = (base_width * self.get_dpi() / 72.0 *
                        self.get_scale_factor())

        # Minimum width for visibility (but allow it to be thin at high zoom)
        if scaled_width < 0.25:
            scaled_width = 0.25

        return scaled_width

    def get_object_color(self, obj: CADObject,
                         default_color: str = "black") -> QColor:
        """Get object color with layer fallback"""
        color_name = obj.attributes.get('color', '')

        if not color_name or color_name == "none":
            # Get layer color if object has no explicit color
            layer_color = self.get_layer_color(obj.layer)
            if layer_color:
                color_name = layer_color
            else:
                color_name = default_color

        return Colors.parse(color_name)

    def get_dash_pattern(self, dash_name: str) -> List[float]:
        """Get dash pattern for line styles"""
        if not dash_name:
            return []

        # Common dash patterns from TCL
        patterns = {
            "": [],
            "solid": [],
            "dash": [5, 5],
            "dot": [2, 3],
            "dashdot": [5, 3, 2, 3],
            "centerline": [10, 3, 2, 3, 2, 3],
            "hidden": [3, 3],
            "phantom": [10, 3, 3, 3, 3, 3]
        }

        return patterns.get(dash_name.lower(), [])

    def object_draw(self, obj: CADObject, override_color: str = ""):
        """
        Main object drawing function - translates cadobjects_object_draw
        Returns list of graphics items created for tracking
        """
        items = []

        if not obj.visible:
            return items

        # Check layer visibility - skip drawing if layer is hidden
        if hasattr(obj, 'layer') and obj.layer:
            if not self.get_layer_visibility(obj.layer):
                return items

        # Handle GROUP type objects
        if obj.object_type.value == "group":
            children = obj.attributes.get('children', [])
            for child in children:
                child_items = self.object_draw(child, override_color)
                items.extend(child_items)
            return items

        # Get object properties
        color = (override_color if override_color else
                 self.get_object_color(obj))
        fill_color = obj.attributes.get('fillcolor', '')
        if fill_color and fill_color != "none":
            fill = QBrush(Colors.parse(fill_color))
        else:
            fill = QBrush(Qt.BrushStyle.NoBrush)

        width = self.get_stroke_width(obj)
        dash_pattern = self.get_dash_pattern(
            obj.attributes.get('linedash', ''))

        # Create pen
        color_obj = (Colors.parse(color) if isinstance(color, str)
                     else color)
        pen = QPen(color_obj, width)
        if dash_pattern:
            pen.setDashPattern(dash_pattern)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        # Remove existing graphics for this object
        self._delete_object_graphics(obj)

        # Try custom drawing method first
        if not self._try_custom_drawing(obj, pen, fill):
            # Fall back to decomposition-based drawing
            items = self.object_drawobj_from_decomposition(obj, pen, fill)

        # Draw selection if selected
        if obj.selected:
            selection_items = self._draw_selection(obj)
            if selection_items:
                items.extend(selection_items)

        return items

    def _delete_object_graphics(self, obj: CADObject):
        """Remove existing graphics items for an object"""
        # TODO: Track and remove graphics items by object ID
        pass

    def _try_custom_drawing(self, obj: CADObject, pen: QPen,
                            fill: QBrush) -> bool:
        """Try object-specific custom drawing methods"""
        # TODO: This would call object-specific drawing methods
        # For now, return False to use decomposition
        return False

    def object_drawobj_from_decomposition(self, obj: CADObject, pen: QPen,
                                          fill: QBrush):
        """
        Draw object from decomposition - translates
        cadobjects_object_drawobj_from_decomposition
        Returns list of graphics items created
        """
        items = []
        decomposition = self._decompose_object(obj)

        for shape_type, shape_data in decomposition:
            if shape_type == "ELLIPSE":
                item = self._draw_ellipse(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "CIRCLE":
                item = self._draw_circle(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "RECTANGLE":
                item = self._draw_rectangle(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "ARC":
                item = self._draw_arc(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "BEZIER":
                item = self._draw_bezier(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "LINES":
                line_items = self._draw_lines(shape_data, pen, fill, obj)
                if line_items:
                    items.extend(line_items)
            elif shape_type == "TEXT":
                item = self._draw_text(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "ROTTEXT":
                item = self._draw_rottext(shape_data, pen, fill, obj)
                if item:
                    items.append(item)
            elif shape_type == "IMAGE":
                item = self._draw_image(shape_data, pen, fill, obj)
                if item:
                    items.append(item)

        return items

    def _decompose_object(self, obj: CADObject) -> List[Tuple[str, Any]]:
        """
        Decompose CAD object into basic drawing primitives
        """
        decomposition = []

        if obj.object_type == ObjectType.LINE:
            if len(obj.coords) >= 2:
                coords = []
                for point in obj.coords:
                    coords.extend([point.x, point.y])
                decomposition.append(("LINES", coords))

        elif obj.object_type == ObjectType.CIRCLE:
            if len(obj.coords) >= 1 and 'radius' in obj.attributes:
                center = obj.coords[0]
                radius = obj.attributes['radius']
                decomposition.append(("CIRCLE", [center.x, center.y, radius]))

        elif obj.object_type == ObjectType.ARC:
            if len(obj.coords) >= 1:
                center = obj.coords[0]
                radius = obj.attributes.get('radius', 0)
                start_angle = obj.attributes.get('start_angle', 0)
                end_angle = obj.attributes.get('end_angle', 0)
                extent = end_angle - start_angle
                decomposition.append(("ARC", [center.x, center.y, radius,
                                              math.degrees(start_angle),
                                              math.degrees(extent)]))

        elif obj.object_type == ObjectType.BEZIER:
            if len(obj.coords) >= 4:
                coords = []
                for point in obj.coords:
                    coords.extend([point.x, point.y])
                decomposition.append(("BEZIER", coords))

        elif obj.object_type == ObjectType.POLYGON:
            if len(obj.coords) >= 3:
                coords = []
                for point in obj.coords:
                    coords.extend([point.x, point.y])
                # Close the polygon
                if obj.coords[0] != obj.coords[-1]:
                    coords.extend([obj.coords[0].x, obj.coords[0].y])
                decomposition.append(("LINES", coords))

        elif obj.object_type == ObjectType.TEXT:
            if len(obj.coords) >= 1:
                pos = obj.coords[0]
                text = obj.attributes.get('text', 'Text')
                font_family = obj.attributes.get('font_family', 'Arial')
                font_size = obj.attributes.get('font_size', 12)
                justification = obj.attributes.get('justification', 'left')
                font = [font_family, font_size]
                decomposition.append(("TEXT", [pos.x, pos.y, text, font,
                                               justification]))

        return decomposition

    def _draw_ellipse(self, data: List[float], pen: QPen, fill: QBrush,
                      obj: CADObject):
        """Draw ellipse primitive"""
        cx, cy, rad1, rad2 = data

        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL]
        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2,
                pen=pen, brush=fill, z=1, tags=tags, data=obj.object_id
            )
        else:
            return None  # Cannot draw without scene
        return ellipse

    def _draw_circle(self, data: List[float], pen: QPen, fill: QBrush,
                     obj: CADObject):
        """Draw circle primitive"""
        cx, cy, radius = data

        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL]
        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2,
                pen=pen, brush=fill, z=1, tags=tags, data=obj.object_id
            )
        else:
            return None  # Cannot draw without scene
        return ellipse

    def _draw_rectangle(self, data: List[float], pen: QPen, fill: QBrush,
                        obj: CADObject):
        """Draw rectangle primitive"""
        x0, y0, x1, y1 = data

        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL]
        if self.cad_scene:
            rect = self.cad_scene.addRect(
                x0, y0, x1 - x0, y1 - y0, pen=pen, brush=fill,
                z=1, tags=tags, data=obj.object_id)
        else:
            return None  # Cannot draw without scene
        return rect

    def _draw_arc(self, data: List[float], pen: QPen, fill: QBrush,
                  obj: CADObject):
        """Draw arc primitive"""
        cx, cy, radius, start_deg, extent_deg = data

        # Convert to Qt's angle system (16ths of a degree)
        start_angle_16 = int(start_deg * 16)
        span_angle_16 = int(extent_deg * 16)
        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL]
        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2,
                pen=pen, brush=QBrush(Qt.BrushStyle.NoBrush),
                z=1, tags=tags, data=obj.object_id
            )
        else:
            return None  # Cannot draw without scene
        ellipse.setStartAngle(start_angle_16)
        ellipse.setSpanAngle(span_angle_16)
        return ellipse

    def _draw_bezier(self, data: List[float], pen: QPen, fill: QBrush,
                     obj: CADObject):
        """Draw bezier curve primitive"""
        if len(data) < 8:
            return

        # Create QPainterPath for bezier curve
        path = QPainterPath()
        x0, y0 = data[0], data[1]
        path.moveTo(x0, y0)

        # Process control points in groups of 6 (3 points = x1,y1,x2,y2,x3,y3)
        for i in range(2, len(data), 6):
            if i + 5 < len(data):
                x1, y1, x2, y2, x3, y3 = data[i:i + 6]
                path.cubicTo(x1, y1, x2, y2, x3, y3)

        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL, DrawingTags.BEZIER]
        if self.cad_scene:
            path_item = self.cad_scene.addPath(
                path, pen, fill, z=1, tags=tags, data=obj.object_id)
        else:
            return None  # Cannot draw without scene
        return path_item

    def _draw_lines(self, data: List[float], pen: QPen, fill: QBrush,
                    obj: CADObject):
        """Draw lines/polyline primitive"""
        if len(data) < 4:
            return

        # Check if path is closed
        is_closed = (len(data) >= 4 and
                     abs(data[0] - data[-2]) < 1e-6 and
                     abs(data[1] - data[-1]) < 1e-6)

        if is_closed and fill.style() != Qt.BrushStyle.NoBrush:
            # Draw as polygon
            points = []
            for i in range(0, len(data), 2):
                points.append(QPointF(data[i], data[i + 1]))

            polygon = QPolygonF(points)
            tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL,
                    DrawingTags.FILLED]
            if self.cad_scene:
                poly_item = self.cad_scene.addPolygon(
                    polygon, pen=pen, brush=fill,
                    z=1, tags=tags, data=obj.object_id)
            else:
                return []  # Cannot draw without scene
            return [poly_item]
        else:
            # Draw as polyline
            path = QPainterPath()
            path.moveTo(data[0], data[1])

            for i in range(2, len(data), 2):
                path.lineTo(data[i], data[i + 1])

            tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL]
            if self.cad_scene:
                path_item = self.cad_scene.addPath(
                    path, pen, QBrush(Qt.BrushStyle.NoBrush),
                    z=1, tags=tags, data=obj.object_id)
            else:
                return []  # Cannot draw without scene
            return [path_item]

    def _draw_text(self, data: List, pen: QPen, fill: QBrush, obj: CADObject):
        """Draw text primitive"""
        cx, cy, text, font_spec, justification = data

        # Create font
        font_family, font_size = font_spec
        scaled_font_size = int(font_size * self.get_scale_factor() *
                               2.153 + 0.5)
        if scaled_font_size < 1:
            scaled_font_size = 1

        font = QFont(font_family)
        font.setPointSize(scaled_font_size)

        # Create text item
        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL, DrawingTags.TEXT]
        if self.cad_scene:
            text_item = self.cad_scene.addText(
                text, font, z=1, tags=tags, data=obj.object_id)
        else:
            return None  # Cannot draw without scene
        text_item.setDefaultTextColor(pen.color())

        # Set anchor based on justification
        if justification == "center":
            # Center alignment
            bounds = text_item.boundingRect()
            text_item.setPos(cx - bounds.width() / 2, cy)
        elif justification == "right":
            # Right alignment
            bounds = text_item.boundingRect()
            text_item.setPos(cx - bounds.width(), cy)
        else:
            # Left alignment (default)
            text_item.setPos(cx, cy)
        return text_item

    def _draw_rottext(self, data: List, pen: QPen, fill: QBrush,
                      obj: CADObject):
        """Draw rotated text primitive"""
        cx, cy, text, font_spec, justification, rotation = data

        # Create font
        font_family, font_size = font_spec
        scaled_font_size = int(font_size * self.get_scale_factor() *
                               2.153 + 0.5)
        if scaled_font_size < 1:
            scaled_font_size = 1

        font = QFont(font_family)
        font.setPointSize(scaled_font_size)

        tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL, DrawingTags.PTEXT]

        # Create text item
        if self.cad_scene:
            text_item = self.cad_scene.addText(
                text, font, z=1, tags=tags, data=obj.object_id)
        else:
            return None  # Cannot draw without scene
        text_item.setDefaultTextColor(pen.color())

        # Apply rotation
        transform = QTransform()
        transform.rotate(-rotation)  # Qt uses negative angles
        text_item.setTransform(transform)

        # Set position
        text_item.setPos(cx, cy)
        return text_item

    def _draw_image(self, data: List, pen: QPen, fill: QBrush, obj: CADObject):
        """Draw image primitive"""
        cx, cy, width, height, rotation, pixmap = data

        # Create pixmap item
        if isinstance(pixmap, QPixmap):
            tags = [DrawingTags.ALL_DRAWN, DrawingTags.ACTUAL,
                    DrawingTags.PIMAGE]
            if self.cad_scene:
                image_item = self.cad_scene.addPixmap(
                    pixmap, z=1, tags=tags, data=obj.object_id)
            else:
                return None  # Cannot draw without scene

            # Scale and position
            image_item.setScale(width / pixmap.width())
            image_item.setPos(cx - width / 2, cy - height / 2)

            # Apply rotation if needed
            if abs(rotation) > 0.01:
                transform = QTransform()
                transform.rotate(-rotation)
                image_item.setTransform(transform)
            return image_item
        return None  # No valid pixmap provided

    def _draw_selection(self, obj: CADObject):
        """Draw selection highlight around object"""
        bounds = obj.get_bounds()
        if bounds:
            x1, y1, x2, y2 = bounds

            padding = 3
            select_pen = QPen(QColor(255, 255, 0), 1)  # Yellow selection
            select_pen.setDashPattern([3, 3])  # Dashed line

            select_rect = None
            if self.cad_scene:
                select_rect = self.cad_scene.addRect(
                    x1 - padding, y1 - padding,
                    (x2 - x1) + 2 * padding, (y2 - y1) + 2 * padding,
                    select_pen, QBrush(Qt.BrushStyle.NoBrush),
                    z=2, tags=["SELECTOR"]
                )
            return [select_rect]

    # Control point and construction drawing methods

    def object_draw_controls(self, obj: CADObject, color: str = "blue"):
        """Draw control points and construction lines for an object"""
        if obj.object_type.value == "group":
            children = obj.attributes.get('children', [])
            for child in children:
                self.object_draw_controls(child, color)
            return

        # Delete existing control graphics
        self._delete_control_graphics(obj)

        # Draw object-specific controls
        self._draw_object_controls(obj, color)

    def _delete_control_graphics(self, obj: CADObject):
        """Remove existing control graphics for an object"""
        # Remove control points and control lines for this object
        cp_items = self.get_items_by_tag("CP")
        cl_items = self.get_items_by_tag("CL")

        items_to_remove = []

        # Check control points
        for item in cp_items:
            if item.data(0) == obj.object_id:  # Check object ID stored in item
                items_to_remove.append(item)

        # Check control lines
        for item in cl_items:
            if item.data(0) == obj.object_id:  # Check object ID stored in item
                items_to_remove.append(item)

        # Remove items from scene and clean up tags
        for item in items_to_remove:
            # Remove all tags from this item
            for tag in self.get_item_tags(item):
                self.remove_item_tag(item, tag)
            # Remove from scene
            if self.cad_scene:
                self.cad_scene.removeItem(item)

    def _draw_object_controls(self, obj: CADObject, color: str):
        """Draw object-specific control points and lines"""
        control_points = obj.get_control_points()

        for i, point in enumerate(control_points):
            self.object_draw_controlpoint(
                obj, obj.object_type.value, point.x, point.y, i,
                NodeType.OVAL, color, "white"
            )

    def object_draw_controlpoint(self, obj: CADObject, obj_type: str,
                                 x: float, y: float, cp_num: int,
                                 cp_type: NodeType, outline_color: str,
                                 fill_color: str,
                                 tags: Optional[List[str]] = None):
        """Draw a control point marker"""
        if tags is None:
            tags = []

        # Draw control point marker based on type
        size = 6
        pen = QPen(Colors.parse(outline_color))
        brush = QBrush(Colors.parse(fill_color))

        tags += ["CP", f"Node_{cp_num}"]
        if cp_type == NodeType.OVAL:
            if self.cad_scene:
                cp_item = self.cad_scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen=pen, brush=brush,
                    z=3, tags=tags, data=obj.object_id
                )
            else:
                cp_item = None
        elif cp_type == NodeType.RECTANGLE:
            if self.cad_scene:
                cp_item = self.cad_scene.addRect(
                    x - size/2, y - size/2, size, size, pen=pen, brush=brush,
                    z=3, tags=tags, data=obj.object_id
                )
            else:
                cp_item = None
        elif cp_type == NodeType.DIAMOND:
            # Create diamond shape
            points = [
                QPointF(x, y - size/2),  # Top
                QPointF(x + size/2, y),  # Right
                QPointF(x, y + size/2),  # Bottom
                QPointF(x - size/2, y)   # Left
            ]
            polygon = QPolygonF(points)
            if self.cad_scene:
                cp_item = self.cad_scene.addPolygon(
                    polygon, pen=pen, brush=brush,
                    z=3, tags=tags, data=obj.object_id)
            else:
                cp_item = None
        else:
            # Default to oval
            if self.cad_scene:
                cp_item = self.cad_scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen=pen, brush=brush,
                    z=3, tags=tags, data=obj.object_id
                )
            else:
                cp_item = None
        return cp_item

    def object_draw_control_line(self, obj: CADObject, x0: float, y0: float,
                                 x1: float, y1: float, cp_num: int,
                                 color: str, dash: str = "",
                                 tags: Optional[List[str]] = None):
        """Draw a control/construction line"""
        if tags is None:
            tags = []
        tags += ["CL", f"Node_{cp_num}"]

        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        if dash:
            pen.setDashPattern(self.get_dash_pattern(dash))

        line_item = None
        if self.cad_scene:
            line_item = self.cad_scene.addLine(
                x0, y0, x1, y1, pen, z=0.5, tags=tags, data=obj.object_id)
        return line_item

    def object_draw_circle(self, cx: float, cy: float, radius: float,
                           tags: List[str], color: str, dash: str = "",
                           width: float = 0.001):
        """Draw a construction circle"""
        self.object_draw_oval(cx, cy, radius, radius, tags, color,
                              dash, width)

    def object_draw_oval(self, cx: float, cy: float, rad1: float,
                         rad2: float, tags: List[str], color: str,
                         dash: str = "", width: float = 0.001):
        """Draw a construction oval/ellipse"""
        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        if dash:
            pen.setDashPattern(self.get_dash_pattern(dash))

        ellipse_item = None
        if self.cad_scene:
            ellipse_item = self.cad_scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2,
                pen=pen, brush=QBrush(Qt.BrushStyle.NoBrush),
                z=0.5, tags=["CL"] + tags
            )
        return ellipse_item

    def object_draw_center_cross(self, cx: float, cy: float, radius: float,
                                 tags: List[str], color: str,
                                 width: float = 0.001):
        """Draw center cross marker"""
        self.object_draw_oval_cross(cx, cy, radius, radius, tags, color, width)

    def object_draw_oval_cross(self, cx: float, cy: float,
                               rad1: float, rad2: float, tags: List[str],
                               color: str, width: float = 0.001):
        """Draw oval center cross marker"""
        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        # Draw cross lines from center, so dashes are centered
        lines = [
            (cx, cy, cx - rad1, cy),  # Left
            (cx, cy, cx + rad1, cy),  # Right
            (cx, cy, cx, cy - rad2),  # Up
            (cx, cy, cx, cy + rad2)   # Down
        ]

        line_items = []
        for x0, y0, x1, y1 in lines:
            if self.cad_scene:
                cross_tags = ["CL", "CROSS"] + tags
                line_item = self.cad_scene.addLine(x0, y0, x1, y1, pen, z=0.5,
                                                   tags=cross_tags)
                line_items.append(line_item)
        return line_items

    def object_draw_centerline(self, x0: float, y0: float, x1: float,
                               y1: float, tags: List[str], color: str):
        """Draw a centerline"""
        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        if self.cad_scene:
            center_tags = ["CL", "CENTERLINE"] + tags
            line_item = self.cad_scene.addLine(x0, y0, x1, y1, pen, z=0.5,
                                               tags=center_tags)
        else:
            return None  # Cannot draw without scene
        return line_item

    def object_draw_center_arc(self, cx: float, cy: float, radius: float,
                               start_deg: float, extent_deg: float,
                               tags: List[str], color: str):
        """Draw a center arc construction line"""
        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        # Create arc path
        path = QPainterPath()

        # Create arc
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        path.arcMoveTo(rect, start_deg)
        path.arcTo(rect, start_deg, extent_deg)

        path_item = None
        if self.cad_scene:
            path_item = self.cad_scene.addPath(
                path, pen, QBrush(Qt.BrushStyle.NoBrush),
                z=0.5, tags=["CL", "CENTER_ARC"] + tags
            )
        return path_item

    def object_draw_control_arc(self, obj: CADObject, cx: float, cy: float,
                                radius: float, start_deg: float,
                                extent_deg: float, cp_num: int, color: str,
                                dash: str = "",
                                tags: Optional[List[str]] = None):
        """Draw a control arc - translates
        cadobjects_object_draw_control_arc"""
        if tags is None:
            tags = []

        pen = QPen(Colors.parse(color),
                   self.get_construction_line_width())
        if dash:
            pen.setDashPattern(self.get_dash_pattern(dash))

        # Create arc path
        path = QPainterPath()

        # Create arc
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        path.arcMoveTo(rect, start_deg)
        path.arcTo(rect, start_deg, extent_deg)

        if self.cad_scene:
            path_item = self.cad_scene.addPath(
                path, pen, QBrush(Qt.BrushStyle.NoBrush),
                z=1.5, tags=["CL", f"Node_{cp_num}"] + tags,
                data=obj.object_id
            )
        else:
            return None  # Cannot draw without scene
        return path_item

    def redraw(self):
        """Complete redraw of all objects - translates cadobjects_redraw"""
        # Clear scene
        if self.cad_scene:
            self.cad_scene.scene.clear()

        # Redraw grid - now handled by CadScene
        if self.cad_scene:
            self.cad_scene.redraw_grid()

        # TODO: Redraw all objects from document
        # This would iterate through all objects in layers and draw them

        # Redraw construction points
        self.object_redraw_construction_points()

    def redraw_grid(self):
        """Redraw grid - delegates to CadScene"""
        if self.cad_scene:
            self.cad_scene.redraw_grid()
        else:
            # Fallback: Handle case where no CadScene is available
            # This allows legacy tests to work
            print("Warning: No CadScene available, grid drawing skipped")

    # Construction point management

    def object_draw_construction_point(self, x: float, y: float):
        """Add and draw a construction point"""
        self.construction_points.append(Point(x, y))
        self.object_redraw_construction_points()

    def object_redraw_construction_points(self):
        """Redraw all construction points"""
        # Clear existing construction points
        self.remove_items_by_tag(DrawingTags.CONSTRUCTION_PT.value)

        for point in self.construction_points:
            size = 4
            pen = QPen(QColor(255, 0, 0))  # Red
            brush = QBrush(QColor(255, 0, 0))

            if self.cad_scene:
                self.cad_scene.addEllipse(
                    point.x - size/2, point.y - size/2, size, size, pen, brush,
                    z=2, tags=[DrawingTags.CONSTRUCTION_PT.value]
                )
