"""
CubicBezierCadObject - A cubic Bezier curve CAD object defined by four control points.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, BezierPath,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainablePoint2D, ConstrainableBezierPath,
)

if TYPE_CHECKING:
    from ..document import Document


class CubicBezierCadObject(CadObject):
    """A cubic Bezier curve CAD object defined by a list of control points."""

    def __init__(
            self,
            document: 'Document',
            points: List[Point2D],
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self.bezier_path = BezierPath(points)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the Bezier curve."""
        return self.bezier_path.get_bounds()

    @property
    def points(self) -> List[Point2D]:
        """Get all control points as a list."""
        return self.bezier_path.points.copy()
    
    @points.setter
    def points(self, value: List[Point2D]):
        """Set all control points from a list."""
        self.bezier_path = BezierPath([Point2D(p) for p in value])

    @property
    def start_point(self) -> Optional[Point2D]:
        """Get the start point of the first segment."""
        return self.bezier_path.start_point
    
    @property
    def end_point(self) -> Optional[Point2D]:
        """Get the end point of the last segment."""
        return self.bezier_path.end_point

    @property
    def is_closed(self) -> bool:
        """Check if the path is closed (start and end points are the same)."""
        return self.bezier_path.is_closed

    def add_point(self, point: Point2D):
        """Add a new control point to the end of the list."""
        new_points = self.bezier_path.points + [Point2D(point)]
        self.bezier_path = BezierPath(new_points)

    def insert_point(self, index: int, point: Point2D):
        """Insert a control point at the specified index."""
        points = self.bezier_path.points.copy()
        points.insert(index, Point2D(point))
        self.bezier_path = BezierPath(points)

    def remove_point(self, index: int):
        """Remove a control point at the specified index."""
        points = self.bezier_path.points.copy()
        if 0 <= index < len(points):
            del points[index]
            self.bezier_path = BezierPath(points)

    def get_point(self, index: int) -> Point2D:
        """Get a specific control point by index."""
        points = self.bezier_path.points
        if 0 <= index < len(points):
            return points[index]
        raise IndexError(f"Point index {index} out of range")

    def set_point(self, index: int, point: Point2D):
        """Set a specific control point by index."""
        points = self.bezier_path.points.copy()
        if 0 <= index < len(points):
            points[index] = Point2D(point)
            self.bezier_path = BezierPath(points)
        else:
            raise IndexError(f"Point index {index} out of range")

    def get_segments(self) -> List[Tuple[Point2D, Point2D, Point2D, Point2D]]:
        """Get all segments as a list of (start, control1, control2, end) tuples."""
        return self.bezier_path._get_segments_from_points()

    def point_at_parameter(self, t: float) -> Optional[Point2D]:
        """Get the point on the curve at parameter t (0 <= t <= 1)."""
        return self.bezier_path.point_at_parameter(t)

    def tangent_at_parameter(self, t: float) -> Optional[Point2D]:
        """Get the tangent vector at parameter t (0 <= t <= 1)."""
        return self.bezier_path.tangent_at_parameter(t)

    def translate(self, dx: float, dy: float):
        """Move the Bezier curve by the specified offset."""
        self.bezier_path.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the Bezier curve by the specified factor around the center point."""
        self.bezier_path.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the Bezier curve by the specified angle around the center point."""
        self.bezier_path.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the Bezier curve by the given transform."""
        self.bezier_path.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the Bezier curve contains the given point."""
        closest_point = self.bezier_path.closest_point_to(point)
        return point.distance_to(closest_point) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the Bezier curve into simpler objects."""
        return [self.bezier_path]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this Bezier curve."""
        # Create constraint points for all control points
        self._constraint_points = []
        for point in self.bezier_path.points:
            cp = ConstrainablePoint2D(solver, (point.x, point.y), fixed=False)
            self._constraint_points.append(cp)
        self.constraint_bezier = ConstrainableBezierPath(solver, self._constraint_points)

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, '_constraint_points'):
            # Update all constraint points with current control points
            for i, constraint_point in enumerate(self._constraint_points):
                if i < len(self.bezier_path.points):
                    constraint_point.update_values(self.bezier_path.points[i].x, self.bezier_path.points[i].y)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        # Update all control points from constraints
        new_points = []
        for constraint_point in self._constraint_points:
            x, y = constraint_point.get(solver.variables)
            new_points.append(Point2D(x, y))
        
        # Update the Bezier path geometry
        self.bezier_path = BezierPath(new_points)

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, '_constraint_points'):
            constrainables = []
            for i, cp in enumerate(self._constraint_points):
                constrainables.append((f"point_{i}", cp))
            constrainables.append(("bezier", self.constraint_bezier))
            return constrainables
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["points"] = [point.to_string() for point in self.bezier_path.points]
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'CubicBezierCadObject':
        """Create a Bezier curve object from serialized data."""
        points = [Point2D(*point_data) for point_data in data["points"]]
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, points, color, line_width)
