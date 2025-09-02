"""
EllipseCadObject - An ellipse CAD object defined by center point, radius1, radius2, and rotation.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, Ellipse,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainableLength, ConstrainableAngle,
    ConstrainablePoint2D, ConstrainableEllipse,
)

if TYPE_CHECKING:
    from ...models.document import Document


class EllipseCadObject(CadObject):
    """An ellipse CAD object defined by center point, radius1, radius2, and rotation_degrees."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            radius1: float,
            radius2: float,
            rotation_degrees: float = 0.0,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self.ellipse = Ellipse(center_point, radius1, radius2, rotation_degrees)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the ellipse."""
        if not self.ellipse:
            return (0, 0, 0, 0)
        return self.ellipse.get_bounds()

    @property
    def center_point(self) -> Point2D:
        """Get the center point."""
        if not self.ellipse:
            return Point2D(0, 0)
        return self.ellipse.center
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point."""
        if not self.ellipse:
            return
        self.ellipse.center = Point2D(value)

    @property
    def radius1(self) -> float:
        """Get the first radius."""
        if not self.ellipse:
            return 0
        return self.ellipse.major_axis / 2
    
    @radius1.setter
    def radius1(self, value: float):
        """Set the first radius."""
        if not self.ellipse:
            return
        self.ellipse = Ellipse(self.ellipse.center, value, self.ellipse.radius2, self.ellipse.rotation_degrees)

    @property
    def radius2(self) -> float:
        """Get the second radius."""
        if not self.ellipse:
            return 0
        return self.ellipse.minor_axis / 2
    
    @radius2.setter
    def radius2(self, value: float):
        """Set the second radius."""
        if not self.ellipse:
            return
        self.ellipse = Ellipse(self.ellipse.center, self.ellipse.radius1, value, self.ellipse.rotation_degrees)

    @property
    def rotation_degrees(self) -> float:
        """Get the rotation angle in degrees."""
        if not self.ellipse:
            return 0
        return self.ellipse.rotation_degrees
    
    @rotation_degrees.setter
    def rotation_degrees(self, value: float):
        """Set the rotation angle in degrees."""
        if not self.ellipse:
            return
        self.ellipse.rotation_degrees = float(value)

    @property
    def rotation_radians(self) -> float:
        """Get the rotation angle in radians."""
        if not self.ellipse:
            return 0
        return self.ellipse.rotation_radians
    
    @rotation_radians.setter
    def rotation_radians(self, value: float):
        """Set the rotation angle in radians."""
        if not self.ellipse:
            return
        self.ellipse.rotation_radians = value

    @property
    def major_axis_point(self) -> Point2D:
        """Get the major axis point."""
        if not self.ellipse:
            return Point2D(0, 0)
        return self.ellipse.center + Point2D(self.ellipse.major_axis / 2, angle=self.ellipse.rotation_degrees)
    
    @major_axis_point.setter
    def major_axis_point(self, value: Point2D):
        """Set the major axis point by calculating radius and rotation."""
        if not self.ellipse:
            return
        point = Point2D(value)
        radius1 = self.ellipse.center.distance_to(point)
        rotation_degrees = (point - self.ellipse.center).angle_degrees
        self.ellipse = Ellipse(self.ellipse.center, radius1, self.ellipse.radius2, rotation_degrees)

    @property
    def minor_axis_point(self) -> Point2D:
        """Get the minor axis point."""
        if not self.ellipse:
            return Point2D(0, 0)
        return self.ellipse.center + Point2D(self.ellipse.minor_axis / 2, angle=self.ellipse.rotation_degrees + 90)
    
    @minor_axis_point.setter
    def minor_axis_point(self, value: Point2D):
        """Set the minor axis point by calculating radius."""
        if not self.ellipse:
            return
        point = Point2D(value)
        radius2 = self.ellipse.center.distance_to(point)
        self.ellipse = Ellipse(self.ellipse.center, self.ellipse.radius1, radius2, self.ellipse.rotation_degrees)

    @property
    def major_axis(self) -> float:
        """Get the major axis length."""
        if not self.ellipse:
            return 0
        return self.ellipse.major_axis
    
    @major_axis.setter
    def major_axis(self, value: float):
        """Set the major axis length."""
        if not self.ellipse:
            return
        self.ellipse.major_axis = value

    @property
    def minor_axis(self) -> float:
        """Get the minor axis length."""
        if not self.ellipse:
            return 0
        return self.ellipse.minor_axis
    
    @minor_axis.setter
    def minor_axis(self, value: float):
        """Set the minor axis length."""
        if not self.ellipse:
            return
        self.ellipse.minor_axis = value

    @property
    def focus1(self) -> Point2D:
        """Get the first focus point."""
        if not self.ellipse:
            return Point2D(0, 0)
        return self.ellipse.get_foci()[0]
    
    @focus1.setter
    def focus1(self, value: Point2D):
        """Set the first focus point by updating the ellipse parameters."""
        if not self.ellipse:
            return
        value = Point2D(value)
        focus2 = self.ellipse.get_foci()[1]
                
        # Calculate major axis length (sum of distances from foci to any point on ellipse)
        # For simplicity, use the current major axis length
        major_axis_length = self.major_axis
        
        # Create new ellipse from foci
        self.ellipse = Ellipse.from_foci(value, focus2, major_axis_length)

    @property
    def focus2(self) -> Point2D:
        """Get the second focus point."""
        if not self.ellipse:
            return Point2D(0, 0)
        return self.ellipse.get_foci()[1]
    
    @focus2.setter
    def focus2(self, value: Point2D):
        """Set the second focus point by updating the ellipse parameters."""
        if not self.ellipse:
            return
        value = Point2D(value)
        focus1 = self.ellipse.get_foci()[0]
        
        # Calculate major axis length (sum of distances from foci to any point on ellipse)
        # For simplicity, use the current major axis length
        major_axis_length = self.major_axis
        
        # Create new ellipse from foci
        self.ellipse = Ellipse.from_foci(focus1, value, major_axis_length)

    def translate(self, dx: float, dy: float):
        """Move the ellipse by the specified offset."""
        if not self.ellipse:
            return
        self.ellipse.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the ellipse by the specified factor around the center point."""
        if not self.ellipse:
            return
        self.ellipse.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the ellipse by the specified angle around the center point."""
        if not self.ellipse:
            return
        self.ellipse.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the ellipse by the given transform."""
        if not self.ellipse:
            return
        self.ellipse.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the ellipse contains the given point."""
        if not self.ellipse:
            return False
        closest_point = self.ellipse.closest_point_to(point)
        return point.distance_to(closest_point) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the ellipse into simpler objects."""
        if not self.ellipse:
            return []
        return [self.ellipse]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this ellipse."""
        if not self.ellipse:
            return
        # Create constraint points for center, major axis, and minor axis
        center_cp = ConstrainablePoint2D(solver, (self.ellipse.center.x, self.ellipse.center.y), fixed=False)
        radius1 = ConstrainableLength(solver, self.radius1, fixed=False)
        radius2 = ConstrainableLength(solver, self.radius2, fixed=False)
        rotation_degrees = ConstrainableAngle(solver, self.rotation_degrees, fixed=False)
        ellipse = ConstrainableEllipse(solver, center_cp, radius1, radius2, rotation_degrees)
        
        # Store constraint objects for later updates
        self.constraint_center = center_cp
        self.constraint_radius1 = radius1
        self.constraint_radius2 = radius2
        self.constraint_rotation_degrees = rotation_degrees
        self.constraint_ellipse = ellipse

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if not self.ellipse:
            return
        if hasattr(self, 'constraint_center'):
            # Update the constrainable points with current ellipse points
            self.constraint_center.update_values(self.ellipse.center.x, self.ellipse.center.y)
            self.constraint_radius1.update_value(self.radius1)
            self.constraint_radius2.update_value(self.radius2)
            self.constraint_rotation_degrees.update_value(self.rotation_degrees)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        if not self.ellipse:
            return
        # Get updated coordinates from constraints
        cx, cy = self.constraint_center.get(solver.variables)
        r1 = self.constraint_radius1.get(solver.variables)
        r2 = self.constraint_radius2.get(solver.variables)
        rotation_degrees = self.constraint_rotation_degrees.get(solver.variables)
        
        # Update the center point
        center_point = Point2D(cx, cy)
        
        # Create new ellipse with updated parameters
        self.ellipse = Ellipse(center_point, r1, r2, rotation_degrees)

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if not self.ellipse:
            return []
        if hasattr(self, 'constraint_center'):
            return [
                ("center", self.constraint_center),
                ("radius1", self.constraint_radius1),
                ("radius2", self.constraint_radius2),
                ("rotation_angle", self.constraint_rotation_degrees),
                ("ellipse", self.constraint_ellipse)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        if not self.ellipse:
            return {}
        data = {}
        data["center_point"] = self.ellipse.center.to_string()
        data["radius1"] = self.radius1
        data["radius2"] = self.radius2
        data["rotation_degrees"] = self.rotation_degrees
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'EllipseCadObject':
        """Create an ellipse object from serialized data."""
        center_point = Point2D(*data["center_point"])
        radius1 = data["radius1"]
        radius2 = data["radius2"]
        rotation_degrees = data.get("rotation_degrees", 0.0)
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, center_point, radius1, radius2, rotation_degrees, color, line_width) 