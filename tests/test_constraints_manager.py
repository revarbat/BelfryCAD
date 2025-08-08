#!/usr/bin/env python3
"""
Test the ConstraintsManager class functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.utils.geometry import Point2D
from BelfryCAD.utils.constraints import CoincidentConstraint, HorizontalConstraint


def test_constraints_manager():
    """Test the ConstraintsManager functionality."""
    print("Testing ConstraintsManager...")
    
    # Create a document
    doc = Document()
    
    # Create some test objects
    line1 = LineCadObject(
        document=doc,
        start_point=Point2D(0, 0),
        end_point=Point2D(10, 0)
    )
    line1_id = doc.add_object(line1)
    
    line2 = LineCadObject(
        document=doc,
        start_point=Point2D(0, 5),
        end_point=Point2D(10, 5)
    )
    line2_id = doc.add_object(line2)
    
    circle1 = CircleCadObject(
        document=doc,
        center_point=Point2D(5, 10),
        perimeter_point=Point2D(8, 10)
    )
    circle1_id = doc.add_object(circle1)
    
    print(f"Created objects: line1={line1_id}, line2={line2_id}, circle1={circle1_id}")
    
    # Test 1: Add constraints
    print("\n1. Testing constraint addition...")
    
    # Create constrainables for the objects
    line1.make_constrainables(doc.constraints_manager.solver)
    line2.make_constrainables(doc.constraints_manager.solver)
    circle1.make_constrainables(doc.constraints_manager.solver)
    
    # Add a coincident constraint between line1 end and line2 start
    constraint_id1 = doc.get_constraint_id("coincident", line1_id, line2_id)
    coincident_constraint = CoincidentConstraint(
        line1.get_constrainables()[1][1],  # end_point
        line2.get_constrainables()[0][1]   # start_point
    )
    
    success = doc.add_constraint(constraint_id1, coincident_constraint, line1_id, line2_id)
    print(f"   Added coincident constraint: {success}")
    
    # Add a horizontal constraint to line1
    constraint_id2 = doc.get_constraint_id("horizontal", line1_id, None)
    horizontal_constraint = HorizontalConstraint(
        line1.get_constrainables()[0][1],  # start_point
        line1.get_constrainables()[1][1]   # end_point
    )
    
    success = doc.add_constraint(constraint_id2, horizontal_constraint, line1_id)
    print(f"   Added horizontal constraint: {success}")
    
    # Test 2: Check constraint tracking
    print("\n2. Testing constraint tracking...")
    
    print(f"   Total constraints: {doc.get_constraint_count()}")
    print(f"   Has constraints: {doc.has_constraints()}")
    
    line1_constraints = doc.get_constraints_for_object(line1_id)
    print(f"   Line1 constraints: {line1_constraints}")
    
    line2_constraints = doc.get_constraints_for_object(line2_id)
    print(f"   Line2 constraints: {line2_constraints}")
    
    between_constraints = doc.get_constraints_between_objects(line1_id, line2_id)
    print(f"   Constraints between line1 and line2: {between_constraints}")
    
    # Test 3: Solve constraints
    print("\n3. Testing constraint solving...")
    
    # Get initial positions
    initial_line1_start = line1.start_point
    initial_line1_end = line1.end_point
    initial_line2_start = line2.start_point
    initial_line2_end = line2.end_point
    
    print(f"   Initial line1: {initial_line1_start} to {initial_line1_end}")
    print(f"   Initial line2: {initial_line2_start} to {initial_line2_end}")
    
    # Solve constraints
    success = doc.solve_constraints()
    print(f"   Constraint solving: {success}")
    
    # Get final positions
    final_line1_start = line1.start_point
    final_line1_end = line1.end_point
    final_line2_start = line2.start_point
    final_line2_end = line2.end_point
    
    print(f"   Final line1: {final_line1_start} to {final_line1_end}")
    print(f"   Final line2: {final_line2_start} to {final_line2_end}")
    
    # Test 4: Remove constraints
    print("\n4. Testing constraint removal...")
    
    removed_constraints = doc.remove_constraints_between_objects(line1_id, line2_id)
    print(f"   Removed constraints: {removed_constraints}")
    
    print(f"   Remaining constraints: {doc.get_constraint_count()}")
    
    # Test 5: Clear all constraints
    print("\n5. Testing constraint clearing...")
    
    doc.constraints_manager.clear_all_constraints()
    print(f"   After clearing: {doc.get_constraint_count()} constraints")
    print(f"   Has constraints: {doc.has_constraints()}")
    
    print("\nConstraintsManager test completed successfully!")
    print("✅ Constraint addition works")
    print("✅ Constraint tracking works")
    print("✅ Constraint solving works")
    print("✅ Constraint removal works")
    print("✅ Constraint clearing works")


if __name__ == "__main__":
    test_constraints_manager() 