"""
EllipseCadItem - An ellipse CAD item defined by two focus points and a perimeter point.
"""

import math
from typing import List, Optional, TYPE_CHECKING
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker, Qt, QTransform
from typing import cast

from ..cad_item import CadItem
from ..control_points import ControlPoint, SquareControlPoint, DiamondControlPoint, ControlDatum
from ..cad_rect import CadRect
from ....widgets.cad_scene import CadScene
import logging

if TYPE_CHECKING:
    from ....main_window import MainWindow


class EllipseCadItem(CadItem):
    """An ellipse CAD item defined by two focus points and a perimeter point."""

    def __init__(
                self,
                main_window: 'MainWindow',
                focus1_point: QPointF = QPointF(-2, 0),
                focus2_point: QPointF = QPointF(2, 0),
                perimeter_point: QPointF = QPointF(2,1),
                color: QColor = QColor(0, 0, 0),
                line_width: Optional[float] = 0.05
    ):
        super().__init__(main_window, color, line_width)
        
        # Default to a horizontal ellipse if no points provided
        self._focus1_point = focus1_point if focus1_point else QPointF(-2, 0)
        self._focus2_point = focus2_point if focus2_point else QPointF(2, 0)
        self._perimeter_point = perimeter_point if perimeter_point else QPointF(3, 0)
        
        # Convert points to QPointF if they aren't already
        if isinstance(self._focus1_point, (list, tuple)):
            self._focus1_point = QPointF(
                self._focus1_point[0], self._focus1_point[1])
        if isinstance(self._focus2_point, (list, tuple)):
            self._focus2_point = QPointF(
                self._focus2_point[0], self._focus2_point[1])
        if isinstance(self._perimeter_point, (list, tuple)):
            self._perimeter_point = QPointF(
                self._perimeter_point[0], self._perimeter_point[1])
        
        self._focus1_cp = None
        self._focus2_cp = None
        self._perimeter_cp = None
        self._center_cp = None
        self._major_radius_datum = None
        self._minor_radius_datum = None
        self._rotation_datum = None
        
        # Position the ellipse at the center
        self.setPos(self.center_point)
        
        # Create control points
        self.createControls()

    @property
    def focus1_point(self) -> QPointF:
        """Get the first focus point in scene coordinates."""
        return self._focus1_point

    @property
    def focus2_point(self) -> QPointF:
        """Get the second focus point in scene coordinates."""
        return self._focus2_point

    @property
    def perimeter_point(self) -> QPointF:
        """Get the perimeter point in scene coordinates."""
        return self._perimeter_point

    @property
    def center_point(self) -> QPointF:
        """Get the center point in scene coordinates."""
        return (self._focus1_point + self._focus2_point) * 0.5

    @property
    def major_radius(self) -> float:
        """Get the major radius (semi-major axis)."""
        # The major radius is half the sum of distances from foci to perimeter
        dist1 = math.hypot(self._perimeter_point.x() - self._focus1_point.x(),
                          self._perimeter_point.y() - self._focus1_point.y())
        dist2 = math.hypot(self._perimeter_point.x() - self._focus2_point.x(),
                          self._perimeter_point.y() - self._focus2_point.y())
        return (dist1 + dist2) / 2

    @property
    def minor_radius(self) -> float:
        """Get the minor radius (semi-minor axis)."""
        # minor_radius = sqrt(major_radius² - focal_distance²)
        major_r = self.major_radius
        focal_distance = math.hypot(
            self._focus2_point.x() - self._focus1_point.x(),
            self._focus2_point.y() - self._focus1_point.y()
        ) * 0.5
        return math.sqrt(major_r * major_r - focal_distance * focal_distance)

    @property
    def rotation_angle(self) -> float:
        """Get the rotation angle in degrees."""
        # Calculate angle from center to focus2
        center = self.center_point
        angle = math.degrees(math.atan2(
            self._focus2_point.y() - center.y(),
            self._focus2_point.x() - center.x()
        ))
        return (angle + 360) % 360

    @property
    def eccentricity(self) -> float:
        """Get the eccentricity of the ellipse."""
        major_r = self.major_radius
        minor_r = self.minor_radius
        if major_r == 0:
            return 0.0
        return math.sqrt(1 - (minor_r * minor_r) / (major_r * major_r))

    def boundingRect(self):
        """Return the bounding rectangle of the ellipse."""
        # Get the ellipse parameters
        center = self.center_point
        major_r = self.major_radius
        minor_r = self.minor_radius
        rotation = math.radians(self.rotation_angle)
        
        # Calculate the bounding box of the rotated ellipse
        cos_rot = math.cos(rotation)
        sin_rot = math.sin(rotation)
        
        # Maximum extent in x and y directions
        max_x = abs(major_r * cos_rot) + abs(minor_r * sin_rot)
        max_y = abs(major_r * sin_rot) + abs(minor_r * cos_rot)
        
        # Create bounding rect centered at the ellipse center
        rect = CadRect(
            -max_x, -max_y, 
            2 * max_x, 2 * max_y
        )
        
        # Add padding for line width
        rect.expandByScalar(max(self.line_width / 2, 0.1))
        
        return rect

    def shape(self):
        """Return the shape for hit testing."""
        # Create a painter path for the ellipse
        path = QPainterPath()
        
        # Get ellipse parameters
        center = self.center_point
        major_r = self.major_radius
        minor_r = self.minor_radius
        rotation = self.rotation_angle
        
        # Create ellipse path
        ellipse_rect = QRectF(-major_r, -minor_r, 2 * major_r, 2 * minor_r)
        path.addEllipse(ellipse_rect)
        
        # Apply rotation and translation
        transform = QTransform()
        #transform.translate(center.x(), center.y())
        transform.rotate(rotation)
        path = transform.map(path)
        
        # Create stroker for line width
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.line_width, 0.1))  # Minimum width for selection
        return stroker.createStroke(path)

    def paint_item_with_color(self, painter, option, widget=None, color: Optional[QColor] = None):
        """Paint the ellipse with a specific color."""
        painter.save()
        line_color = color if color is not None else self.color

        # Set up pen and brush
        pen = QPen(line_color, self.line_width)
        if self._line_width is None:
            pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        # Get ellipse parameters
        center = self.center_point
        major_r = self.major_radius
        minor_r = self.minor_radius
        rotation = self.rotation_angle
        
        # Create ellipse path
        ellipse_rect = QRectF(-major_r, -minor_r, 2 * major_r, 2 * minor_r)
        path = QPainterPath()
        path.addEllipse(ellipse_rect)
        
        # Apply rotation and translation
        transform = QTransform()
        #transform.translate(center.x(), center.y())
        transform.rotate(rotation)
        path = transform.map(path)
        
        # Draw the ellipse
        painter.drawPath(path)
        
        painter.restore()

        if self._is_singly_selected():
            #self.draw_center_cross(painter, QPointF(0, 0))
            ang = self.rotation_angle
            self.draw_construction_line(
                painter,
                QPointF(0, 0),
                QPointF(
                    self.major_radius * math.cos(math.radians(ang+180)),
                    self.major_radius * math.sin(math.radians(ang+180)))
            )
            self.draw_construction_line(
                painter,
                QPointF(0, 0),
                QPointF(
                    self.minor_radius * math.cos(math.radians(ang - 90)),
                    self.minor_radius * math.sin(math.radians(ang - 90)))
            )
            self.draw_radius_arrow(painter, QPointF(0, 0), ang, self.major_radius, self.line_width)
            self.draw_radius_arrow(painter, QPointF(0, 0), ang + 90, self.minor_radius, self.line_width)


    def paint_item(self, painter, option, widget=None):
        """Paint the ellipse."""
        self.paint_item_with_color(painter, option, widget, self._color)

    def _create_controls_impl(self):
        """Create control points for the ellipse and return them."""
        # Get precision from scene
        precision = 3  # Default fallback
        scene = self.scene()
        if scene and isinstance(scene, CadScene):
            precision = scene.get_precision()
        
        # Create control points
        self._focus1_cp = ControlPoint(
            cad_item=self,
            setter=self._set_focus1_position
        )
        self._focus2_cp = ControlPoint(
            cad_item=self,
            setter=self._set_focus2_position
        )
        self._perimeter_cp = DiamondControlPoint(
            cad_item=self,
            setter=self._set_perimeter_position
        )
        self._center_cp = SquareControlPoint(
            cad_item=self,
            setter=self._set_center_position
        )
        
        # Create control datums
        self._major_radius_datum = ControlDatum(
            setter=self._set_major_radius,
            prefix="Rmaj: ",
            cad_item=self,
            label="Major Radius",
            angle=0,
            pixel_offset=10,
            min_value=self.minor_radius
        )
        self._minor_radius_datum = ControlDatum(
            setter=self._set_minor_radius,
            prefix="Rmin: ",
            cad_item=self,
            label="Minor Radius",
            angle=90,
            pixel_offset=10,
            max_value=self.major_radius
        )
        self._rotation_datum = ControlDatum(
            setter=self._set_rotation_angle,
            prefix="∠",
            suffix="°",
            cad_item=self,
            label="Rotation Angle",
            angle=90,
            pixel_offset=10,
            precision_override=1,
            is_length=False
        )
        
        self.updateControls()
        
        # Store control points in the list that the scene expects
        control_points = [
            self._focus1_cp, self._focus2_cp,
            self._perimeter_cp, self._center_cp,
            self._major_radius_datum, self._minor_radius_datum,
            self._rotation_datum
        ]
        self._control_point_items.extend(control_points)
        
        # Return the list of control points
        return control_points

    def updateControls(self):
        """Update control point positions and values."""
        if self._focus1_cp:
            self._focus1_cp.setPos(self._focus1_point)
        if self._focus2_cp:
            self._focus2_cp.setPos(self._focus2_point)
        if self._perimeter_cp:
            self._perimeter_cp.setPos(self._perimeter_point)
        if self._center_cp:
            self._center_cp.setPos(self.center_point)
        
        # Update control datums
        rotation = self.rotation_angle
        if self._major_radius_datum:
            major_r = self.major_radius
            center = self.center_point
            # Position datum at 0 degrees from rotation
            angle_rad = math.radians(rotation)
            pos = center + QPointF(
                major_r * math.cos(angle_rad),
                major_r * math.sin(angle_rad))
            self._major_radius_datum.update_datum(major_r, pos)
            self._major_radius_datum.angle = rotation
            # Update max value based on current minor radius
            if self._minor_radius_datum:
                self._major_radius_datum.min_value = self.minor_radius
            
        if self._minor_radius_datum:
            minor_r = self.minor_radius
            center = self.center_point
            rotation = self.rotation_angle
            # Position datum at 90 degrees from rotation
            angle_rad = math.radians(rotation + 90)
            pos = center + QPointF(minor_r * math.cos(angle_rad), minor_r * math.sin(angle_rad))
            self._minor_radius_datum.update_datum(minor_r, pos)
            self._minor_radius_datum.angle = rotation + 90
            # Update max value based on current major radius
            if self._major_radius_datum:
                self._minor_radius_datum.max_value = self.major_radius
        
        if self._rotation_datum:
            rotation = self.rotation_angle
            center = self.center_point
            pos = center
            self._rotation_datum.update_datum(rotation, pos)
            self._rotation_datum.angle = rotation - 90

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """Return list of control point positions in scene coordinates (excluding ControlDatums)."""
        out = []
        # Return scene coordinates for all control points
        if self._focus1_cp and (exclude_cps is None or self._focus1_cp not in exclude_cps):
            out.append(self._focus1_point)
        if self._focus2_cp and (exclude_cps is None or self._focus2_cp not in exclude_cps):
            out.append(self._focus2_point)
        if self._perimeter_cp and (exclude_cps is None or self._perimeter_cp not in exclude_cps):
            out.append(self._perimeter_point)
        if self._center_cp and (exclude_cps is None or self._center_cp not in exclude_cps):
            out.append(self.center_point)
        return out

    def _get_control_point_objects(self) -> List['ControlPoint']:
        """Get the list of ControlPoint objects for this CAD item."""
        return [x for x in [self._focus1_cp, self._focus2_cp, self._perimeter_cp, self._center_cp] if x]

    # Control point setters
    def _set_focus1_position(self, new_position: QPointF):
        """Set the first focus position and move focus2 to maintain symmetry."""
        center = self.center_point
        old_angle = self.rotation_angle
        focus1_vector = new_position - center
        self._focus1_point = new_position
        self._focus2_point = center - focus1_vector
        delta_angle = math.radians(self.rotation_angle - old_angle)
        pp_dist = math.hypot(
            self._perimeter_point.x() - center.x(),
            self._perimeter_point.y() - center.y())
        pp_angle = math.atan2(
            self._perimeter_point.y() - center.y(),
            self._perimeter_point.x() - center.x()) + delta_angle
        self._perimeter_point = center + QPointF(
            pp_dist * math.cos(pp_angle),
            pp_dist * math.sin(pp_angle))
        self.prepareGeometryChange()
        self.updateControls()
        self.update()

    def _set_focus2_position(self, new_position: QPointF):
        """Set the second focus position and move focus1 to maintain symmetry."""
        center = self.center_point
        old_angle = self.rotation_angle
        focus2_vector = new_position - center
        self._focus2_point = new_position
        self._focus1_point = center - focus2_vector
        delta_angle = math.radians(self.rotation_angle - old_angle)
        pp_dist = math.hypot(
            self._perimeter_point.x() - center.x(),
            self._perimeter_point.y() - center.y())
        pp_angle = math.atan2(  
            self._perimeter_point.y() - center.y(),
            self._perimeter_point.x() - center.x()) + delta_angle
        self._perimeter_point = center + QPointF(
            pp_dist * math.cos(pp_angle),
            pp_dist * math.sin(pp_angle))
        self.prepareGeometryChange()
        self.updateControls()
        self.update()

    def _set_perimeter_position(self, new_position: QPointF):
        """Set the perimeter point position."""
        self._perimeter_point = new_position
        self.prepareGeometryChange()
        self.update()

    def _set_center_position(self, new_position: QPointF):
        """Set the center position by moving both foci."""
        old_center = self.center_point
        delta = new_position - old_center
        
        # Move both foci by the same amount
        self._focus1_point += delta
        self._focus2_point += delta
        self._perimeter_point += delta
        
        # Move the CAD item to the new center
        self.setPos(self.center_point)
        self.prepareGeometryChange()
        self.update()

    # Control datum setters
    def _set_major_radius(self, new_major_radius: float):
        """Set the major radius by adjusting both focal distance and perimeter point."""
        if new_major_radius <= 0:
            logging.warning(f"Major radius must be positive, got {new_major_radius}")
            return
        
        current_major_radius = self.major_radius
        current_minor_radius = self.minor_radius
        
        if new_major_radius <= current_minor_radius:
            logging.warning(f"Major radius ({new_major_radius}) cannot be smaller than or equal to minor radius ({current_minor_radius})")
            return  # Major radius cannot be smaller than minor radius
        
        # Calculate new focal distance based on new major radius and current minor radius
        # c² = a² - b²
        new_focal_distance = math.sqrt(new_major_radius * new_major_radius - 
                                     current_minor_radius * current_minor_radius)
        
        # Calculate current focal distance
        current_focal_distance = math.hypot(self._focus2_point.x() - self._focus1_point.x(),
                                          self._focus2_point.y() - self._focus1_point.y()) / 2
        
        if current_focal_distance <= 0:
            return
        
        # Scale the foci distance
        scale_factor = new_focal_distance / current_focal_distance
        center = self.center_point
        
        # Calculate foci positions relative to center
        focus1_relative = self._focus1_point - center
        focus2_relative = self._focus2_point - center
        
        # Scale and update foci positions
        self._focus1_point = center + focus1_relative * scale_factor
        self._focus2_point = center + focus2_relative * scale_factor
        
        # Now adjust the perimeter point to achieve the exact new major radius
        # For an ellipse with foci at (-c, 0) and (c, 0), the major radius is a
        # and the perimeter point at (a, 0) satisfies: (a+c) + (a-c) = 2a
        # So we can directly calculate the perimeter point
        
        # Calculate the direction along the major axis (from center to focus2)
        major_axis_direction = self._focus2_point - center
        if major_axis_direction.x() == 0 and major_axis_direction.y() == 0:
            # If foci are at center, use a default direction
            major_axis_direction = QPointF(1, 0)
        
        # Normalize the direction
        major_axis_length = math.hypot(major_axis_direction.x(), major_axis_direction.y())
        if major_axis_length > 0:
            major_axis_direction = QPointF(major_axis_direction.x() / major_axis_length,
                                         major_axis_direction.y() / major_axis_length)
        
        # Calculate the focal distance
        focal_distance = math.hypot(self._focus2_point.x() - self._focus1_point.x(),
                                  self._focus2_point.y() - self._focus1_point.y()) / 2
        
        # For an ellipse, the perimeter point along the major axis should be at distance 'a' from center
        # where 'a' is the major radius
        perimeter_distance = new_major_radius
        
        # Set the perimeter point along the major axis
        self._perimeter_point = center + QPointF(major_axis_direction.x() * perimeter_distance,
                                               major_axis_direction.y() * perimeter_distance)
        
        self.prepareGeometryChange()
        self.update()

    def _set_minor_radius(self, new_minor_radius: float):
        """Set the minor radius by adjusting both focal distance and perimeter point."""
        if new_minor_radius <= 0:
            logging.warning(f"Minor radius must be positive, got {new_minor_radius}")
            return
        
        current_major_radius = self.major_radius
        if current_major_radius <= new_minor_radius:
            logging.warning(f"Minor radius ({new_minor_radius}) cannot be larger than or equal to major radius ({current_major_radius})")
            return  # Minor radius cannot be larger than major radius
        
        # Calculate new focal distance
        # minor_radius² = major_radius² - focal_distance²
        new_focal_distance = math.sqrt(current_major_radius * current_major_radius - 
                                     new_minor_radius * new_minor_radius)
        
        # Calculate current focal distance
        current_focal_distance = math.hypot(self._focus2_point.x() - self._focus1_point.x(),
                                          self._focus2_point.y() - self._focus1_point.y()) / 2
        
        if current_focal_distance <= 0:
            return
        
        # Scale the foci distance
        scale_factor = new_focal_distance / current_focal_distance
        center = self.center_point
        
        # Calculate foci positions relative to center
        focus1_relative = self._focus1_point - center
        focus2_relative = self._focus2_point - center
        
        # Scale and update foci positions
        self._focus1_point = center + focus1_relative * scale_factor
        self._focus2_point = center + focus2_relative * scale_factor
        
        # Now adjust the perimeter point to maintain the exact original major radius
        # For an ellipse with foci at (-c, 0) and (c, 0), the major radius is a
        # and the perimeter point at (a, 0) satisfies: (a+c) + (a-c) = 2a
        # So we can directly calculate the perimeter point
        
        # Calculate the direction along the major axis (from center to focus2)
        major_axis_direction = self._focus2_point - center
        if major_axis_direction.x() == 0 and major_axis_direction.y() == 0:
            # If foci are at center, use a default direction
            major_axis_direction = QPointF(1, 0)
        
        # Normalize the direction
        major_axis_length = math.hypot(major_axis_direction.x(), major_axis_direction.y())
        if major_axis_length > 0:
            major_axis_direction = QPointF(major_axis_direction.x() / major_axis_length,
                                         major_axis_direction.y() / major_axis_length)
        
        # For an ellipse, the perimeter point along the major axis should be at distance 'a' from center
        # where 'a' is the major radius (which should remain unchanged)
        perimeter_distance = current_major_radius
        
        # Set the perimeter point along the major axis
        self._perimeter_point = center + QPointF(major_axis_direction.x() * perimeter_distance,
                                               major_axis_direction.y() * perimeter_distance)
        
        self.prepareGeometryChange()
        self.update()

    def _set_rotation_angle(self, new_rotation: float):
        """Set the rotation angle by rotating the foci and perimeter point around the center."""
        current_rotation = self.rotation_angle
        rotation_delta = new_rotation - current_rotation
        
        # Rotate foci and perimeter point around the center
        center = self.center_point
        angle_rad = math.radians(rotation_delta)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Rotate focus1
        focus1_relative = self._focus1_point - center
        new_focus1_x = focus1_relative.x() * cos_angle - focus1_relative.y() * sin_angle
        new_focus1_y = focus1_relative.x() * sin_angle + focus1_relative.y() * cos_angle
        self._focus1_point = center + QPointF(new_focus1_x, new_focus1_y)
        
        # Rotate focus2
        focus2_relative = self._focus2_point - center
        new_focus2_x = focus2_relative.x() * cos_angle - focus2_relative.y() * sin_angle
        new_focus2_y = focus2_relative.x() * sin_angle + focus2_relative.y() * cos_angle
        self._focus2_point = center + QPointF(new_focus2_x, new_focus2_y)
        
        # Rotate perimeter point
        perimeter_relative = self._perimeter_point - center
        new_perimeter_x = perimeter_relative.x() * cos_angle - perimeter_relative.y() * sin_angle
        new_perimeter_y = perimeter_relative.x() * sin_angle + perimeter_relative.y() * cos_angle
        self._perimeter_point = center + QPointF(new_perimeter_x, new_perimeter_y)
        
        self.updateControls()
        self.prepareGeometryChange()
        self.update() 