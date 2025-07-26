#!/usr/bin/env python3
"""
Test script for Ellipse constraint geometry.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.constraints import (
    ConstraintSolver, Point2D, Ellipse, LineSegment, Circle, Arc,
    point_on_ellipse, ellipse_is_centered_at_point, line_is_tangent_to_ellipse,
    ellipse_radius1_is, ellipse_radius2_is, ellipse_rotation_is
)


def test_ellipse_basic():
    """Test basic ellipse creation and properties."""
    print("Testing basic ellipse functionality...")
    
    solver = ConstraintSolver()
    
    # Create a point for the center
    center = Point2D(solver, (0, 0), fixed=True)
    
    # Create an ellipse with major radius 5, minor radius 3, rotation 0
    ellipse = Ellipse(solver, center, 5.0, 3.0, 0.0)
    
    # Solve the constraints
    result = solver.solve()
    
    if result is not None:
        print(f"Solve successful: {result.success}")
        print(f"Cost: {result.cost}")
        
        # Get the ellipse parameters
        cx, cy, major_r, minor_r, rotation = ellipse.get(solver.variables)
        print(f"Ellipse: center=({cx:.3f}, {cy:.3f}), major_r={major_r:.3f}, minor_r={minor_r:.3f}, rotation={rotation:.3f}")
        
        # Test eccentricity
        ecc = ellipse.eccentricity(solver.variables)
        print(f"Eccentricity: {ecc:.3f}")
        
        # Test focus points
        f1, f2 = ellipse.get_focus_points(solver.variables)
        print(f"Focus points: F1=({f1[0]:.3f}, {f1[1]:.3f}), F2=({f2[0]:.3f}, {f2[1]:.3f})")
        
        return True
    else:
        print("Solve failed")
        return False


def test_ellipse_constraints():
    """Test ellipse constraints."""
    print("\nTesting ellipse constraints...")
    
    solver = ConstraintSolver()
    
    # Create fixed center point
    center = Point2D(solver, (0, 0), fixed=True)
    
    # Create ellipse with initial parameters
    ellipse = Ellipse(solver, center, 5.0, 3.0, 30.0)
    
    # Add constraints
    solver.add_constraint(ellipse_radius1_is(ellipse, 6.0), "radius1")
    solver.add_constraint(ellipse_radius2_is(ellipse, 4.0), "radius2")
    solver.add_constraint(ellipse_rotation_is(ellipse, 45.0), "rotation")
    
    # Solve
    result = solver.solve()
    
    if result is not None and result.success:
        print(f"Solve successful: {result.success}")
        
        # Get the ellipse parameters
        cx, cy, major_r, minor_r, rotation = ellipse.get(solver.variables)
        print(f"Ellipse: center=({cx:.3f}, {cy:.3f}), major_r={major_r:.3f}, minor_r={minor_r:.3f}, rotation={rotation:.3f}")
        
        # Verify constraints
        print(f"Radius1 constraint: {abs(major_r - 6.0):.6f}")
        print(f"Radius2 constraint: {abs(minor_r - 4.0):.6f}")
        print(f"Rotation constraint: {abs(rotation - 45.0):.6f}")
        
        return True
    else:
        print("Solve failed")
        return False


def test_point_on_ellipse():
    """Test point on ellipse constraint."""
    print("\nTesting point on ellipse constraint...")
    
    solver = ConstraintSolver()
    
    # Create fixed center point
    center = Point2D(solver, (0, 0), fixed=True)
    
    # Create ellipse
    ellipse = Ellipse(solver, center, 5.0, 3.0, 0.0)
    
    # Create a point that should be on the ellipse
    point = Point2D(solver, (5.0, 0.0))  # Should be on major axis
    
    # Add constraint
    solver.add_constraint(point_on_ellipse(point, ellipse), "point_on_ellipse")
    
    # Solve
    result = solver.solve()
    
    if result is not None and result.success:
        print(f"Solve successful: {result.success}")
        
        # Get the point coordinates
        px, py = point.get(solver.variables)
        print(f"Point: ({px:.3f}, {py:.3f})")
        
        # Calculate distance to ellipse perimeter
        dist = ellipse.distance_to_perimeter(solver.variables, point)
        print(f"Distance to ellipse perimeter: {dist:.6f}")
        
        return True
    else:
        print("Solve failed")
        return False


def test_line_tangent_to_ellipse():
    """Test line tangent to ellipse constraint."""
    print("\nTesting line tangent to ellipse constraint...")
    
    solver = ConstraintSolver()
    
    # Create fixed center point
    center = Point2D(solver, (0, 0), fixed=True)
    
    # Create ellipse
    ellipse = Ellipse(solver, center, 5.0, 3.0, 0.0)
    
    # Create line points
    p1 = Point2D(solver, (10.0, 0.0))
    p2 = Point2D(solver, (10.0, 5.0))
    line = LineSegment(solver, p1, p2)
    
    # Add constraint
    solver.add_constraint(line_is_tangent_to_ellipse(line, ellipse), "line_tangent")
    
    # Solve
    result = solver.solve()
    
    if result is not None and result.success:
        print(f"Solve successful: {result.success}")
        
        # Get the line coordinates
        x1, y1, x2, y2 = line.get(solver.variables)
        print(f"Line: ({x1:.3f}, {y1:.3f}) to ({x2:.3f}, {y2:.3f})")
        
        # Calculate distance from line to ellipse
        dist = line.distance_to(solver.variables, center)
        print(f"Distance from line to ellipse center: {dist:.6f}")
        
        return True
    else:
        print("Solve failed")
        return False


def main():
    """Run all ellipse tests."""
    print("=== Ellipse Constraint Tests ===\n")
    
    tests = [
        test_ellipse_basic,
        test_ellipse_constraints,
        test_point_on_ellipse,
        test_line_tangent_to_ellipse
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ Test passed\n")
            else:
                print("✗ Test failed\n")
        except Exception as e:
            print(f"✗ Test failed with exception: {e}\n")
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("All ellipse tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 