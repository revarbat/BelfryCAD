"""
RectangleCadObject - A rectangle CAD object defined by corner points.
"""

from typing import Optional, Tuple, List, TYPE_CHECKING

from ...cad_geometry import (
    ShapeType, Shape2D, Transform2D,
    Point2D, Rect,
)
from ..cad_object import CadObject
from ...utils.constraints import (
    ConstraintSolver, Constrainable,
    ConstrainablePoint2D, ConstrainableLength,
)

if TYPE_CHECKING:
    from ...models.document import Document


class RectangleCadObject(CadObject):
    """A rectangle CAD object defined by corner points, width, and height."""

    def __init__(
            self,
            document: 'Document',
            corner1: Point2D,
            corner2: Point2D,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        # Create rect from two diagonal corners
        x1, y1 = min(corner1.x, corner2.x), min(corner1.y, corner2.y)
        x2, y2 = max(corner1.x, corner2.x), max(corner1.y, corner2.y)
        self.rect = Rect(x1, y1, x2 - x1, y2 - y1)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the rectangle."""
        return self.rect.get_bounds()

    @property
    def corner1(self) -> Point2D:
        """Get the bottom-left corner point."""
        return Point2D(self.rect.left, self.rect.bottom)
    
    @corner1.setter
    def corner1(self, value: Point2D):
        """Set the bottom-left corner point."""
        point = Point2D(value)
        delta = point - self.corner1
        self.rect.left += delta.x
        self.rect.bottom += delta.y
        self.rect.width -= delta.x
        self.rect.height -= delta.y

    @property
    def corner2(self) -> Point2D:
        """Get the bottom-left corner point."""
        return Point2D(self.rect.left, self.rect.top)
    
    @corner2.setter
    def corner2(self, value: Point2D):
        """Set the bottom-left corner point."""
        point = Point2D(value)
        delta = point - self.corner2
        self.rect.left += delta.x
        self.rect.width -= delta.x
        self.rect.height += delta.y

    @property
    def corner3(self) -> Point2D:
        """Get the top-right corner point."""
        return Point2D(self.rect.right, self.rect.top)
    
    @corner3.setter
    def corner3(self, value: Point2D):
        """Set the top-right corner point, adjusting width and height."""
        point = Point2D(value)
        delta = point - self.corner3
        self.rect.width += delta.x
        self.rect.height += delta.y

    @property
    def corner4(self) -> Point2D:
        """Get the top-right corner point."""
        return Point2D(self.rect.right, self.rect.bottom)
    
    @corner4.setter
    def corner4(self, value: Point2D):
        """Set the top-right corner point, adjusting width and height."""
        point = Point2D(value)
        delta = point - self.corner4
        self.rect.bottom += delta.y
        self.rect.width += delta.x
        self.rect.height -= delta.y

    @property
    def width(self) -> float:
        """Get the width of the rectangle."""
        return self.rect.width
    
    @width.setter
    def width(self, value: float):
        """Set the width of the rectangle."""
        self.rect.width = float(value)

    @property
    def height(self) -> float:
        """Get the height of the rectangle."""
        return self.rect.height
    
    @height.setter
    def height(self, value: float):
        """Set the height of the rectangle."""
        self.rect.height = float(value)

    @property
    def center_point(self) -> Point2D:
        """Get the center point of the rectangle."""
        return self.rect.center
    
    @center_point.setter
    def center_point(self, value: Point2D):
        """Set the center point of the rectangle."""
        point = Point2D(value)
        self.rect.left = point.x - self.rect.width / 2
        self.rect.bottom = point.y - self.rect.height / 2

    @property
    def corners(self) -> Tuple[Point2D, Point2D, Point2D, Point2D]:
        """Get all four corner points (bottom-left, bottom-right, top-right, top-left)."""
        return (
            Point2D(self.rect.left, self.rect.bottom),
            Point2D(self.rect.right, self.rect.bottom),
            Point2D(self.rect.right, self.rect.top),
            Point2D(self.rect.left, self.rect.top)
        )

    def translate(self, dx: float, dy: float):
        """Move the rectangle by the specified offset."""
        self.rect = self.rect.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the rectangle by the specified factor around the center point."""
        self.rect = self.rect.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the rectangle by the specified angle around the center point."""
        # Note: Rotation of a rectangle returns a polygon
        return self.rect.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the rectangle by the specified transform."""
        # Note: General transformation of a rectangle returns a polygon
        return self.rect.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the rectangle contains the given point."""
        return self.rect.contains_point(point, tolerance)

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the rectangle into simpler objects."""
        return self.rect.decompose(into)

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for the rectangle."""
        corner = ConstrainablePoint2D(solver, (self.rect.left, self.rect.bottom), fixed=False)
        width = ConstrainableLength(solver, self.rect.width, fixed=False)
        height = ConstrainableLength(solver, self.rect.height, fixed=False)
        
        self.constraint_corner = corner
        self.constraint_width = width
        self.constraint_height = height

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_corner'):
            # Update the constrainable corner point with current corner
            self.constraint_corner.update_values(self.rect.left, self.rect.bottom)
            # Update the constrainable width and height
            self.constraint_width.update_value(self.rect.width)
            self.constraint_height.update_value(self.rect.height)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        if hasattr(self, 'constraint_corner'):
            cx, cy = self.constraint_corner.get(solver.variables)
            width = self.constraint_width.get(solver.variables)
            height = self.constraint_height.get(solver.variables)
            
            self.rect.left = cx
            self.rect.bottom = cy
            self.rect.width = width
            self.rect.height = height

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_corner'):
            return [
                ("corner", self.constraint_corner),
                ("width", self.constraint_width),
                ("height", self.constraint_height),
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the object data."""
        return {
            "corner1": (self.corner1.x, self.corner1.y),
            "corner2": (self.corner3.x, self.corner3.y),
        }

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'RectangleCadObject':
        """Create a rectangle object from the given data."""
        corner1 = Point2D(*data["corner1"])
        corner2 = Point2D(*data["corner2"])
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(
            document=document,
            corner1=corner1,
            corner2=corner2,
            color=color,
            line_width=line_width
        ) 