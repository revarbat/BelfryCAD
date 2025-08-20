"""
EllipseCadObject - An ellipse CAD object defined by center point and two radius points.
"""

import numpy as np
from typing import Optional, Tuple, List, TYPE_CHECKING

from ..cad_object import CadObject
from ...cad_geometry import Point2D, Ellipse, Transform2D, ShapeType, Shape2D
from ...utils.constraints import (
    ConstraintSolver,
    ConstrainablePoint2D,
    ConstrainableEllipse,
    Constrainable,
)

if TYPE_CHECKING:
    from ...models.document import Document


class EllipseCadObject(CadObject):
    """An ellipse CAD object defined by center point, major axis point, and minor axis point."""

    def __init__(
            self,
            document: 'Document',
            center_point: Point2D,
            major_axis_point: Point2D,
            minor_axis_point: Point2D,
            color: str = "black",
            line_width: Optional[float] = 0.05
    ):
        super().__init__(document, color, line_width)
        self._center_point = center_point
        self._major_axis_point = major_axis_point
        self._minor_axis_point = minor_axis_point
        self._update_ellipse()

    def _update_ellipse(self):
        """Update the ellipse geometry from the current points."""
        major_axis = self._center_point.distance_to(self._major_axis_point)
        minor_axis = self._center_point.distance_to(self._minor_axis_point)
        rotation = (self._major_axis_point - self._center_point).angle_radians
        self.ellipse = Ellipse(self._center_point, major_axis, minor_axis, rotation)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounds of the ellipse."""
        return self.ellipse.get_bounds()

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
        self._major_axis_point += delta
        self._minor_axis_point += delta
        self._update_ellipse()

    @property
    def major_axis_point(self) -> Point2D:
        """Get the major axis point."""
        return self._major_axis_point
    
    @major_axis_point.setter
    def major_axis_point(self, value: Point2D):
        """Set the major axis point."""
        self._major_axis_point = Point2D(value)
        self._update_ellipse()

    @property
    def minor_axis_point(self) -> Point2D:
        """Get the minor axis point."""
        return self._minor_axis_point
    
    @minor_axis_point.setter
    def minor_axis_point(self, value: Point2D):
        """Set the minor axis point."""
        self._minor_axis_point = Point2D(value)
        self._update_ellipse()

    @property
    def major_axis(self) -> float:
        """Get the major axis length."""
        return self.ellipse.major_axis
    
    @major_axis.setter
    def major_axis(self, value: float):
        """Set the major axis length by moving the major axis point."""
        angle = (self._major_axis_point - self._center_point).angle_radians
        self._major_axis_point = self._center_point + Point2D(value, angle=angle)
        self._update_ellipse()

    @property
    def minor_axis(self) -> float:
        """Get the minor axis length."""
        return self.ellipse.minor_axis
    
    @minor_axis.setter
    def minor_axis(self, value: float):
        """Set the minor axis length by moving the minor axis point."""
        angle = (self._minor_axis_point - self._center_point).angle_radians
        self._minor_axis_point = self._center_point + Point2D(value, angle=angle)
        self._update_ellipse()

    @property
    def rotation(self) -> float:
        """Get the rotation angle in radians."""
        return self.ellipse.rotation
    
    @rotation.setter
    def rotation(self, value: float):
        """Set the rotation angle by moving the major axis point."""
        major_axis = self._center_point.distance_to(self._major_axis_point)
        self._major_axis_point = self._center_point + Point2D(major_axis, angle=value)
        self._update_ellipse()

    @property
    def rotation_degrees(self) -> float:
        """Get the rotation angle in degrees."""
        return self.ellipse.rotation_degrees
    
    @rotation_degrees.setter
    def rotation_degrees(self, value: float):
        """Set the rotation angle in degrees."""
        self.rotation = np.radians(value)

    @property
    def focus1(self) -> Point2D:
        """Get the first focus point."""
        return self.ellipse.get_foci()[0]
    
    @focus1.setter
    def focus1(self, value: Point2D):
        """Set the first focus point by updating the ellipse parameters."""
        value = Point2D(value)
        focus2 = self.ellipse.get_foci()[1]
        
        # Calculate new center as midpoint of foci
        new_center = (value + focus2) / 2
        
        # Calculate focal distance
        focal_distance = value.distance_to(focus2) / 2
        
        # Calculate major axis length (sum of distances from foci to any point on ellipse)
        # For simplicity, use the current major axis length
        major_axis_length = self.major_axis
        
        # Create new ellipse from foci
        self.ellipse = Ellipse.from_foci(value, focus2, major_axis_length)
        
        # Update internal points
        self._center_point = self.ellipse.center
        self._major_axis_point = self._center_point + Point2D(self.ellipse.major_axis / 2, angle=self.ellipse.rotation)
        self._minor_axis_point = self._center_point + Point2D(self.ellipse.minor_axis / 2, angle=self.ellipse.rotation + np.pi/2)

    @property
    def focus2(self) -> Point2D:
        """Get the second focus point."""
        return self.ellipse.get_foci()[1]
    
    @focus2.setter
    def focus2(self, value: Point2D):
        """Set the second focus point by updating the ellipse parameters."""
        value = Point2D(value)
        focus1 = self.ellipse.get_foci()[0]
        
        # Calculate new center as midpoint of foci
        new_center = (focus1 + value) / 2
        
        # Calculate focal distance
        focal_distance = focus1.distance_to(value) / 2
        
        # Calculate major axis length (sum of distances from foci to any point on ellipse)
        # For simplicity, use the current major axis length
        major_axis_length = self.major_axis
        
        # Create new ellipse from foci
        self.ellipse = Ellipse.from_foci(focus1, value, major_axis_length)
        
        # Update internal points
        self._center_point = self.ellipse.center
        self._major_axis_point = self._center_point + Point2D(self.ellipse.major_axis / 2, angle=self.ellipse.rotation)
        self._minor_axis_point = self._center_point + Point2D(self.ellipse.minor_axis / 2, angle=self.ellipse.rotation + np.pi/2)

    def translate(self, dx: float, dy: float):
        """Move all points by the specified offset."""
        self.ellipse.translate(Point2D(dx, dy))
        self._center_point.translate(Point2D(dx, dy))
        self._major_axis_point.translate(Point2D(dx, dy))
        self._minor_axis_point.translate(Point2D(dx, dy))

    def scale(self, scale: float, center: Point2D):
        """Scale the ellipse by the specified factor around the center point."""
        self.ellipse.scale(scale, center)
        self._center_point.scale(scale, center)
        self._major_axis_point.scale(scale, center)
        self._minor_axis_point.scale(scale, center)

    def rotate(self, angle: float, center: Point2D):
        """Rotate the ellipse by the specified angle around the center point."""
        self.ellipse.rotate(angle, center)
        self._center_point.rotate(angle, center)
        self._major_axis_point.rotate(angle, center)
        self._minor_axis_point.rotate(angle, center)

    def transform(self, transform: Transform2D):
        """Transform the ellipse by the given transform."""
        self.ellipse.transform(transform)
        self._center_point.transform(transform)
        self._major_axis_point.transform(transform)
        self._minor_axis_point.transform(transform)

    def contains_point(self, point: Point2D, tolerance: float = 5.0) -> bool:
        """Check if the ellipse contains the given point."""
        closest_point = self.ellipse.closest_point_to(point)
        return point.distance_to(closest_point) <= tolerance

    def decompose(self, into: List[ShapeType] = []) -> List[Shape2D]:
        """Decompose the ellipse into simpler objects."""
        return [self.ellipse]

    def make_constrainables(self, solver: ConstraintSolver):
        """Setup constraints for this ellipse."""
        # Create constraint points
        center_cp = ConstrainablePoint2D(solver, (self._center_point.x, self._center_point.y), fixed=False)
        major_cp = ConstrainablePoint2D(solver, (self._major_axis_point.x, self._major_axis_point.y), fixed=False)
        minor_cp = ConstrainablePoint2D(solver, (self._minor_axis_point.x, self._minor_axis_point.y), fixed=False)
        
        # Store constraint objects for later updates
        self.constraint_center = center_cp
        self.constraint_major = major_cp
        self.constraint_minor = minor_cp

    def update_constrainables_before_solving(self, solver: ConstraintSolver):
        """Update constrainables with current object values before solving."""
        if hasattr(self, 'constraint_center'):
            # Update the constrainable points with current ellipse points
            self.constraint_center.update_values(self._center_point.x, self._center_point.y)
            self.constraint_major.update_values(self._major_axis_point.x, self._major_axis_point.y)
            self.constraint_minor.update_values(self._minor_axis_point.x, self._minor_axis_point.y)

    def update_from_solved_constraints(self, solver: ConstraintSolver):
        """Update object from constraints."""
        # Get updated coordinates from constraints
        center_x, center_y = self.constraint_center.get(solver.variables)
        major_x, major_y = self.constraint_major.get(solver.variables)
        minor_x, minor_y = self.constraint_minor.get(solver.variables)
        
        # Update the stored points
        self._center_point = Point2D(center_x, center_y)
        self._major_axis_point = Point2D(major_x, major_y)
        self._minor_axis_point = Point2D(minor_x, minor_y)
        
        # Update the ellipse geometry
        self._update_ellipse()

    def get_constrainables(self) -> List[Tuple[str, Constrainable]]:
        """Get list of constrainables for this object."""
        if hasattr(self, 'constraint_center'):
            return [
                ("center", self.constraint_center),
                ("major_axis", self.constraint_major),
                ("minor_axis", self.constraint_minor)
            ]
        return []

    def get_object_data(self) -> dict:
        """Get the data needed to re-create this object."""
        data = {}
        data["center_point"] = self._center_point.to_string()
        data["major_axis_point"] = self._major_axis_point.to_string()
        data["minor_axis_point"] = self._minor_axis_point.to_string()
        return data

    @classmethod
    def create_object_from_data(cls, document: 'Document', obj_type: str, data: dict) -> 'EllipseCadObject':
        """Create an ellipse object from serialized data."""
        center_point = Point2D(*data["center_point"])
        major_axis_point = Point2D(*data["major_axis_point"])
        minor_axis_point = Point2D(*data["minor_axis_point"])
        color = data.get("color", "black")
        line_width = data.get("line_width", 0.05)
        
        return cls(document, center_point, major_axis_point, minor_axis_point, color, line_width) 