"""
This module translates all the cadobjects_object_draw_* procedures from TCL
to Python, providing comprehensive object drawing functionality for the
pyTkCAD application.

The DrawingManager class serves as the main interface for all drawing
operations, maintaining compatibility with the original TCL implementation
while leveraging Qt's powerful graphics system.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Union

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPen, QBrush, QColor, QPainterPath, QPolygonF, QPixmap, QFont,
    QTransform
)
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point

# Import RulerWidget for grid info access
from BelfryCAD.gui.rulers import RulerWidget


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


@dataclass
class DrawingContext:
    """Drawing context containing scene, DPI, scale factors, etc."""
    scene: QGraphicsScene
    dpi: float = 72.0
    scale_factor: float = 1.0
    show_grid: bool = True
    show_origin: bool = True
    grid_color: QColor = field(default_factory=lambda: QColor(0, 255, 255))
    origin_color_x: QColor = field(default_factory=lambda: QColor(255, 0, 0))
    origin_color_y: QColor = field(default_factory=lambda: QColor(0, 255, 0))


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

    def __init__(self, context: DrawingContext):
        self.context = context
        self.construction_points: List[Point] = []
        self.node_images: Dict[NodeType, str] = {}
        self._init_node_images()

        # Reference to CadScene for tagged item creation
        self.cad_scene = None

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
            return self.cad_scene.getItemsByTag(tag)
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
        items = list(self.get_items_by_tag(tag))  # Make a copy to avoid modification during iteration
        for item in items:
            # Remove all tags from this item
            for tag_to_remove in list(self.get_item_tags(item)):  # Also copy this list
                self.remove_item_tag(item, tag_to_remove)
            # Remove from scene
            self.context.scene.removeItem(item)

    def clearAllTags(self):
        """Clear all tagging data"""
        if self.cad_scene:
            self.cad_scene.clearAllTags()
        else:
            # Fallback for cases where cad_scene is not set
            pass

    def _init_node_images(self):
        """Initialize node type images (placeholder for actual images)"""
        # TODO: Load actual node images
        self.node_images = {
            NodeType.OVAL: "oval",
            NodeType.DIAMOND: "diamond",
            NodeType.RECTANGLE: "rectangle",
            NodeType.ENDNODE: "endnode"
        }

    def get_dpi(self) -> float:
        """Get DPI setting"""
        return self.context.dpi

    def get_scale_factor(self) -> float:
        """Get current scale factor"""
        return self.context.scale_factor

    def scale_coords(self, coords: List[float]) -> List[float]:
        """Scale coordinates based on DPI and scale factor with Y-axis flip
        for CAD convention"""
        dpi = self.context.dpi
        scale_factor = self.context.scale_factor

        # Convert CAD coordinates to canvas coordinates
        # X: normal scaling, Y: negative scaling to flip from CAD convention
        # (Y up) to Qt convention (Y down)
        scaled_coords = []
        for i in range(0, len(coords), 2):
            x = coords[i] * dpi * scale_factor
            # Negative Y for coordinate system flip
            y = -coords[i + 1] * dpi * scale_factor
            scaled_coords.extend([x, y])

        return scaled_coords

    def descale_coords(self, coords: List[float]) -> List[float]:
        """Convert canvas coordinates back to CAD coordinates with
        Y-axis flip"""
        dpi = self.context.dpi
        scale_factor = self.context.scale_factor

        # Convert canvas coordinates to CAD coordinates
        # X: normal descaling, Y: negative descaling to flip from
        # Qt convention (Y down) to CAD convention (Y up)
        descaled_coords = []
        for i in range(0, len(coords), 2):
            x = coords[i] / (dpi * scale_factor)
            # Negative Y for coordinate system flip
            y = coords[i + 1] / (-dpi * scale_factor)
            descaled_coords.extend([x, y])

        return descaled_coords

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
        scaled_width = width * self.context.scale_factor

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

        scaled_width = (base_width * self.context.dpi / 72.0 *
                        self.context.scale_factor)

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

        return self._parse_color(color_name)

    def _parse_color(self, color_name: str) -> QColor:
        """Parse color name to QColor"""
        if color_name == "black":
            return QColor(0, 0, 0)
        elif color_name == "white":
            return QColor(255, 255, 255)
        elif color_name == "red":
            return QColor(255, 0, 0)
        elif color_name == "green":
            return QColor(0, 255, 0)
        elif color_name == "blue":
            return QColor(0, 0, 255)
        elif color_name == "yellow":
            return QColor(255, 255, 0)
        elif color_name == "cyan":
            return QColor(0, 255, 255)
        elif color_name == "magenta":
            return QColor(255, 0, 255)
        elif color_name == "gray" or color_name == "grey":
            return QColor(128, 128, 128)
        else:
            try:
                return QColor(color_name)
            except Exception:
                return QColor(0, 0, 0)  # Default to black

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
            fill = QBrush(self._parse_color(fill_color))
        else:
            fill = QBrush(Qt.BrushStyle.NoBrush)

        width = self.get_stroke_width(obj)
        dash_pattern = self.get_dash_pattern(
            obj.attributes.get('linedash', ''))

        # Create pen
        color_obj = (self._parse_color(color) if isinstance(color, str)
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
        # This would call object-specific drawing methods
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
        scaled_coords = self.scale_coords([cx, cy, rad1, 0, rad2, 0])
        cx, cy, rad1, _, rad2, _ = scaled_coords

        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2, pen, fill
            )
        else:
            ellipse = self.context.scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2, pen, fill
            )
        ellipse.setZValue(1)
        self._set_item_tags(ellipse, obj, [DrawingTags.ALL_DRAWN,
                                           DrawingTags.ACTUAL])
        return ellipse

    def _draw_circle(self, data: List[float], pen: QPen, fill: QBrush,
                     obj: CADObject):
        """Draw circle primitive"""
        cx, cy, radius = data
        scaled_coords = self.scale_coords([cx, cy, radius, 0])
        cx, cy, radius, _ = scaled_coords

        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2, pen, fill
            )
        else:
            ellipse = self.context.scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2, pen, fill
            )
        ellipse.setZValue(1)
        self._set_item_tags(ellipse, obj, [DrawingTags.ALL_DRAWN,
                                           DrawingTags.ACTUAL])
        return ellipse

    def _draw_rectangle(self, data: List[float], pen: QPen, fill: QBrush,
                        obj: CADObject):
        """Draw rectangle primitive"""
        x0, y0, x1, y1 = self.scale_coords(data)

        if self.cad_scene:
            rect = self.cad_scene.addRect(
                x0, y0, x1 - x0, y1 - y0, pen, fill)
        else:
            rect = self.context.scene.addRect(
                x0, y0, x1 - x0, y1 - y0, pen, fill)
        rect.setZValue(1)
        self._set_item_tags(rect, obj, [DrawingTags.ALL_DRAWN,
                                        DrawingTags.ACTUAL])
        return rect

    def _draw_arc(self, data: List[float], pen: QPen, fill: QBrush,
                  obj: CADObject):
        """Draw arc primitive"""
        cx, cy, radius, start_deg, extent_deg = data
        scaled_coords = self.scale_coords([cx, cy, radius, 0])
        cx, cy, radius, _ = scaled_coords

        # Convert to Qt's angle system (16ths of a degree)
        start_angle_16 = int(start_deg * 16)
        span_angle_16 = int(extent_deg * 16)
        if self.cad_scene:
            ellipse = self.cad_scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2, pen,
                QBrush(Qt.BrushStyle.NoBrush)
            )
        else:
            ellipse = self.context.scene.addEllipse(
                cx - radius, cy - radius, radius * 2, radius * 2, pen,
                QBrush(Qt.BrushStyle.NoBrush)
            )
        ellipse.setStartAngle(start_angle_16)
        ellipse.setSpanAngle(span_angle_16)
        ellipse.setZValue(1)
        self._set_item_tags(ellipse, obj, [DrawingTags.ALL_DRAWN,
                                           DrawingTags.ACTUAL])
        return ellipse

    def _draw_bezier(self, data: List[float], pen: QPen, fill: QBrush,
                     obj: CADObject):
        """Draw bezier curve primitive"""
        if len(data) < 8:
            return

        scaled_coords = self.scale_coords(data)

        # Create QPainterPath for bezier curve
        path = QPainterPath()
        x0, y0 = scaled_coords[0], scaled_coords[1]
        path.moveTo(x0, y0)

        # Process control points in groups of 6 (3 points = x1,y1,x2,y2,x3,y3)
        for i in range(2, len(scaled_coords), 6):
            if i + 5 < len(scaled_coords):
                x1, y1, x2, y2, x3, y3 = scaled_coords[i:i + 6]
                path.cubicTo(x1, y1, x2, y2, x3, y3)

        if self.cad_scene:
            path_item = self.cad_scene.addPath(path, pen, fill)
        else:
            path_item = self.context.scene.addPath(path, pen, fill)
        path_item.setZValue(1)
        self._set_item_tags(path_item, obj, [DrawingTags.ALL_DRAWN,
                                             DrawingTags.ACTUAL,
                                             DrawingTags.BEZIER])
        return path_item

    def _draw_lines(self, data: List[float], pen: QPen, fill: QBrush,
                    obj: CADObject):
        """Draw lines/polyline primitive"""
        if len(data) < 4:
            return

        scaled_coords = self.scale_coords(data)

        # Check if path is closed
        is_closed = (len(scaled_coords) >= 4 and
                     abs(scaled_coords[0] - scaled_coords[-2]) < 1e-6 and
                     abs(scaled_coords[1] - scaled_coords[-1]) < 1e-6)

        if is_closed and fill.style() != Qt.BrushStyle.NoBrush:
            # Draw as polygon
            points = []
            for i in range(0, len(scaled_coords), 2):
                points.append(QPointF(scaled_coords[i], scaled_coords[i + 1]))

            polygon = QPolygonF(points)
            if self.cad_scene:
                poly_item = self.cad_scene.addPolygon(polygon, pen, fill)
            else:
                poly_item = self.context.scene.addPolygon(polygon, pen, fill)
            poly_item.setZValue(1)
            self._set_item_tags(poly_item, obj, [DrawingTags.ALL_DRAWN,
                                                 DrawingTags.ACTUAL,
                                                 DrawingTags.FILLED])
            return [poly_item]
        else:
            # Draw as polyline
            path = QPainterPath()
            path.moveTo(scaled_coords[0], scaled_coords[1])

            for i in range(2, len(scaled_coords), 2):
                path.lineTo(scaled_coords[i], scaled_coords[i + 1])

            if self.cad_scene:
                path_item = self.cad_scene.addPath(
                    path, pen, QBrush(Qt.BrushStyle.NoBrush))
            else:
                path_item = self.context.scene.addPath(
                    path, pen, QBrush(Qt.BrushStyle.NoBrush))
            path_item.setZValue(1)
            self._set_item_tags(path_item, obj, [DrawingTags.ALL_DRAWN,
                                                 DrawingTags.ACTUAL])
            return [path_item]

    def _draw_text(self, data: List, pen: QPen, fill: QBrush, obj: CADObject):
        """Draw text primitive"""
        cx, cy, text, font_spec, justification = data
        scaled_coords = self.scale_coords([cx, cy])
        cx, cy = scaled_coords

        # Create font
        font_family, font_size = font_spec
        scaled_font_size = int(font_size * self.context.scale_factor *
                               2.153 + 0.5)
        if scaled_font_size < 1:
            scaled_font_size = 1

        font = QFont(font_family, scaled_font_size)

        # Create text item
        if self.cad_scene:
            text_item = self.cad_scene.addText(text, font)
        else:
            text_item = self.context.scene.addText(text, font)
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

        text_item.setZValue(1)
        self._set_item_tags(text_item, obj, [DrawingTags.ALL_DRAWN,
                                             DrawingTags.ACTUAL,
                                             DrawingTags.TEXT])
        return text_item

    def _draw_rottext(self, data: List, pen: QPen, fill: QBrush,
                      obj: CADObject):
        """Draw rotated text primitive"""
        cx, cy, text, font_spec, justification, rotation = data
        scaled_coords = self.scale_coords([cx, cy])
        cx, cy = scaled_coords

        # Create font
        font_family, font_size = font_spec
        scaled_font_size = int(font_size * self.context.scale_factor *
                               2.153 + 0.5)
        if scaled_font_size < 1:
            scaled_font_size = 1

        font = QFont(font_family, scaled_font_size)

        # Create text item
        if self.cad_scene:
            text_item = self.cad_scene.addText(text, font)
        else:
            text_item = self.context.scene.addText(text, font)
        text_item.setDefaultTextColor(pen.color())

        # Apply rotation
        transform = QTransform()
        transform.rotate(-rotation)  # Qt uses negative angles
        text_item.setTransform(transform)

        # Set position
        text_item.setPos(cx, cy)
        text_item.setZValue(1)
        self._set_item_tags(text_item, obj, [DrawingTags.ALL_DRAWN,
                                             DrawingTags.ACTUAL,
                                             DrawingTags.PTEXT])
        return text_item

    def _draw_image(self, data: List, pen: QPen, fill: QBrush, obj: CADObject):
        """Draw image primitive"""
        cx, cy, width, height, rotation, pixmap = data
        scaled_coords = self.scale_coords([cx, cy, width, height])
        cx, cy, width, height = scaled_coords

        # Create pixmap item
        if isinstance(pixmap, QPixmap):
            if self.cad_scene:
                image_item = self.cad_scene.addPixmap(pixmap)
            else:
                image_item = self.context.scene.addPixmap(pixmap)

            # Scale and position
            image_item.setScale(width / pixmap.width())
            image_item.setPos(cx - width / 2, cy - height / 2)

            # Apply rotation if needed
            if abs(rotation) > 0.01:
                transform = QTransform()
                transform.rotate(-rotation)
                image_item.setTransform(transform)

            image_item.setZValue(0)  # Behind other objects
            self._set_item_tags(image_item, obj, [DrawingTags.ALL_DRAWN,
                                                  DrawingTags.ACTUAL,
                                                  DrawingTags.PIMAGE])
            return image_item

    def _set_item_tags(self, item: QGraphicsItem,
                       obj: Union[CADObject, ConstructionCADObject],
                       tags: List):
        """Set tags on graphics item for organization"""
        # Convert DrawingTags enum to strings if needed
        string_tags = []
        for tag in tags:
            if isinstance(tag, DrawingTags):
                string_tags.append(tag.value)
            else:
                string_tags.append(str(tag))

        # Store tags in item data for later retrieval and management
        if item:
            # Store object ID for tracking
            item.setData(0, obj.object_id)
            # Store tags as a list
            item.setData(1, string_tags)
            # Store object type
            item.setData(2, obj.object_type.value)

            # Update tagging system mappings
            for tag in string_tags:
                self.add_item_tag(item, tag)

    def _draw_selection(self, obj: CADObject):
        """Draw selection highlight around object"""
        bounds = obj.get_bounds()
        if bounds:
            x1, y1, x2, y2 = bounds
            scaled_bounds = self.scale_coords([x1, y1, x2, y2])
            x1, y1, x2, y2 = scaled_bounds

            padding = 3
            select_pen = QPen(QColor(255, 255, 0), 1)  # Yellow selection
            select_pen.setDashPattern([3, 3])  # Dashed line

            if self.cad_scene:
                select_rect = self.cad_scene.addRect(
                    x1 - padding, y1 - padding,
                    (x2 - x1) + 2 * padding, (y2 - y1) + 2 * padding,
                    select_pen, QBrush(Qt.BrushStyle.NoBrush)
                )
            else:
                select_rect = self.context.scene.addRect(
                    x1 - padding, y1 - padding,
                    (x2 - x1) + 2 * padding, (y2 - y1) + 2 * padding,
                    select_pen, QBrush(Qt.BrushStyle.NoBrush)
                )
            select_rect.setZValue(2)  # Above the object
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
            self.context.scene.removeItem(item)

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

        scaled_coords = self.scale_coords([x, y])
        x, y = scaled_coords

        # Draw control point marker based on type
        size = 6
        pen = QPen(self._parse_color(outline_color))
        brush = QBrush(self._parse_color(fill_color))

        if cp_type == NodeType.OVAL:
            if self.cad_scene:
                cp_item = self.cad_scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )
            else:
                cp_item = self.context.scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )
        elif cp_type == NodeType.RECTANGLE:
            if self.cad_scene:
                cp_item = self.cad_scene.addRect(
                    x - size/2, y - size/2, size, size, pen, brush
                )
            else:
                cp_item = self.context.scene.addRect(
                    x - size/2, y - size/2, size, size, pen, brush
                )
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
                cp_item = self.cad_scene.addPolygon(polygon, pen, brush)
            else:
                cp_item = self.context.scene.addPolygon(polygon, pen, brush)
        else:
            # Default to oval
            if self.cad_scene:
                cp_item = self.cad_scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )
            else:
                cp_item = self.context.scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )

        cp_item.setZValue(3)  # Above everything else

        # Set tags for tracking and management
        self._set_item_tags(cp_item, obj, ["CP", f"Node_{cp_num}"])

        return cp_item

    def object_draw_control_line(self, obj: CADObject, x0: float, y0: float,
                                 x1: float, y1: float, cp_num: int,
                                 color: str, dash: str = "",
                                 tags: Optional[List[str]] = None):
        """Draw a control/construction line"""
        if tags is None:
            tags = []

        scaled_coords = self.scale_coords([x0, y0, x1, y1])
        x0, y0, x1, y1 = scaled_coords

        pen = QPen(self._parse_color(color),
                   self.get_construction_line_width())
        if dash:
            pen.setDashPattern(self.get_dash_pattern(dash))

        if self.cad_scene:
            line_item = self.cad_scene.addLine(x0, y0, x1, y1, pen)
        else:
            line_item = self.context.scene.addLine(x0, y0, x1, y1, pen)
        line_item.setZValue(0.5)  # Below objects but above background

        # Set tags for tracking and management
        self._set_item_tags(line_item, obj, ["CL", f"Node_{cp_num}"] + tags)

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
        scaled_coords = self.scale_coords([cx, cy, rad1, rad2])
        cx, cy, rad1, rad2 = scaled_coords

        pen = QPen(self._parse_color(color),
                   self.get_construction_line_width())
        if dash:
            pen.setDashPattern(self.get_dash_pattern(dash))

        if self.cad_scene:
            ellipse_item = self.cad_scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2,
                pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        else:
            ellipse_item = self.context.scene.addEllipse(
                cx - rad1, cy - rad2, rad1 * 2, rad2 * 2,
                pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        ellipse_item.setZValue(0.5)
        # Set tags for tracking and management
        # Create a construction object for tagging
        dummy_obj = ConstructionCADObject(
            f"oval_{id(ellipse_item)}", ObjectType.LINE
        )
        self._set_item_tags(ellipse_item, dummy_obj, ["CL"] + tags)

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
        scaled_coords = self.scale_coords([cx, cy, rad1, rad2])
        cx, cy, rad1, rad2 = scaled_coords

        pen = QPen(self._parse_color(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        # Draw cross lines from center
        lines = [
            (cx, cy, cx - rad1, cy),  # Left
            (cx, cy, cx + rad1, cy),  # Right
            (cx, cy, cx, cy - rad2),  # Up
            (cx, cy, cx, cy + rad2)   # Down
        ]

        line_items = []
        for x0, y0, x1, y1 in lines:
            if self.cad_scene:
                line_item = self.cad_scene.addLine(x0, y0, x1, y1, pen)
            else:
                line_item = self.context.scene.addLine(x0, y0, x1, y1, pen)
            line_item.setZValue(0.5)

            # Set tags for tracking and management
            dummy_obj = ConstructionCADObject(
                f"cross_{id(line_item)}", ObjectType.LINE
            )
            self._set_item_tags(line_item, dummy_obj, ["CL", "CROSS"] + tags)
            line_items.append(line_item)

        return line_items

    def object_draw_centerline(self, x0: float, y0: float, x1: float,
                               y1: float, tags: List[str], color: str):
        """Draw a centerline"""
        scaled_coords = self.scale_coords([x0, y0, x1, y1])
        x0, y0, x1, y1 = scaled_coords

        pen = QPen(self._parse_color(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        if self.cad_scene:
            line_item = self.cad_scene.addLine(x0, y0, x1, y1, pen)
        else:
            line_item = self.context.scene.addLine(x0, y0, x1, y1, pen)
        line_item.setZValue(0.5)

        # Set tags for tracking and management
        dummy_obj = ConstructionCADObject(
            f"centerline_{id(line_item)}", ObjectType.LINE
        )
        self._set_item_tags(line_item, dummy_obj, ["CL", "CENTERLINE"] + tags)

        return line_item

    def object_draw_center_arc(self, cx: float, cy: float, radius: float,
                               start_deg: float, extent_deg: float,
                               tags: List[str], color: str):
        """Draw a center arc construction line"""
        scaled_coords = self.scale_coords([cx, cy, radius, 0])
        cx, cy, radius, _ = scaled_coords

        pen = QPen(self._parse_color(color),
                   self.get_construction_line_width())
        pen.setDashPattern(self.get_dash_pattern("centerline"))

        # Create arc path
        path = QPainterPath()

        # Create arc
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        path.arcMoveTo(rect, start_deg)
        path.arcTo(rect, start_deg, extent_deg)

        if self.cad_scene:
            path_item = self.cad_scene.addPath(
                path, pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        else:
            path_item = self.context.scene.addPath(
                path, pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        path_item.setZValue(0.5)

        # Set tags for tracking and management
        dummy_obj = ConstructionCADObject(
            f"center_arc_{id(path_item)}", ObjectType.ARC
        )
        self._set_item_tags(path_item, dummy_obj, ["CL", "CENTER_ARC"] + tags)

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

        scaled_coords = self.scale_coords([cx, cy, radius, 0])
        cx, cy, radius, _ = scaled_coords

        pen = QPen(self._parse_color(color),
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
                path, pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        else:
            path_item = self.context.scene.addPath(
                path, pen, QBrush(Qt.BrushStyle.NoBrush)
            )
        # Above control lines but below control points
        path_item.setZValue(1.5)

        # Set tags for tracking and management
        self._set_item_tags(path_item, obj, ["CL", f"Node_{cp_num}"] + tags)

        return path_item

    # Grid helper methods (from TCL cadobjects_grid_info and color functions)

    def _get_grid_info(self):
        """Calculate grid spacing info - calls ruler's method"""
        # Create temporary RulerWidget to get grid info (no duplication)
        # This ensures we always use the same values as the ruler system
        from PySide6.QtWidgets import QGraphicsView
        temp_view = QGraphicsView(self.context.scene)
        temp_ruler = RulerWidget(temp_view, "horizontal")
        
        # Connect the ruler to this drawing context for real DPI/scale values
        temp_ruler.set_drawing_context(self.context)
        
        return temp_ruler.get_grid_info()

    def _color_to_hsv(self, color):
        """Convert QColor to HSV values (0-360, 0-1, 0-1)"""
        if isinstance(color, str):
            color = QColor(color)
        elif isinstance(color, QColor):
            pass
        else:
            color = QColor(0, 255, 255)  # Default cyan

        # Get HSV values from QColor
        h = color.hueF()
        s = color.saturationF()
        v = color.valueF()
        return (h * 360.0 if h >= 0 else 0.0, s, v)

    def _color_from_hsv(self, hue, saturation, value):
        """Create QColor from HSV values"""
        color = QColor()
        color.setHsvF(hue / 360.0, saturation, value)
        return color

    def _draw_grid_origin(self, dpi, linewidth):
        """Draw origin lines - translates part of cadobjects_redraw_grid"""
        # Get scene bounds
        scene_rect = self.context.scene.sceneRect()
        x0, y0 = scene_rect.left(), scene_rect.top()
        x1, y1 = scene_rect.right(), scene_rect.bottom()

        # Origin colors (default if not configured)
        x_color = "#FF0000"  # Red
        y_color = "#00FF00"  # Green

        # Draw X-axis origin line (horizontal)
        y_scene = 0  # Origin Y in CAD coordinates becomes 0 in scene
        if y0 <= y_scene <= y1:  # Origin is visible
            pen = QPen(QColor(x_color))
            pen.setWidthF(linewidth)
            if self.cad_scene:
                line_item = self.cad_scene.addLine(
                    x0, y_scene, x1, y_scene, pen)
            else:
                line_item = self.context.scene.addLine(
                    x0, y_scene, x1, y_scene, pen)
            line_item.setZValue(-5)  # Behind everything

            dummy_obj = ConstructionCADObject(
                f"origin_x_{id(line_item)}", ObjectType.LINE)
            self._set_item_tags(
                line_item, dummy_obj, [DrawingTags.GRID_ORIGIN])

        # Draw Y-axis origin line (vertical)
        x_scene = 0  # Origin X in CAD coordinates becomes 0 in scene
        if x0 <= x_scene <= x1:  # Origin is visible
            pen = QPen(QColor(y_color))
            pen.setWidthF(linewidth)
            if self.cad_scene:
                line_item = self.cad_scene.addLine(
                    x_scene, y0, x_scene, y1, pen)
            else:
                line_item = self.context.scene.addLine(
                    x_scene, y0, x_scene, y1, pen)
            line_item.setZValue(-5)  # Behind everything

            dummy_obj = ConstructionCADObject(
                f"origin_y_{id(line_item)}", ObjectType.LINE)
            self._set_item_tags(
                line_item, dummy_obj, [DrawingTags.GRID_ORIGIN])

    def _draw_grid_lines(
            self, xstart, xend, ystart, yend,
            minorspacing, majorspacing,
            superspacing, labelspacing, scalemult,
            gridcolor, unitcolor, supercolor,
            linewidth, srx0, srx1, sry0, sry1
    ):
        """Draw multi-level grid lines - main part of cadobjects_redraw_grid"""

        # Calculate grid line positions and draw them
        # Following the TCL logic closely

        def quantize(value, spacing):
            """Quantize value to nearest multiple of spacing"""
            return round(value / spacing) * spacing

        def approx(x, y, epsilon=1e-6):
            """Check if two floats are approximately equal"""
            return abs(x - y) < epsilon

        # Minor grid lines (most frequent)
        if minorspacing > 0:
            # Vertical minor lines
            x = quantize(xstart, minorspacing)
            while x <= xend:
                x_scene = x * scalemult
                if srx0 <= x_scene <= srx1:
                    tags = [DrawingTags.GRID.value]
                    if (superspacing > 0 and
                            approx(x, quantize(x, superspacing))):
                        pen = QPen(supercolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_UNIT_LINE.value)
                        z_val = -6
                    elif (majorspacing > 0 and
                          approx(x, quantize(x, majorspacing))):
                        pen = QPen(unitcolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_UNIT_LINE.value)
                        z_val = -7
                    else:
                        pen = QPen(gridcolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_LINE.value)
                        z_val = -8

                    if self.cad_scene:
                        line_item = self.cad_scene.addLine(
                            x_scene, sry0, x_scene, sry1, pen)
                    else:
                        line_item = self.context.scene.addLine(
                            x_scene, sry0, x_scene, sry1, pen)
                    line_item.setZValue(z_val)

                    dummy_obj = ConstructionCADObject(
                        f"grid_minor_v_{id(line_item)}", ObjectType.LINE)
                    self._set_item_tags(line_item, dummy_obj, tags)
                x += minorspacing

            # Horizontal minor lines
            y = quantize(ystart, minorspacing)
            while y <= yend:
                y_scene = -y * scalemult  # Y-axis flip
                if sry0 <= y_scene <= sry1:
                    tags = [DrawingTags.GRID.value]
                    if (superspacing > 0 and
                            approx(y, quantize(y, superspacing))):
                        pen = QPen(supercolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_UNIT_LINE.value)
                        z_val = -6
                    elif (majorspacing > 0 and
                            approx(y, quantize(y, majorspacing))):
                        pen = QPen(unitcolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_UNIT_LINE.value)
                        z_val = -7
                    else:
                        pen = QPen(gridcolor)
                        pen.setWidthF(linewidth * 1.0)
                        tags.append(DrawingTags.GRID_LINE.value)
                        z_val = -8

                    if self.cad_scene:
                        line_item = self.cad_scene.addLine(
                            srx0, y_scene, srx1, y_scene, pen)
                    else:
                        line_item = self.context.scene.addLine(
                            srx0, y_scene, srx1, y_scene, pen)
                    line_item.setZValue(z_val)

                    dummy_obj = ConstructionCADObject(
                        f"grid_minor_h_{id(line_item)}", ObjectType.LINE)
                    self._set_item_tags(line_item, dummy_obj, tags)
                y += minorspacing

    def redraw_grid(self, color: str = ""):
        """Redraw the grid - translates cadobjects_redraw_grid"""
        # Remove existing grid items (both tagged and old Z-value items)
        self.remove_items_by_tag(DrawingTags.GRID.value)

        # Also remove old grid items with Z-value -1001 (legacy system)
        items_to_remove = []
        for item in self.context.scene.items():
            if hasattr(item, 'zValue') and item.zValue() == -1001:
                items_to_remove.append(item)

        for item in items_to_remove:
            try:
                self.context.scene.removeItem(item)
            except RuntimeError:
                # Item may have already been removed
                pass

        # Get grid info like TCL implementation
        grid_info = self._get_grid_info()
        if not grid_info:
            return

        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info
        
        def _adjust_saturation(color, factor):
            """Adjust saturation of a color by a factor"""
            hue, sat, val = self._color_to_hsv(color)
            new_sat = min(max(sat * factor, 0.0), 1.0)
            return self._color_from_hsv(hue, new_sat, val)

        # Calculate colors like TCL implementation
        if color:
            unitcolor = self._parse_color(color)
        else:
            unitcolor = self._color_from_hsv(180.0, 0.5, 1.0)
        supercolor = _adjust_saturation(unitcolor, 2.0)
        gridcolor = _adjust_saturation(unitcolor, 0.4)

        dpi = self.context.dpi
        scalefactor = self.context.scale_factor
        lwidth = 0.5

        scalemult = dpi * scalefactor / conversion

        # Get visible scene rectangle
        scene_rect = self.context.scene.sceneRect()
        srx0, sry0 = scene_rect.left(), scene_rect.top()
        srx1, sry1 = scene_rect.right(), scene_rect.bottom()

        # Calculate CAD coordinate ranges (descale from scene coordinates)
        xstart = srx0 / scalemult
        xend = srx1 / scalemult
        ystart = sry1 / (-scalemult)  # Y-axis flip
        yend = sry0 / (-scalemult)    # Y-axis flip

        # Draw origin if enabled (simplified check)
        if self.context.show_origin:
            self._draw_grid_origin(dpi, lwidth)

        # Draw grid if enabled
        if self.context.show_grid:
            self._draw_grid_lines(
                xstart, xend, ystart, yend,
                minorspacing, majorspacing,
                superspacing, labelspacing, scalemult,
                gridcolor, unitcolor, supercolor,
                lwidth, srx0, srx1, sry0, sry1)

    def redraw(self, color: str = ""):
        """Complete redraw of all objects - translates cadobjects_redraw"""
        # Clear scene
        self.context.scene.clear()

        # Redraw grid
        self.redraw_grid(color)

        # TODO: Redraw all objects from document
        # This would iterate through all objects in layers and draw them

        # Redraw construction points
        self.object_redraw_construction_points()

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
            scaled_coords = self.scale_coords([point.x, point.y])
            x, y = scaled_coords

            size = 4
            pen = QPen(QColor(255, 0, 0))  # Red
            brush = QBrush(QColor(255, 0, 0))

            if self.cad_scene:
                cp_item = self.cad_scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )
            else:
                cp_item = self.context.scene.addEllipse(
                    x - size/2, y - size/2, size, size, pen, brush
                )
            cp_item.setZValue(2)

            # Set tags for tracking and management
            dummy_obj = ConstructionCADObject(
                f"construction_pt_{id(cp_item)}", ObjectType.POINT
            )
            self._set_item_tags(
                cp_item, dummy_obj, [DrawingTags.CONSTRUCTION_PT]
            )
