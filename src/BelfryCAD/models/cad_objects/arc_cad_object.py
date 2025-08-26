"""
ArcCadObject - An arc CAD object defined by center point, radius, start angle, and span angle.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, Arc,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainableLength, ConstrainableAngle,
    ConstrainablePoint2D,ConstrainableArc,
)

if TYPE_CHECKING:
    from ...models.document import Document


class ArcCadObject(CadObject):
    """An arc CAD object defined by center point, radius, start angle, and span angle."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            radius: float,
            start_degrees: float,
            span_degrees: float,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self.arc = Arc(center_point, radius, start_degrees, span_degrees)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the arc."""
        return self.arc.get_bounds()

    @property
    def center_point(self) -> Point2D:
        """Get the center point."""
        return self.arc.center
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point."""
        self.arc.center = Point2D(value)

    @property
    def radius(self) -> float:
        """Get the radius of the arc."""
        return self.arc.radius
    
    @radius.setter
    def radius(self, value: float):
        """Set the radius."""
        self.arc.radius = float(value)

    @property
    def start_degrees(self) -> float:
        """Get the start angle in degrees."""
        return self.arc.start_degrees
    
    @start_degrees.setter
    def start_degrees(self, value: float):
        """Set the start angle in degrees."""
        self.arc.start_degrees = float(value)

    @property
    def span_degrees(self) -> float:
        """Get the span angle in degrees."""
        return self.arc.span_degrees
    
    @span_degrees.setter
    def span_degrees(self, value: float):
        """Set the span angle in degrees."""
        self.arc.span_degrees = float(value)

    @property
    def end_degrees(self) -> float:
        """Get the end angle in degrees."""
        return self.arc.end_degrees
    
    @end_degrees.setter
    def end_degrees(self, value: float):
        """Set the end angle by adjusting the span angle."""
        self.arc.span_degrees = value - self.arc.start_degrees

    @property
    def start_point(self) -> Point2D:
        """Get the start point of the arc."""
        return self.arc.start_point
    
    @start_point.setter
    def start_point(self, value: Point2D):
        """Set the start point by adjusting the start angle."""
        point = Point2D(value)
        self.arc.start_degrees = (point - self.arc.center).angle_degrees

    @property
    def end_point(self) -> Point2D:
        """Get the end point of the arc."""
        return self.arc.end_point
    
    @end_point.setter
    def end_point(self, value: Point2D):
        """Set the end point by adjusting the span angle."""
        point = Point2D(value)
        end_degrees = (point - self.arc.center).angle_degrees
        self.arc.span_degrees = end_degrees - self.arc.start_degrees

    def translate(self, dx: float, dy: float):
        """Move the arc by the specified offset."""
        self.arc.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the arc by the specified factor around the center point."""
        self.arc.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the arc by the specified angle in degrees around the center point."""
        self.arc.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the arc by the given transform."""
        self.arc.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the arc contains the given point."""
        return self.arc.contains_point(point, tolerance)

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the arc into simpler objects."""
        return self.arc.decompose(into)

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this arc."""
        # Create constraint points for center, start, and end
        center_cp = ConstrainablePoint2D(solver, (self.arc.center.x, self.arc.center.y), fixed=False)
        radius = ConstrainableLength(solver, self.arc.radius, fixed=False)
        start_degrees = ConstrainableAngle(solver, self.arc.start_degrees, fixed=False)
        span_degrees = ConstrainableAngle(solver, self.arc.span_degrees, fixed=False)
        arc = ConstrainableArc(solver, center_cp, radius, start_degrees, span_degrees)
        
        # Store constraint objects for later updates
        self.constraint_center = center_cp
        self.constraint_radius = radius
        self.constraint_start = start_degrees
        self.constraint_span = span_degrees
        self.constraint_arc = arc

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_center'):
            # Update the constrainable points with current arc points
            self.constraint_center.update_values(self.arc.center.x, self.arc.center.y)
            self.constraint_radius.update_value(self.arc.radius)
            self.constraint_start.update_value(self.arc.start_degrees)
            self.constraint_span.update_value(self.arc.span_degrees)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        # Get updated coordinates from constraints
        cx, cy, r, start_degrees, span_degrees = \
            self.constraint_arc.get(solver.variables)

        # Update the arc geometry directly
        self.arc = Arc(Point2D(cx, cy), r, start_degrees, span_degrees)

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_center'):
            return [
                ("center", self.constraint_center),
                ("start_angle", self.constraint_start),
                ("span_angle", self.constraint_span),
                ("radius", self.constraint_radius),
                ("arc", self.constraint_arc),
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["center_point"] = self.arc.center.to_string()
        data["radius"] = self.arc.radius
        data["start_degrees"] = self.arc.start_degrees
        data["span_degrees"] = self.arc.span_degrees
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'ArcCadObject':
        """Create an arc object from serialized data."""
        center_point = Point2D(*data["center_point"])
        radius = data["radius"]
        start_degrees = data["start_degrees"]
        span_degrees = data["span_degrees"]
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, center_point, radius, start_degrees, span_degrees, color, line_width)

