"""
LineCadObject - A line CAD object defined by two points.
"""

from typing import Optional, Tuple, TYPE_CHECKING, List

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, Line2D,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainablePoint2D, ConstrainableLine2D,
)

if TYPE_CHECKING:
    from ...models.document import Document


class LineCadObject(CadObject):
    """A line CAD item defined by two points."""

    def __init__(
            self,
            document: 'Document',
            start_point: Point2D,
            end_point: Point2D,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self.line = Line2D(start_point, end_point)

    @property
    def start_point(self) -> Point2D:
        """Get the start point."""
        return self.line.start

    @start_point.setter
    def start_point(self, value: Point2D):
        """Set the start point."""
        self.line.start = value

    @property 
    def mid_point(self) -> Point2D:
        """Get the midpoint of the line segment."""
        return self.line.midpoint

    @mid_point.setter
    def mid_point(self, value: Point2D):
        """Set the midpoint of the line segment."""
        self.line.midpoint = value

    @property
    def end_point(self) -> Point2D:
        """Get the end point."""
        return self.line.end

    @end_point.setter
    def end_point(self, value: Point2D):
        """Set the end point."""
        self.line.end = value

    @property
    def points(self) -> Tuple[Point2D, Point2D]:
        """Get both points as a tuple."""
        return (self.line.start, self.line.end)

    @points.setter
    def points(self, value):
        """Set both points from a tuple/list of two points."""
        if len(value) != 2:
            raise ValueError("Points must contain exactly 2 points")
        start, end = value
        self.line.start = start
        self.line.end = end

    @property
    def length(self):
        """Calculate the length of the line segment."""
        return self.line.length

    @length.setter
    def length(self, value):
        """Set the length of the line segment by moving the endpoint."""
        current_angle = self.line.angle_radians
        self.line.end = Point2D(value, angle=current_angle)

    @property
    def angle_radians(self) -> float:
        """Calculate the angle of the line segment in radians."""
        return self.line.angle_radians

    @angle_radians.setter
    def angle_radians(self, value):
        """Set the angle of the line segment by moving the endpoint."""
        self.line.angle_radians = value

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the line segment."""
        return self.line.get_bounds()

    def translate(self, dx: float, dy: float):
        """Move both endpoints by the specified offset."""
        self.line += Point2D(dx, dy)

    def scale(self, scale: float, center: Point2D):
        """Scale the line segment by the specified scale factor around the center point."""
        self.line.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the line segment by the specified angle around the center point."""
        self.line.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the line segment by the specified transform."""
        self.line.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the line segment contains the given point."""
        return self.line.distance_to_point(point) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the line into simpler objects."""
        return [self.line]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this object."""
        csp = ConstrainablePoint2D(solver, (self.line.start.x, self.line.start.y), fixed=False)
        cep = ConstrainablePoint2D(solver, (self.line.end.x, self.line.end.y), fixed=False)
        cl = ConstrainableLine2D(solver, csp, cep)
        self.constraint_start_point = csp
        self.constraint_end_point = cep
        self.constraint_line = cl

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_line'):
            # Update the constrainable points with current line endpoints
            self.constraint_line.p1.update_values(self.line.start.x, self.line.start.y)
            self.constraint_line.p2.update_values(self.line.end.x, self.line.end.y)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        spx, spy, epx, epy = self.constraint_line.get(solver.variables)
        self.line.start = Point2D(spx, spy)
        self.line.end = Point2D(epx, epy)

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_line'):
            return [
                ("start_point", self.constraint_line.p1),
                ("end_point", self.constraint_line.p2),
                ("line", self.constraint_line)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["start_point"] = self.line.start.to_string()
        data["end_point"] = self.line.end.to_string()
        return data
    
    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'LineCadObject':
        """Create a line object from the given data."""
        data["start"] = Point2D.from_string(data["start"])
        data["end"] = Point2D.from_string(data["end"])
        return cls(document, data["start"], data["end"])

CadObject.register_object_type(LineCadObject, "line", {"start": "", "end": ""})
