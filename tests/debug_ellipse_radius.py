#!/usr/bin/env python3
"""
Debug test for ellipse radius calculation.
"""

import math
from PySide6.QtCore import QPointF


def debug_major_radius_calculation():
    """Debug the major radius calculation."""
    print("Debugging major radius calculation...")
    
    # Initial setup
    focus1 = QPointF(-4.472, 0)
    focus2 = QPointF(4.472, 0)
    center = (focus1 + focus2) * 0.5
    print(f"Center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Focus1: ({focus1.x():.3f}, {focus1.y():.3f})")
    print(f"Focus2: ({focus2.x():.3f}, {focus2.y():.3f})")
    
    # Test different perimeter points
    target_major_radius = 5.0
    print(f"\nTarget major radius: {target_major_radius:.3f}")
    
    for test_dist in range(1, 11):
        test_perimeter = center + QPointF(test_dist, 0)
        
        # Calculate distances from test perimeter to foci
        dist1 = math.hypot(test_perimeter.x() - focus1.x(), test_perimeter.y() - focus1.y())
        dist2 = math.hypot(test_perimeter.x() - focus2.x(), test_perimeter.y() - focus2.y())
        
        test_major_radius = (dist1 + dist2) / 2
        
        print(f"Test perimeter at ({test_perimeter.x():.3f}, {test_perimeter.y():.3f}):")
        print(f"  Dist1: {dist1:.3f}")
        print(f"  Dist2: {dist2:.3f}")
        print(f"  Major radius: {test_major_radius:.3f}")
        print(f"  Error: {abs(test_major_radius - target_major_radius):.3f}")
        
        if abs(test_major_radius - target_major_radius) < 0.1:
            print(f"  ✓ Found good perimeter point!")
            break


def debug_binary_search():
    """Debug the binary search approach."""
    print("\nDebugging binary search...")
    
    # Initial setup
    focus1 = QPointF(-4.472, 0)
    focus2 = QPointF(4.472, 0)
    center = (focus1 + focus2) * 0.5
    target_major_radius = 5.0
    
    # Binary search
    min_dist = 0
    max_dist = target_major_radius * 2
    test_dist = (min_dist + max_dist) / 2
    
    print(f"Search range: {min_dist:.3f} to {max_dist:.3f}")
    
    for i in range(10):
        test_perimeter = center + QPointF(test_dist, 0)
        
        # Calculate distances from test perimeter to foci
        dist1 = math.hypot(test_perimeter.x() - focus1.x(), test_perimeter.y() - focus1.y())
        dist2 = math.hypot(test_perimeter.x() - focus2.x(), test_perimeter.y() - focus2.y())
        
        test_major_radius = (dist1 + dist2) / 2
        
        print(f"Iteration {i}:")
        print(f"  Test distance: {test_dist:.3f}")
        print(f"  Test perimeter: ({test_perimeter.x():.3f}, {test_perimeter.y():.3f})")
        print(f"  Major radius: {test_major_radius:.3f}")
        print(f"  Error: {abs(test_major_radius - target_major_radius):.3f}")
        
        if abs(test_major_radius - target_major_radius) < 0.001:
            print(f"  ✓ Found exact perimeter point!")
            break
        elif test_major_radius < target_major_radius:
            min_dist = test_dist
            print(f"  Too small, increasing min_dist to {min_dist:.3f}")
        else:
            max_dist = test_dist
            print(f"  Too large, decreasing max_dist to {max_dist:.3f}")
        
        test_dist = (min_dist + max_dist) / 2


if __name__ == "__main__":
    debug_major_radius_calculation()
    debug_binary_search() 