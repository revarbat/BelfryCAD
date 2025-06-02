#!/usr/bin/env python3

"""
Matrix Math Utilities

This module provides matrix and vector math operations for 2D and 3D
transformations, translated from the original TCL implementation.
Uses numpy for efficient matrix operations.

Main classes:
    Matrix: Object-oriented matrix operations for 2D and 3D transformations
    Vector: Vector operations and utilities

Legacy functions are maintained for backward compatibility.
"""

import numpy as np
import math
from typing import List, Union, Optional, Tuple


##################################################################
# Matrix Class
##################################################################

class Matrix:
    """
    Object-oriented matrix class for 2D and 3D transformations.

    This class provides a clean API for matrix operations and transformations,
    wrapping numpy arrays with convenient methods for graphics transformations.
    """

    def __init__(
        self,
        data: Optional[
            Union[
                np.ndarray,
                List[List[float]]
            ]
        ] = None,
        dimension: int = 2
    ):
        """
        Initialize a matrix.

        Args:
            data: Matrix data as numpy array or nested list.
                  If None, creates identity matrix.
            dimension: Dimension (2 for 2D, 3 for 3D transformations)
        """
        if data is None:
            if dimension == 2:
                self._matrix = self._identity_2d()
            elif dimension == 3:
                self._matrix = self._identity_3d()
            else:
                raise ValueError("Dimension must be 2 or 3")
        elif isinstance(data, np.ndarray):
            self._matrix = data.copy()
        else:
            self._matrix = np.array(data, dtype=float)

    @property
    def data(self) -> np.ndarray:
        """Get the underlying numpy array."""
        return self._matrix

    @property
    def shape(self) -> Tuple[int, int]:
        """Get matrix shape."""
        return self._matrix.shape

    @property
    def is_2d(self) -> bool:
        """Check if this is a 2D transformation matrix (3x3)."""
        return self.shape == (3, 3)

    @property
    def is_3d(self) -> bool:
        """Check if this is a 3D transformation matrix (4x4)."""
        return self.shape == (4, 4)

    def __str__(self) -> str:
        """String representation of the matrix."""
        return str(self._matrix)

    def __repr__(self) -> str:
        """Representation of the matrix."""
        return f"Matrix({self._matrix.tolist()})"

    def __mul__(self, other: 'Matrix') -> 'Matrix':
        """Matrix multiplication operator."""
        if not isinstance(other, Matrix):
            raise TypeError("Can only multiply with another Matrix")
        return Matrix(np.dot(self._matrix, other._matrix))

    def __eq__(self, other: 'Matrix') -> bool:
        """Equality comparison."""
        if not isinstance(other, Matrix):
            return False
        return np.allclose(self._matrix, other._matrix)

    @staticmethod
    def _identity_2d() -> np.ndarray:
        """Create 2D identity matrix."""
        return np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

    @staticmethod
    def _identity_3d() -> np.ndarray:
        """Create 3D identity matrix."""
        return np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])

    @classmethod
    def identity(cls, dimension: int = 2) -> 'Matrix':
        """
        Create an identity transformation matrix.

        Args:
            dimension: 2 for 2D (3x3), 3 for 3D (4x4)

        Returns:
            Identity matrix
        """
        return cls(dimension=dimension)

    @classmethod
    def translate(cls, dx: float, dy: float,
                  dz: Optional[float] = None) -> 'Matrix':
        """
        Create a translation matrix.

        Args:
            dx: Translation in x direction
            dy: Translation in y direction
            dz: Translation in z direction (for 3D)

        Returns:
            Translation matrix
        """
        if dz is None:
            # 2D translation
            return cls(np.array([
                [1.0, 0.0, dx],
                [0.0, 1.0, dy],
                [0.0, 0.0, 1.0]
            ]))
        else:
            # 3D translation
            return cls(np.array([
                [1.0, 0.0, 0.0, dx],
                [0.0, 1.0, 0.0, dy],
                [0.0, 0.0, 1.0, dz],
                [0.0, 0.0, 0.0, 1.0]
            ]))

    @classmethod
    def scale(cls, sx: float, sy: float, sz: Optional[float] = None,
              cx: float = 0.0, cy: float = 0.0, cz: float = 0.0
              ) -> 'Matrix':
        """
        Create a scaling matrix with optional center point.

        Args:
            sx: Scale factor in x direction
            sy: Scale factor in y direction
            sz: Scale factor in z direction (for 3D)
            cx: Center point x coordinate
            cy: Center point y coordinate
            cz: Center point z coordinate

        Returns:
            Scaling matrix
        """
        if sz is None:
            # 2D scaling
            return cls(np.array([
                [sx, 0.0, cx - sx * cx],
                [0.0, sy, cy - sy * cy],
                [0.0, 0.0, 1.0]
            ]))
        else:
            # 3D scaling
            return cls(np.array([
                [sx, 0.0, 0.0, cx - sx * cx],
                [0.0, sy, 0.0, cy - sy * cy],
                [0.0, 0.0, sz, cz - sz * cz],
                [0.0, 0.0, 0.0, 1.0]
            ]))

    @classmethod
    def rotate(cls, angle: float, cx: float = 0.0, cy: float = 0.0,
               axis: Optional[List[float]] = None) -> 'Matrix':
        """
        Create a rotation matrix.

        Args:
            angle: Rotation angle in degrees
            cx: Center point x coordinate (2D only)
            cy: Center point y coordinate (2D only)
            axis: Rotation axis vector [x, y, z] (3D only)

        Returns:
            Rotation matrix
        """
        if axis is None:
            # 2D rotation
            ang_rad = math.radians(angle)
            cos_ang = math.cos(ang_rad)
            sin_ang = math.sin(ang_rad)

            mat = np.array([
                [cos_ang, -sin_ang, cx],
                [sin_ang, cos_ang, cy],
                [0.0, 0.0, 1.0]
            ])

            # Apply center point transformation
            translate_back = cls.translate(-cx, -cy)
            return cls(mat) * translate_back
        else:
            # 3D rotation around arbitrary axis
            ang_rad = math.radians(angle)

            x, y, z = vector_normalize(axis)
            cosv = math.cos(ang_rad)
            sinv = math.sin(ang_rad)
            cos1m = 1.0 - cosv

            return cls(np.array([
                [cosv + cos1m * x * x,
                 cos1m * x * y - sinv * z,
                 cos1m * x * z + sinv * y, 0.0],
                [cos1m * y * x + sinv * z,
                 cosv + cos1m * y * y,
                 cos1m * y * z - sinv * x, 0.0],
                [cos1m * z * x - sinv * y,
                 cos1m * z * y + sinv * x,
                 cosv + cos1m * z * z, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ]))

    @classmethod
    def skew_x(cls, angle: float, cx: float = 0.0,
               cy: float = 0.0) -> 'Matrix':
        """
        Create a 2D skew matrix for X axis.

        Args:
            angle: Skew angle in degrees
            cx: Center point x coordinate
            cy: Center point y coordinate

        Returns:
            Skew matrix
        """
        ang_rad = math.radians(angle)
        tan_ang = math.tan(ang_rad)

        mat = np.array([
            [1.0, tan_ang, cx],
            [0.0, 1.0, cy],
            [0.0, 0.0, 1.0]
        ])

        translate_back = cls.translate(-cx, -cy)
        return cls(mat) * translate_back

    @classmethod
    def skew_y(cls, angle: float, cx: float = 0.0,
               cy: float = 0.0) -> 'Matrix':
        """
        Create a 2D skew matrix for Y axis.

        Args:
            angle: Skew angle in degrees
            cx: Center point x coordinate
            cy: Center point y coordinate

        Returns:
            Skew matrix
        """
        ang_rad = math.radians(angle)
        tan_ang = math.tan(ang_rad)

        mat = np.array([
            [1.0, 0.0, cx],
            [tan_ang, 1.0, cy],
            [0.0, 0.0, 1.0]
        ])

        translate_back = cls.translate(-cx, -cy)
        return cls(mat) * translate_back

    def transpose(self) -> 'Matrix':
        """
        Return the transpose of this matrix.

        Returns:
            Transposed matrix
        """
        return Matrix(self._matrix.T)

    def transform_coords(self, coords: List[float]) -> List[float]:
        """
        Transform a list of coordinates using this matrix.

        Args:
            coords: List of coordinates [x1, y1, x2, y2, ...] for 2D
                   or [x1, y1, z1, x2, y2, z2, ...] for 3D

        Returns:
            List of transformed coordinates
        """
        if self.is_2d:
            return self._transform_coords_2d(coords)
        elif self.is_3d:
            return self._transform_coords_3d(coords)
        else:
            raise ValueError("Matrix must be 3x3 (2D) or 4x4 (3D)")

    def _transform_coords_2d(self, coords: List[float]) -> List[float]:
        """Transform 2D coordinates."""
        outcoords = []
        for i in range(0, len(coords), 2):
            x, y = coords[i], coords[i + 1]
            nx = (self._matrix[0, 0] * x + self._matrix[0, 1] * y +
                  self._matrix[0, 2])
            ny = (self._matrix[1, 0] * x + self._matrix[1, 1] * y +
                  self._matrix[1, 2])
            outcoords.extend([nx, ny])
        return outcoords

    def _transform_coords_3d(self, coords: List[float]) -> List[float]:
        """Transform 3D coordinates."""
        outcoords = []
        for i in range(0, len(coords), 3):
            x, y, z = coords[i], coords[i + 1], coords[i + 2]
            nx = (self._matrix[0, 0] * x + self._matrix[0, 1] * y +
                  self._matrix[0, 2] * z + self._matrix[0, 3])
            ny = (self._matrix[1, 0] * x + self._matrix[1, 1] * y +
                  self._matrix[1, 2] * z + self._matrix[1, 3])
            nz = (self._matrix[2, 0] * x + self._matrix[2, 1] * y +
                  self._matrix[2, 2] * z + self._matrix[2, 3])
            outcoords.extend([nx, ny, nz])
        return outcoords

    def print(self) -> None:
        """Print the matrix in formatted output."""
        m, n = self._matrix.shape
        for i in range(m):
            row = "["
            for j in range(n):
                row += f" {self._matrix[i, j]:10.5f}"
            row += " ]"
            print(row)


##################################################################
# Vector Class
##################################################################

class Vector:
    """
    Vector class for mathematical operations.
    """

    def __init__(self, components: List[float]):
        """
        Initialize a vector.

        Args:
            components: List of vector components
        """
        self._components = list(components)

    @property
    def components(self) -> List[float]:
        """Get vector components."""
        return self._components.copy()

    @property
    def x(self) -> float:
        """Get x component."""
        return self._components[0] if len(self._components) > 0 else 0.0

    @property
    def y(self) -> float:
        """Get y component."""
        return self._components[1] if len(self._components) > 1 else 0.0

    @property
    def z(self) -> float:
        """Get z component."""
        return self._components[2] if len(self._components) > 2 else 0.0

    def __str__(self) -> str:
        """String representation."""
        return f"Vector({self._components})"

    def __repr__(self) -> str:
        """Representation."""
        return self.__str__()

    def __add__(self, other: 'Vector') -> 'Vector':
        """Vector addition."""
        if not isinstance(other, Vector):
            raise TypeError("Can only add Vector to Vector")
        return Vector([a + b for a, b in
                      zip(self._components, other._components)])

    def __sub__(self, other: 'Vector') -> 'Vector':
        """Vector subtraction."""
        if not isinstance(other, Vector):
            raise TypeError("Can only subtract Vector from Vector")
        return Vector([a - b for a, b in
                      zip(self._components, other._components)])

    def __mul__(self, scalar: float) -> 'Vector':
        """Scalar multiplication."""
        return Vector([scalar * component for component in self._components])

    def __rmul__(self, scalar: float) -> 'Vector':
        """Reverse scalar multiplication."""
        return self.__mul__(scalar)

    def magnitude(self) -> float:
        """Calculate vector magnitude."""
        return math.sqrt(sum(val * val for val in self._components))

    def normalize(self) -> 'Vector':
        """
        Return normalized vector.

        Returns:
            Normalized vector

        Raises:
            ZeroDivisionError: If vector has zero magnitude
        """
        mag = self.magnitude()
        if mag == 0.0:
            raise ZeroDivisionError("Cannot normalize zero-length vector")
        return Vector([val / mag for val in self._components])

    def dot(self, other: 'Vector') -> float:
        """
        Calculate dot product with another vector.

        Args:
            other: Other vector

        Returns:
            Dot product
        """
        return sum(a * b for a, b in zip(self._components, other._components))

    def cross(self, other: 'Vector') -> 'Vector':
        """
        Calculate cross product with another 3D vector.

        Args:
            other: Other 3D vector

        Returns:
            Cross product vector

        Raises:
            ValueError: If vectors are not 3D
        """
        if len(self._components) != 3 or len(other._components) != 3:
            raise ValueError("Cross product requires 3D vectors")

        x1, y1, z1 = self._components
        x2, y2, z2 = other._components

        x = y1 * z2 - z1 * y2
        y = z1 * x2 - x1 * z2
        z = x1 * y2 - y1 * x2

        return Vector([x, y, z])

    def reflect(self, normal: 'Vector') -> 'Vector':
        """
        Reflect this vector across a normal vector.

        Args:
            normal: Normal vector for reflection

        Returns:
            Reflected vector
        """
        numer = self.dot(normal)
        denom = normal.dot(normal)
        mult = 2.0 * numer / denom
        return self - (mult * normal)


##################################################################
# Legacy Functions (for backward compatibility)
##################################################################
# General Matrix math
##################################################################

def matrix_mult(mat1: np.ndarray, mat2: np.ndarray) -> np.ndarray:
    """
    Multiply two matrices.

    Args:
        mat1: First matrix (m x n)
        mat2: Second matrix (n x p)

    Returns:
        Product matrix (m x p)

    Raises:
        ValueError: If matrix dimensions are incompatible
    """
    if mat1.shape[1] != mat2.shape[0]:
        raise ValueError("Columns in mat1 must == rows in mat2")

    return np.dot(mat1, mat2)


def matrix_transpose(mat: np.ndarray) -> np.ndarray:
    """
    Transpose a matrix.

    Args:
        mat: Input matrix

    Returns:
        Transposed matrix
    """
    return mat.T


def matrix_print(mat: np.ndarray) -> None:
    """
    Print a matrix in formatted output.

    Args:
        mat: Matrix to print
    """
    m, n = mat.shape
    for i in range(m):
        row = "["
        for j in range(n):
            row += f" {mat[i, j]:10.5f}"
        row += " ]"
        print(row)


##################################################################
# Matrix 2D math
##################################################################

def matrix_identity() -> np.ndarray:
    """
    Create a 2D identity transformation matrix (3x3).

    Returns:
        3x3 identity matrix
    """
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])


def matrix_translate(dx: float, dy: float) -> np.ndarray:
    """
    Create a 2D translation matrix.

    Args:
        dx: Translation in x direction
        dy: Translation in y direction

    Returns:
        3x3 translation matrix
    """
    return np.array([
        [1.0, 0.0, dx],
        [0.0, 1.0, dy],
        [0.0, 0.0, 1.0]
    ])


def matrix_scale(sx: float, sy: float, cx: float = 0.0,
                 cy: float = 0.0) -> np.ndarray:
    """
    Create a 2D scaling matrix with optional center point.

    Args:
        sx: Scale factor in x direction
        sy: Scale factor in y direction
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)

    Returns:
        3x3 scaling matrix
    """
    return np.array([
        [sx, 0.0, cx - sx * cx],
        [0.0, sy, cy - sy * cy],
        [0.0, 0.0, 1.0]
    ])


def matrix_rotate(ang: float, cx: float = 0.0, cy: float = 0.0) -> np.ndarray:
    """
    Create a 2D rotation matrix with optional center point.

    Args:
        ang: Rotation angle in degrees
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)

    Returns:
        3x3 rotation matrix
    """
    ang_rad = math.radians(ang)
    cos_ang = math.cos(ang_rad)
    sin_ang = math.sin(ang_rad)

    mat = np.array([
        [cos_ang, -sin_ang, cx],
        [sin_ang, cos_ang, cy],
        [0.0, 0.0, 1.0]
    ])

    # Apply center point transformation
    mat = matrix_mult(mat, matrix_translate(-cx, -cy))
    return mat


def matrix_reflect_by_angle(ang: float) -> np.ndarray:
    """
    Create a reflection matrix by angle.

    Args:
        ang: Angle in degrees

    Returns:
        3x3 reflection matrix
    """
    ang_rad = 2.0 * math.radians(ang)
    cos_ang = math.cos(ang_rad)
    sin_ang = math.sin(ang_rad)

    return np.array([
        [cos_ang, sin_ang, 0.0],
        [sin_ang, -cos_ang, 0.0],
        [0.0, 0.0, 1.0]
    ])


def matrix_reflect_line(x0: float, y0: float, x1: float,
                        y1: float) -> np.ndarray:
    """
    Create a reflection matrix across a line.

    Args:
        x0, y0: First point on the line
        x1, y1: Second point on the line

    Returns:
        3x3 reflection matrix
    """
    dx = x1 - x0
    dy = y1 - y0
    dx, dy = vector_normalize([dx, dy])

    mat = np.array([
        [dx * dx - dy * dy, 2.0 * dx * dy, x0],
        [2.0 * dx * dy, dy * dy - dx * dx, y0],
        [0.0, 0.0, 1.0]
    ])

    mat2 = matrix_translate(-x0, -y0)
    return matrix_mult(mat, mat2)


def matrix_skew_xy(skx: float, sky: float, cx: float = 0.0,
                   cy: float = 0.0) -> np.ndarray:
    """
    Create a skew matrix for both X and Y axes.

    Args:
        skx: Skew factor for x
        sky: Skew factor for y
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)

    Returns:
        3x3 skew matrix
    """
    mat = np.array([
        [1.0, skx, cx],
        [sky, 1.0, cy],
        [0.0, 0.0, 1.0]
    ])

    mat2 = matrix_translate(-cx, -cy)
    return matrix_mult(mat, mat2)


def matrix_skew_x(ang: float, cx: float = 0.0, cy: float = 0.0) -> np.ndarray:
    """
    Create a skew matrix for X axis.

    Args:
        ang: Skew angle in degrees
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)

    Returns:
        3x3 skew matrix
    """
    ang_rad = math.radians(ang)
    tan_ang = math.tan(ang_rad)

    mat = np.array([
        [1.0, tan_ang, cx],
        [0.0, 1.0, cy],
        [0.0, 0.0, 1.0]
    ])

    mat2 = matrix_translate(-cx, -cy)
    return matrix_mult(mat, mat2)


def matrix_skew_y(ang: float, cx: float = 0.0, cy: float = 0.0) -> np.ndarray:
    """
    Create a skew matrix for Y axis.

    Args:
        ang: Skew angle in degrees
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)

    Returns:
        3x3 skew matrix
    """
    ang_rad = math.radians(ang)
    tan_ang = math.tan(ang_rad)

    mat = np.array([
        [1.0, 0.0, cx],
        [tan_ang, 1.0, cy],
        [0.0, 0.0, 1.0]
    ])

    mat2 = matrix_translate(-cx, -cy)
    return matrix_mult(mat, mat2)


def matrix_transform(*args) -> np.ndarray:
    """
    Create a transformation matrix from a sequence of operations.

    Args:
        *args: Variable arguments specifying transformations.
               Format: 'operation', param1, param2, ...

    Supported operations:
        - 'translate', dx, dy
        - 'scale', sx, [sy], [cx], [cy]
        - 'rotate', angle, [cx], [cy]
        - 'skewX', angle, [cx], [cy]
        - 'skewY', angle, [cx], [cy]
        - 'skewXY', skx, [sky], [cx], [cy]

    Returns:
        3x3 transformation matrix

    Raises:
        ValueError: For unknown transformation types
    """
    mat = matrix_identity()
    i = 0

    while i < len(args):
        cmd = args[i]
        i += 1

        if cmd == 'translate':
            xoff = args[i]
            i += 1
            yoff = args[i]
            i += 1
            mat2 = matrix_translate(xoff, yoff)

        elif cmd == 'scale':
            scx = args[i]
            i += 1
            scy = scx
            if i < len(args) and isinstance(args[i], (int, float)):
                scy = args[i]
                i += 1
            cx = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cx = args[i]
                i += 1
            cy = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cy = args[i]
                i += 1
            mat2 = matrix_scale(scx, scy, cx, cy)

        elif cmd == 'rotate':
            ang = args[i]
            i += 1
            cx = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cx = args[i]
                i += 1
            cy = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cy = args[i]
                i += 1
            mat2 = matrix_rotate(ang, cx, cy)

        elif cmd == 'skewX':
            ang = args[i]
            i += 1
            cx = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cx = args[i]
                i += 1
            cy = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cy = args[i]
                i += 1
            mat2 = matrix_skew_x(ang, cx, cy)

        elif cmd == 'skewY':
            ang = args[i]
            i += 1
            cx = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cx = args[i]
                i += 1
            cy = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cy = args[i]
                i += 1
            mat2 = matrix_skew_y(ang, cx, cy)

        elif cmd == 'skewXY':
            skx = args[i]
            i += 1
            sky = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                sky = args[i]
                i += 1
            cx = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cx = args[i]
                i += 1
            cy = 0.0
            if i < len(args) and isinstance(args[i], (int, float)):
                cy = args[i]
                i += 1
            mat2 = matrix_skew_xy(skx, sky, cx, cy)

        else:
            raise ValueError(f"Unknown transformation type: {cmd}")

        mat = matrix_mult(mat2, mat)

    return mat


def matrix_transform_coords(mat: np.ndarray,
                            coords: List[float]) -> List[float]:
    """
    Transform a list of 2D coordinates using a transformation matrix.

    Args:
        mat: 3x3 transformation matrix
        coords: List of coordinates [x1, y1, x2, y2, ...]

    Returns:
        List of transformed coordinates
    """
    outcoords = []
    for i in range(0, len(coords), 2):
        x, y = coords[i], coords[i + 1]
        nx = mat[0, 0] * x + mat[0, 1] * y + mat[0, 2]
        ny = mat[1, 0] * x + mat[1, 1] * y + mat[1, 2]
        outcoords.extend([nx, ny])

    return outcoords


##################################################################
# Matrix 3D math
##################################################################

def matrix_3d_identity() -> np.ndarray:
    """
    Create a 3D identity transformation matrix (4x4).

    Returns:
        4x4 identity matrix
    """
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_translate(dx: float, dy: float, dz: float) -> np.ndarray:
    """
    Create a 3D translation matrix.

    Args:
        dx: Translation in x direction
        dy: Translation in y direction
        dz: Translation in z direction

    Returns:
        4x4 translation matrix
    """
    return np.array([
        [1.0, 0.0, 0.0, dx],
        [0.0, 1.0, 0.0, dy],
        [0.0, 0.0, 1.0, dz],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_scale(sx: float, sy: float, sz: float, cx: float = 0.0,
                    cy: float = 0.0, cz: float = 0.0) -> np.ndarray:
    """
    Create a 3D scaling matrix with optional center point.

    Args:
        sx: Scale factor in x direction
        sy: Scale factor in y direction
        sz: Scale factor in z direction
        cx: Center point x coordinate (default: 0.0)
        cy: Center point y coordinate (default: 0.0)
        cz: Center point z coordinate (default: 0.0)

    Returns:
        4x4 scaling matrix
    """
    return np.array([
        [sx, 0.0, 0.0, cx - sx * cx],
        [0.0, sy, 0.0, cy - sy * cy],
        [0.0, 0.0, sz, cz - sz * cz],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_rotate(vect: List[float], ang: float) -> np.ndarray:
    """
    Create a 3D rotation matrix around an arbitrary axis.

    Args:
        vect: Rotation axis vector [x, y, z]
        ang: Rotation angle in degrees

    Returns:
        4x4 rotation matrix
    """
    ang_rad = math.radians(ang)

    x, y, z = vector_normalize(vect)
    cosv = math.cos(ang_rad)
    sinv = math.sin(ang_rad)
    cos1m = 1.0 - cosv

    return np.array([
        [cosv + cos1m * x * x, cos1m * x * y - sinv * z,
         cos1m * x * z + sinv * y, 0.0],
        [cos1m * y * x + sinv * z, cosv + cos1m * y * y,
         cos1m * y * z - sinv * x, 0.0],
        [cos1m * z * x - sinv * y, cos1m * z * y + sinv * x,
         cosv + cos1m * z * z, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_reflect_line(x0: float, y0: float, z0: float,
                           x1: float, y1: float, z1: float) -> np.ndarray:
    """
    Create a 3D reflection matrix across a line.

    Args:
        x0, y0, z0: First point on the line
        x1, y1, z1: Second point on the line

    Returns:
        4x4 reflection matrix
    """
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0
    dx, dy, dz = vector_normalize([dx, dy, dz])

    mat = matrix_3d_translate(x0, y0, z0)

    mat2 = np.array([
        [-dz * dz - dy * dy, dx * dy, dx * dz, 0.0],
        [dy * dx, -dx * dx - dz * dz, dy * dz, 0.0],
        [dz * dx, dz * dy, -dy * dy - dx * dx, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    mat = matrix_mult(mat, mat2)
    mat2 = matrix_3d_translate(-x0, -y0, -z0)
    return matrix_mult(mat, mat2)


def matrix_3d_shear_xy(shx: float, shy: float) -> np.ndarray:
    """
    Create a 3D shear matrix in XY plane.

    Args:
        shx: Shear factor for x
        shy: Shear factor for y

    Returns:
        4x4 shear matrix
    """
    return np.array([
        [1.0, 0.0, shx, 0.0],
        [0.0, 1.0, shy, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_shear_xz(shx: float, shz: float) -> np.ndarray:
    """
    Create a 3D shear matrix in XZ plane.

    Args:
        shx: Shear factor for x
        shz: Shear factor for z

    Returns:
        4x4 shear matrix
    """
    return np.array([
        [1.0, shx, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, shz, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_shear_yz(shy: float, shz: float) -> np.ndarray:
    """
    Create a 3D shear matrix in YZ plane.

    Args:
        shy: Shear factor for y
        shz: Shear factor for z

    Returns:
        4x4 shear matrix
    """
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [shy, 1.0, 0.0, 0.0],
        [shz, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_3d_coordsys_convert(origin: List[float], xvect: List[float],
                               yvect: List[float],
                               zvect: List[float]) -> np.ndarray:
    """
    Create a coordinate system conversion matrix.

    Args:
        origin: Origin point [x, y, z]
        xvect: X-axis vector [x, y, z]
        yvect: Y-axis vector [x, y, z]
        zvect: Z-axis vector [x, y, z]

    Returns:
        4x4 coordinate system conversion matrix
    """
    xvect_h = list(xvect) + [0.0]
    yvect_h = list(yvect) + [0.0]
    zvect_h = list(zvect) + [0.0]
    origin_h = list(origin) + [1.0]

    mat = np.array([xvect_h, yvect_h, zvect_h, origin_h])
    return mat.T


def matrix_3d_transform_coords(mat: np.ndarray,
                               coords: List[float]) -> List[float]:
    """
    Transform a list of 3D coordinates using a transformation matrix.

    Args:
        mat: 4x4 transformation matrix
        coords: List of coordinates [x1, y1, z1, x2, y2, z2, ...]

    Returns:
        List of transformed coordinates
    """
    outcoords = []
    for i in range(0, len(coords), 3):
        x, y, z = coords[i], coords[i + 1], coords[i + 2]
        nx = mat[0, 0] * x + mat[0, 1] * y + mat[0, 2] * z + mat[0, 3]
        ny = mat[1, 0] * x + mat[1, 1] * y + mat[1, 2] * z + mat[1, 3]
        nz = mat[2, 0] * x + mat[2, 1] * y + mat[2, 2] * z + mat[2, 3]
        outcoords.extend([nx, ny, nz])

    return outcoords


##################################################################
# Vector math
##################################################################

def matrix_vector(mat: np.ndarray) -> List[float]:
    """
    Extract diagonal vector from a matrix.

    Args:
        mat: Input matrix

    Returns:
        Diagonal elements as a list (excluding last element)
    """
    m = mat.shape[0]
    out = []
    for i in range(m - 1):
        out.append(mat[i, i])
    return out


def vector_matrix(vect: List[float]) -> np.ndarray:
    """
    Create a diagonal matrix from a vector.

    Args:
        vect: Input vector

    Returns:
        Diagonal matrix with vector elements and 1 in bottom-right
    """
    m = len(vect) + 1
    mat = np.zeros((m, m))

    for i in range(m):
        if i == m - 1:
            mat[i, i] = 1.0
        else:
            mat[i, i] = vect[i]

    return mat


def vector_magnitude(vect: List[float]) -> float:
    """
    Calculate the magnitude (length) of a vector.

    Args:
        vect: Input vector

    Returns:
        Vector magnitude
    """
    return math.sqrt(sum(val * val for val in vect))


def vector_normalize(vect: List[float]) -> List[float]:
    """
    Normalize a vector to unit length.

    Args:
        vect: Input vector

    Returns:
        Normalized vector

    Raises:
        ZeroDivisionError: If vector has zero magnitude
    """
    length = vector_magnitude(vect)
    if length == 0.0:
        raise ZeroDivisionError("Cannot normalize zero-length vector")

    return [val / length for val in vect]


def vector_add(vect1: List[float], vect2: List[float]) -> List[float]:
    """
    Add two vectors element-wise.

    Args:
        vect1: First vector
        vect2: Second vector

    Returns:
        Sum vector
    """
    return [val1 + val2 for val1, val2 in zip(vect1, vect2)]


def vector_subtract(vect1: List[float], vect2: List[float]) -> List[float]:
    """
    Subtract two vectors element-wise.

    Args:
        vect1: First vector
        vect2: Second vector

    Returns:
        Difference vector (vect1 - vect2)
    """
    return [val1 - val2 for val1, val2 in zip(vect1, vect2)]


def vector_multiply(vect: List[float], val: float) -> List[float]:
    """
    Multiply a vector by a scalar.

    Args:
        vect: Input vector
        val: Scalar value

    Returns:
        Scaled vector
    """
    return [val * val2 for val2 in vect]


def vector_dot(vect1: List[float], vect2: List[float]) -> float:
    """
    Calculate the dot product of two vectors.

    Args:
        vect1: First vector
        vect2: Second vector

    Returns:
        Dot product
    """
    return sum(val1 * val2 for val1, val2 in zip(vect1, vect2))


def vector_cross(vect1: List[float], vect2: List[float]) -> List[float]:
    """
    Calculate the cross product of two 3D vectors.

    Args:
        vect1: First 3D vector [x, y, z]
        vect2: Second 3D vector [x, y, z]

    Returns:
        Cross product vector [x, y, z]

    Raises:
        ValueError: If vectors are not 3D
    """
    if len(vect1) != 3 or len(vect2) != 3:
        raise ValueError("Cross product requires 3D vectors")

    x1, y1, z1 = vect1
    x2, y2, z2 = vect2

    x = y1 * z2 - z1 * y2
    y = z1 * x2 - x1 * z2
    z = x1 * y2 - y1 * x2

    return [x, y, z]


def vector_reflect(vect: List[float], refvect: List[float]) -> List[float]:
    """
    Reflect a vector across another vector.

    Args:
        vect: Vector to reflect
        refvect: Reflection vector

    Returns:
        Reflected vector
    """
    numer = vector_dot(vect, refvect)
    denom = vector_dot(refvect, refvect)
    mult = 2.0 * numer / denom
    vect2 = vector_multiply(refvect, mult)
    return vector_subtract(vect, vect2)


# vim: set ts=4 sw=4 nowrap expandtab: settings
