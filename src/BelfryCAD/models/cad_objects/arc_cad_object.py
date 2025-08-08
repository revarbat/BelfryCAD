"""
ArcCadObject - An arc CAD object defined by center point, start point, and end point.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ..cad_object import CadObject
from ...cad_geometry import (
    Point2D, Arc, Transform2D, ShapeType, Shape2D
)
from ...utils.constraints import (
    ConstraintSolver,
    ConstrainablePoint2D,
    Constrainable,
)

if TYPE_CHECKING:
    from ...models.document import Document


class ArcCadObject(CadObject):
    """An arc CAD object defined by center point, start point, and end point."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            start_point: Point2D,
            end_point: Point2D,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self._center_point = center_point
        self._start_point = start_point
        self._end_point = end_point
        self._update_arc()

    def _update_arc(self):
        """Update the arc geometry from the current points."""
        radius = self._center_point.distance_to(self._start_point)
        start_angle = (self._start_point - self._center_point).angle_radians
        end_angle = (self._end_point - self._center_point).angle_radians
        self.arc = Arc(self._center_point, radius, start_angle, end_angle)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the arc."""
        return self.arc.get_bounds()

    @property
    def center_point(self) -> Point2D:
        """Get the center point."""
        return self._center_point
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point."""
        value = Point2D(value)
        delta = value - self._center_point
        self._center_point = value
        self._start_point += delta
        self._end_point += delta
        self._update_arc()

    @property
    def start_point(self) -> Point2D:
        """Get the start point."""
        return self._start_point
    
    @start_point.setter
    def start_point(self, value: Point2D):
        """Set the start point."""
        self._start_point = Point2D(value)
        self._update_arc()

    @property
    def end_point(self) -> Point2D:
        """Get the end point."""
        return self._end_point
    
    @end_point.setter
    def end_point(self, value: Point2D):
        """Set the end point."""
        self._end_point = Point2D(value)
        self._update_arc()

    @property
    def radius(self) -> float:
        """Get the radius of the arc."""
        return self.arc.radius
    
    @radius.setter
    def radius(self, value: float):
        """Set the radius by moving start and end points."""
        start_angle = (self._start_point - self._center_point).angle_radians
        end_angle = (self._end_point - self._center_point).angle_radians
        self._start_point = self._center_point + Point2D(value, angle=start_angle)
        self._end_point = self._center_point + Point2D(value, angle=end_angle)
        self._update_arc()

    @property
    def start_angle(self) -> float:
        """Get the start angle in radians."""
        return self.arc.start_angle
    
    @start_angle.setter
    def start_angle(self, value: float):
        """Set the start angle by moving the start point."""
        radius = self._center_point.distance_to(self._start_point)
        self._start_point = self._center_point + Point2D(radius, angle=value)
        self._update_arc()

    @property
    def end_angle(self) -> float:
        """Get the end angle in radians."""
        return self.arc.end_angle
    
    @end_angle.setter
    def end_angle(self, value: float):
        """Set the end angle by moving the end point."""
        radius = self._center_point.distance_to(self._end_point)
        self._end_point = self._center_point + Point2D(radius, angle=value)
        self._update_arc()

    @property
    def span_angle(self) -> float:
        """Get the span angle in radians."""
        return self.arc.end_angle - self.arc.start_angle
    
    @span_angle.setter
    def span_angle(self, value: float):
        """Set the span angle by adjusting the end angle."""
        self.end_angle = self.start_angle + value

    def translate(self, dx: float, dy: float):
        """Move all points by the specified offset."""
        self.arc.translate(Point2D(dx, dy))
        self._center_point.translate(Point2D(dx, dy))
        self._start_point.translate(Point2D(dx, dy))
        self._end_point.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the arc by the specified factor around the center point."""
        self.arc.scale(scale, center)
        self._center_point.scale(scale, center)
        self._start_point.scale(scale, center)
        self._end_point.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the arc by the specified angle around the center point."""
        self.arc.rotate(angle, center)
        self._center_point.rotate(angle, center)
        self._start_point.rotate(angle, center)
        self._end_point.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the arc by the given transform."""
        self.arc.transform(transform)
        self._center_point.transform(transform)
        self._start_point.transform(transform)
        self._end_point.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the arc contains the given point."""
        return self.arc.contains_point(point, tolerance)

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the arc into simpler objects."""
        return self.arc.decompose(into)

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this arc."""
        # Create constraint points
        center_cp = ConstrainablePoint2D(solver, (self._center_point.x, self._center_point.y), fixed=False)
        start_cp = ConstrainablePoint2D(solver, (self._start_point.x, self._start_point.y), fixed=False)
        end_cp = ConstrainablePoint2D(solver, (self._end_point.x, self._end_point.y), fixed=False)
        
        # Store constraint objects for later updates
        self.constraint_center = center_cp
        self.constraint_start = start_cp
        self.constraint_end = end_cp

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_center'):
            # Update the constrainable points with current arc points
            self.constraint_center.update_values(self._center_point.x, self._center_point.y)
            self.constraint_start.update_values(self._start_point.x, self._start_point.y)
            self.constraint_end.update_values(self._end_point.x, self._end_point.y)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        # Get updated coordinates from constraints
        center_x, center_y = self.constraint_center.get(solver.variables)
        start_x, start_y = self.constraint_start.get(solver.variables)
        end_x, end_y = self.constraint_end.get(solver.variables)
        
        # Update the stored points
        self._center_point = Point2D(center_x, center_y)
        self._start_point = Point2D(start_x, start_y)
        self._end_point = Point2D(end_x, end_y)
        
        # Update the arc geometry
        self._update_arc()

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_center'):
            return [
                ("center", self.constraint_center),
                ("start", self.constraint_start),
                ("end", self.constraint_end)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["center_point"] = self._center_point.to_string()
        data["start_point"] = self._start_point.to_string()
        data["end_point"] = self._end_point.to_string()
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'ArcCadObject':
        """Create an arc object from serialized data."""
        center_point = Point2D(*data["center_point"])
        start_point = Point2D(*data["start_point"])
        end_point = Point2D(*data["end_point"])
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, center_point, start_point, end_point, color, line_width)

