"""
CircleCadItem - A circle CAD item defined by center point and perimeter point.
"""

from typing import Optional, Tuple, TYPE_CHECKING, List

from ..cad_object import CadObject
from ...cad_geometry import Point2D, Circle, ShapeType, Shape2D
from ...utils.constraints import (
    ConstraintSolver,
    ConstrainableLength,
    ConstrainablePoint2D,
    ConstrainableCircle,
    Constrainable,
)

if TYPE_CHECKING:
    from ...models.document import Document


class CircleCadObject(CadObject):
    """A circle CAD item defined by center point and perimeter point."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            perimeter_point: Point2D,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self._center_point = center_point
        self._perimeter_point = perimeter_point
        radius = center_point.distance_to(perimeter_point)
        self.circle = Circle(center_point, radius)

    def boundingRect(self):
        """Return the bounding rectangle of the circle."""
        return self.circle.get_bounds()

    @property
    def radius(self):
        """Calculate the radius from center to perimeter point."""
        return self.circle.radius

    @radius.setter
    def radius(self, value):
        """Set the radius by moving the perimeter point."""
        angle = (self._perimeter_point - self._center_point).angle_radians
        self._perimeter_point = self._center_point + Point2D(value, angle=angle)
        self.circle.radius = value

    @property
    def diameter(self):
        """Get the diameter of the circle."""
        return self.radius * 2
    
    @diameter.setter
    def diameter(self, value):
        """Set the diameter of the circle."""
        self.radius = value / 2

    @property
    def center_point(self):
        """Get the center point."""
        return self._center_point
    
    @center_point.setter
    def center_point(self, value):
        """Set the center point."""
        value = Point2D(value)
        delta = value - self._center_point
        self._center_point = value
        self.circle.center = value
        self._perimeter_point += delta

    @property
    def perimeter_point(self):
        """Get the perimeter point."""
        return self._perimeter_point
    
    @perimeter_point.setter
    def perimeter_point(self, value):
        """Set the perimeter point."""
        self._perimeter_point = value
        self.circle.radius = self._center_point.distance_to(value)

    def translate(self, dx, dy):
        """Move center and radius points by the specified offset."""
        delta = Point2D(dx, dy)
        self.circle.translate(delta)
        self._center_point.translate(delta)
        self._perimeter_point.translate(delta)

    def scale(self, scale, center):
        """Scale the circle by the specified factor around the center point."""
        self.circle.scale(scale, center)
        self._center_point.scale(scale, center)
        self._perimeter_point.scale(scale, center)

    def rotate(self, angle, center):
        """Rotate the circle by the specified angle around the center point."""
        self.circle.rotate(angle, center)
        self._center_point.rotate(angle, center)
        self._perimeter_point.rotate(angle, center)

    def transform(self, transform):
        """Transform the circle by the specified transform."""
        self.circle.transform(transform)
        self._center_point.transform(transform)
        self._perimeter_point.transform(transform)

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
        self.constraint_circle = ConstrainableCircle(solver, cp, radius)

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_circle'):
            # Update the constrainable center point with current center
            self.constraint_circle.center.update_values(self.circle.center.x, self.circle.center.y)
            # Update the constrainable radius with current radius
            self.constraint_circle.radius.solver.update_variable(self.constraint_circle.radius.index, self.circle.radius)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        cx, cy, radius = self.constraint_circle.get(solver.variables)
        self.circle.center = Point2D(cx, cy)
        self.circle.radius = radius
        # Update the stored points to match
        self._center_point = self.circle.center
        angle = (self._perimeter_point - self._center_point).angle_radians
        self._perimeter_point = self._center_point + Point2D(radius, angle=angle)

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_circle'):
            return [
                ("center", self.constraint_circle.center),
                ("radius", self.constraint_circle.radius)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the object data."""
        return {
            "center": self.circle.center.to_string(),
            "radius": str(self.circle.radius),
        }

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'CircleCadObject':
        """Create a circle object from the given data."""
        data["center"] = Point2D.from_string(data["center"])
        data["radius"] = float(data["radius"])
        data["perimeter_point"] = Point2D(data["radius"], angle=0)
        return cls(document, data["center"], data["perimeter_point"])

CadObject.register_object_type(CircleCadObject, "circle", {"center": "0,0", "radius": "1"})
