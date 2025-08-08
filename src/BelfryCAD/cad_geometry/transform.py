"""
2D Transform Matrix for CAD Geometry

This module provides the Transform2D class for handling 2D transformations
including translation, rotation, scaling, and general matrix operations.
"""

import numpy as np
from typing import Optional, List, Tuple
from .point import Point2D

EPSILON = 1e-10


class Transform2D:
    """
    A 2D transformation matrix for CAD geometry operations.
    
    The transformation matrix is stored as a 3x3 homogeneous matrix:
    [a  b  tx]
    [c  d  ty]
    [0  0   1]
    
    Where (a,b,c,d) form the 2x2 linear transformation and (tx,ty) is the translation.
    """

    def __init__(self, matrix: Optional[np.ndarray] = None):
        """
        Initialize a 2D transformation.
        
        Args:
            matrix: Optional 3x3 homogeneous transformation matrix.
                   If None, creates an identity transformation.
        """
        if matrix is None:
            self.matrix = np.eye(3, dtype=np.float64)
        else:
            if matrix.shape != (3, 3):
                raise ValueError("Transform matrix must be 3x3")
            self.matrix = matrix.astype(np.float64)

    def __repr__(self) -> str:
        return f"Transform2D(matrix=\n{self.matrix})"

    def __str__(self) -> str:
        return f"Transform2D(\n{self.matrix})"

    def __mul__(self, other: 'Transform2D') -> 'Transform2D':
        """Matrix multiplication of transformations."""
        return Transform2D(self.matrix @ other.matrix)

    def __matmul__(self, other: 'Transform2D') -> 'Transform2D':
        """Matrix multiplication of transformations."""
        return Transform2D(self.matrix @ other.matrix)

    def __rmatmul__(self, other: 'Transform2D') -> 'Transform2D':
        """Matrix multiplication of transformations."""
        return Transform2D(other.matrix @ self.matrix)

    def __eq__(self, other) -> bool:
        """Check if two transformations are equal."""
        if not isinstance(other, Transform2D):
            return False
        return np.allclose(self.matrix, other.matrix, atol=EPSILON)

    @property
    def is_identity(self) -> bool:
        """Check if this is an identity transformation."""
        return np.allclose(self.matrix, np.eye(3), atol=EPSILON)

    @property
    def determinant(self) -> float:
        """Get the determinant of the 2x2 linear transformation part."""
        return self.matrix[0, 0] * self.matrix[1, 1] - self.matrix[0, 1] * self.matrix[1, 0]

    @property
    def is_invertible(self) -> bool:
        """Check if the transformation is invertible."""
        return abs(self.determinant) > EPSILON

    def inverse(self) -> 'Transform2D':
        """Get the inverse transformation."""
        if not self.is_invertible:
            raise ValueError("Cannot invert singular transformation")
        
        # Invert the 2x2 linear part
        det = self.determinant
        a, b, c, d = self.matrix[0, 0], self.matrix[0, 1], self.matrix[1, 0], self.matrix[1, 1]
        tx, ty = self.matrix[0, 2], self.matrix[1, 2]
        
        inv_matrix = np.array([
            [d, -b, -d*tx + b*ty],
            [-c, a, c*tx - a*ty],
            [0, 0, det]
        ]) / det
        
        return Transform2D(inv_matrix)

    def transform_point(self, point: 'Point2D') -> 'Point2D':
        """
        Transform a point using this transformation.
        
        Args:
            point: The point to transform
            
        Returns:
            The transformed point
        """
        # Convert to homogeneous coordinates
        homogeneous = np.array([point.x, point.y, 1.0])
        
        # Apply transformation
        transformed = self.matrix @ homogeneous
        
        # Convert back to 2D coordinates
        return Point2D(transformed[0], transformed[1])

    def transform_points(self, points: List['Point2D']) -> List['Point2D']:
        """
        Transform multiple points using this transformation.
        
        Args:
            points: List of points to transform
            
        Returns:
            List of transformed points
        """
        if not points:
            return []
        
        # Convert to homogeneous coordinates
        homogeneous = np.array([[p.x, p.y, 1.0] for p in points])
        
        # Apply transformation to all points at once
        transformed = (self.matrix @ homogeneous.T).T
        
        # Convert back to Point2D objects
        return [Point2D(row[0], row[1]) for row in transformed]

    @classmethod
    def identity(cls) -> 'Transform2D':
        """Create an identity transformation."""
        return cls()

    @classmethod
    def translation(cls, tx: float, ty: float) -> 'Transform2D':
        """
        Create a translation transformation.
        
        Args:
            tx: Translation in x direction
            ty: Translation in y direction
            
        Returns:
            Translation transformation
        """
        matrix = np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])
        return cls(matrix)

    @classmethod
    def rotation(cls, angle: float, center: Optional['Point2D'] = None) -> 'Transform2D':
        """
        Create a rotation transformation.
        
        Args:
            angle: Rotation angle in radians
            center: Center of rotation (defaults to origin)
            
        Returns:
            Rotation transformation
        """
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        
        if center is None:
            # Rotation around origin
            matrix = np.array([
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1]
            ])
        else:
            # Rotation around center point
            cx, cy = center.x, center.y
            matrix = np.array([
                [cos_a, -sin_a, cx - cx*cos_a + cy*sin_a],
                [sin_a, cos_a, cy - cx*sin_a - cy*cos_a],
                [0, 0, 1]
            ])
        
        return cls(matrix)

    @classmethod
    def scaling(cls, sx: float, sy: Optional[float] = None, center: Optional['Point2D'] = None) -> 'Transform2D':
        """
        Create a scaling transformation.
        
        Args:
            sx: Scale factor in x direction
            sy: Scale factor in y direction (defaults to sx)
            center: Center of scaling (defaults to origin)
            
        Returns:
            Scaling transformation
        """
        if sy is None:
            sy = sx
        
        if center is None:
            # Scaling from origin
            matrix = np.array([
                [sx, 0, 0],
                [0, sy, 0],
                [0, 0, 1]
            ])
        else:
            # Scaling from center point
            cx, cy = center.x, center.y
            matrix = np.array([
                [sx, 0, cx - sx*cx],
                [0, sy, cy - sy*cy],
                [0, 0, 1]
            ])
        
        return cls(matrix)

    @classmethod
    def from_points(cls, src_points: List['Point2D'], dst_points: List['Point2D']) -> 'Transform2D':
        """
        Create a transformation that maps source points to destination points.
        
        This uses least squares to find the best affine transformation.
        
        Args:
            src_points: Source points
            dst_points: Destination points
            
        Returns:
            Transformation that approximately maps src_points to dst_points
        """
        if len(src_points) != len(dst_points):
            raise ValueError("Source and destination point lists must have same length")
        
        if len(src_points) < 3:
            raise ValueError("Need at least 3 points to determine transformation")
        
        # Convert to numpy arrays
        src_array = np.array([[p.x, p.y] for p in src_points])
        dst_array = np.array([[p.x, p.y] for p in dst_points])
        
        # Add homogeneous coordinate
        src_homog = np.column_stack([src_array, np.ones(len(src_points))])
        
        # Solve least squares problem: dst = src @ transform_matrix
        # We need to solve for the 2x3 transformation matrix
        transform_matrix, residuals, rank, s = np.linalg.lstsq(src_homog, dst_array, rcond=None)
        
        # Convert to 3x3 homogeneous matrix
        matrix = np.eye(3)
        matrix[:2, :] = transform_matrix.T
        
        return cls(matrix) 