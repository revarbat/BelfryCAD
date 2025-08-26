"""
GearCadObject - A gear CAD object defined by center point and parameters.
"""

import math
from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, SpurGear, Polygon, Circle,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainablePoint2D, ConstrainableCircle,
)

if TYPE_CHECKING:
    from ...models.document import Document


class GearCadObject(CadObject):
    """A gear CAD object defined by center point, pitch diameter, and number of teeth."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            pitch_radius: float,
            num_teeth: int,
            pressure_angle: float = 20.0,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self._center_point = center_point
        self._pitch_radius = pitch_radius
        self._num_teeth = num_teeth
        self._pressure_angle = pressure_angle
        self._update_gear()

    def _update_gear(self):
        """Update the gear geometry from the current parameters."""
        # Create or update the SpurGear instance
        self._spur_gear = SpurGear(
            num_teeth=self._num_teeth,
            pitch_diameter=self._pitch_radius * 2,  # Convert radius to diameter
            pressure_angle=self._pressure_angle
        )
        
        # Update the circle and polygon
        self.circle = Circle(self._center_point, self._pitch_radius)
        self.gear_polygon = self._generate_gear_profile()

    def _generate_gear_profile(self) -> Polygon:
        """Generate the gear tooth profile as a polygon using SpurGear."""
        # Generate gear path using SpurGear
        gear_points = self._spur_gear._to_points(0.001)
        
        # Convert points to Point2D and apply center offset
        polygon_points = []
        for point in gear_points:
            offset_point = point + self._center_point
            polygon_points.append(offset_point)
        
        return Polygon(polygon_points)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the gear."""
        return self.gear_polygon.get_bounds()

    @property
    def center_point(self) -> Point2D:
        """Get the center point."""
        return self._center_point
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point."""
        self._center_point = Point2D(value)
        self._update_gear()

    @property
    def pitch_radius(self) -> float:
        """Get the pitch radius."""
        return self._pitch_radius
    
    @pitch_radius.setter
    def pitch_radius(self, value: float):
        """Set the pitch radius."""
        self._pitch_radius = value
        self._update_gear()

    @property
    def pitch_diameter(self) -> float:
        """Get the pitch diameter."""
        return self._pitch_radius * 2
    
    @pitch_diameter.setter
    def pitch_diameter(self, value: float):
        """Set the pitch diameter."""
        self._pitch_radius = value / 2
        self._update_gear()

    @property
    def num_teeth(self) -> int:
        """Get the number of teeth."""
        return self._num_teeth
    
    @num_teeth.setter
    def num_teeth(self, value: int):
        """Set the number of teeth."""
        self._num_teeth = value
        self._update_gear()

    @property
    def pressure_angle(self) -> float:
        """Get the pressure angle in degrees."""
        return self._pressure_angle
    
    @pressure_angle.setter
    def pressure_angle(self, value: float):
        """Set the pressure angle in degrees."""
        self._pressure_angle = value
        self._update_gear()

    @property
    def circular_pitch(self) -> float:
        """Get the circular pitch."""
        return (math.pi * self.pitch_diameter) / self._num_teeth

    @property
    def diametral_pitch(self) -> float:
        """Get the diametral pitch."""
        return self._num_teeth / self.pitch_diameter

    @property
    def module(self) -> float:
        """Get the module (pitch diameter / teeth)."""
        return self.pitch_diameter / self._num_teeth

    def get_gear_path_points(self) -> List[Point2D]:
        """Get gear path points for rendering."""
        if self._spur_gear is None:
            self._update_gear()
        
        gear_points = self._spur_gear._to_points(0.001)
        # Apply center offset
        return [point + self._center_point for point in gear_points]

    def get_pitch_circle_points(self) -> List[Point2D]:
        """Get pitch circle points for construction display."""
        if self._spur_gear is None:
            self._update_gear()
        
        pitch_points = self._spur_gear.get_pitch_circle_points()
        # Apply center offset
        return [point + self._center_point for point in pitch_points]

    def translate(self, dx: float, dy: float):
        """Move the gear by the specified offset."""
        self.circle.translate(Point2D(dx, dy))
        self.gear_polygon.translate(Point2D(dx, dy))
        self._center_point.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the gear by the specified factor around the center point."""
        self.circle.scale(scale, center)
        self.gear_polygon.scale(scale, center)
        self._center_point.scale(scale, center)
        self._pitch_radius *= scale

    def rotate(self, angle: float, center: Point2D):
        """Rotate the gear by the specified angle around the center point."""
        self.circle.rotate(angle, center)
        self.gear_polygon.rotate(angle, center)
        self._center_point.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the gear by the given transform."""
        self.circle.transform(transform)
        self.gear_polygon.transform(transform)
        self._center_point.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the gear contains the given point."""
        # For now, check if point is within the pitch circle
        return abs(self._center_point.distance_to(point) - self.pitch_radius) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the gear into simpler objects."""
        return [self.gear_polygon]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this gear."""
        # Create constraint point for center
        center_cp = ConstrainablePoint2D(solver, (self._center_point.x, self._center_point.y), fixed=False)
        
        # Store constraint objects for later updates
        self.constraint_center = center_cp

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_center'):
            # Update the constrainable center point with current center
            self.constraint_center.update_values(self._center_point.x, self._center_point.y)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        # Get updated coordinates from constraints
        center_x, center_y = self.constraint_center.get(solver.variables)
        
        # Update the stored center point
        self._center_point = Point2D(center_x, center_y)
        
        # Update the gear geometry
        self._update_gear()

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_center'):
            return [
                ("center", self.constraint_center)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["center_point"] = self._center_point.to_string()
        data["pitch_radius"] = str(self.pitch_radius)
        data["num_teeth"] = str(self.num_teeth)
        data["pressure_angle"] = str(self.pressure_angle)
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'GearCadObject':
        """Create a gear object from serialized data."""
        center_point = Point2D(*data["center_point"])
        pitch_diameter = data["pitch_diameter"]
        num_teeth = data["num_teeth"]
        pressure_angle = data.get("pressure_angle", 20.0)
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, center_point, pitch_diameter, num_teeth, pressure_angle, color, line_width)

