"""
CircleCadObject - A circle CAD object defined by center point and radius.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D,
    Point2D, Circle,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainableLength, ConstrainablePoint2D,
    ConstrainableCircle,
)

if TYPE_CHECKING:
    from ...models.document import Document


class CircleCadObject(CadObject):
    """A circle CAD object defined by center point and radius."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            radius: float,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self.circle = Circle(center_point, radius)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the circle."""
        return self.circle.get_bounds()

    @property
    def radius(self) -> float:
        """Get the radius of the circle."""
        return self.circle.radius
    
    @radius.setter
    def radius(self, value: float):
        """Set the radius of the circle."""
        self.circle.radius = float(value)

    @property
    def diameter(self) -> float:
        """Get the diameter of the circle."""
        return self.circle.diameter
    
    @diameter.setter
    def diameter(self, value: float):
        """Set the diameter of the circle."""
        self.circle.radius = float(value) / 2

    @property
    def center_point(self) -> Point2D:
        """Get the center point."""
        return self.circle.center
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point."""
        self.circle.center = Point2D(value)

    @property
    def perimeter_point(self) -> Point2D:
        """Get a point on the perimeter (at 0 degrees)."""
        return self.circle.center + Point2D(self.circle.radius, angle=0.0)
    
    @perimeter_point.setter
    def perimeter_point(self, value: Point2D):
        """Set the radius by calculating distance from center to the given point."""
        point = Point2D(value)
        self.circle.radius = self.circle.center.distance_to(point)

    def translate(self, dx: float, dy: float):
        """Move the circle by the specified offset."""
        self.circle.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the circle by the specified factor around the center point."""
        self.circle.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the circle by the specified angle around the center point."""
        self.circle.rotate(angle, center)

    def transform(self, transform):
        """Transform the circle by the specified transform."""
        self.circle.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the circle contains the given point."""
        return abs((point - self.circle.center).magnitude - self.circle.radius) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the circle into simpler objects."""
        return [self.circle]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for the circle."""
        cp = ConstrainablePoint2D(solver, (self.circle.center.x, self.circle.center.y), fixed=False)
        radius = ConstrainableLength(solver, self.circle.radius, fixed=True)
        circle = ConstrainableCircle(solver, cp, radius)
        self.constraint_center = cp
        self.constraint_radius = radius
        self.constraint_circle = circle

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_circle'):
            # Update the constrainable center point with current center
            self.constraint_center.update_values(self.circle.center.x, self.circle.center.y)
            # Update the constrainable radius with current radius
            self.constraint_radius.update_value(self.circle.radius)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        cx, cy, radius = self.constraint_circle.get(solver.variables)
        self.circle.center = Point2D(cx, cy)
        self.circle.radius = radius

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_circle'):
            return [
                ("center", self.constraint_center),
                ("radius", self.constraint_radius),
                ("circle", self.constraint_circle),
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the object data."""
        return {
            "center_point": self.circle.center.to_string(),
            "radius": self.circle.radius,
        }

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'CircleCadObject':
        """Create a circle object from the given data."""
        center_point = Point2D(*data["center_point"])
        radius = data["radius"]
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        return cls(document, center_point, radius, color, line_width)

CadObject.register_object_type(CircleCadObject, "circle", {"center_point": "0,0", "radius": "1"})
