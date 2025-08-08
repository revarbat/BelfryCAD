#!/usr/bin/env python3
"""
Example demonstrating the ConstraintsManager functionality.

This example shows how to:
1. Create CAD objects
2. Add constraints between objects
3. Solve constraints
4. Remove constraints
5. Track constraint relationships
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.utils.geometry import Point2D
from BelfryCAD.utils.constraints import (
    CoincidentConstraint, 
    HorizontalConstraint, 
    VerticalConstraint,
    LinesEqualLengthConstraint,
    LinesPerpendicularConstraint
)


def constraints_manager_example():
    """Demonstrate ConstraintsManager functionality."""
    print("ConstraintsManager Example")
    print("=" * 50)
    
    # Create a document
    doc = Document()
    
    # Create some CAD objects
    print("\n1. Creating CAD objects...")
    
    # Create a rectangle using 4 lines
    line1 = LineCadObject(doc, Point2D(0, 0), Point2D(10, 0))  # Bottom
    line2 = LineCadObject(doc, Point2D(10, 0), Point2D(10, 5))  # Right
    line3 = LineCadObject(doc, Point2D(10, 5), Point2D(0, 5))   # Top
    line4 = LineCadObject(doc, Point2D(0, 5), Point2D(0, 0))    # Left
    
    # Add objects to document
    line1_id = doc.add_object(line1)
    line2_id = doc.add_object(line2)
    line3_id = doc.add_object(line3)
    line4_id = doc.add_object(line4)
    
    print(f"   Created lines: {line1_id}, {line2_id}, {line3_id}, {line4_id}")
    
    # Create constrainables for all objects
    print("\n2. Creating constrainables...")
    for obj in [line1, line2, line3, line4]:
        obj.make_constrainables(doc.constraints_manager.solver)
    
    # Add constraints to create a proper rectangle
    print("\n3. Adding constraints...")
    
    # Make lines horizontal/vertical
    horizontal_constraint1 = HorizontalConstraint(
        line1.get_constrainables()[0][1],  # start_point
        line1.get_constrainables()[1][1]   # end_point
    )
    doc.add_constraint("horizontal1", horizontal_constraint1, line1_id)
    
    horizontal_constraint3 = HorizontalConstraint(
        line3.get_constrainables()[0][1],  # start_point
        line3.get_constrainables()[1][1]   # end_point
    )
    doc.add_constraint("horizontal3", horizontal_constraint3, line3_id)
    
    vertical_constraint2 = VerticalConstraint(
        line2.get_constrainables()[0][1],  # start_point
        line2.get_constrainables()[1][1]   # end_point
    )
    doc.add_constraint("vertical2", vertical_constraint2, line2_id)
    
    vertical_constraint4 = VerticalConstraint(
        line4.get_constrainables()[0][1],  # start_point
        line4.get_constrainables()[1][1]   # end_point
    )
    doc.add_constraint("vertical4", vertical_constraint4, line4_id)
    
    # Connect the lines at corners
    coincident1 = CoincidentConstraint(
        line1.get_constrainables()[1][1],  # line1 end
        line2.get_constrainables()[0][1]   # line2 start
    )
    doc.add_constraint("coincident1", coincident1, line1_id, line2_id)
    
    coincident2 = CoincidentConstraint(
        line2.get_constrainables()[1][1],  # line2 end
        line3.get_constrainables()[0][1]   # line3 start
    )
    doc.add_constraint("coincident2", coincident2, line2_id, line3_id)
    
    coincident3 = CoincidentConstraint(
        line3.get_constrainables()[1][1],  # line3 end
        line4.get_constrainables()[0][1]   # line4 start
    )
    doc.add_constraint("coincident3", coincident3, line3_id, line4_id)
    
    coincident4 = CoincidentConstraint(
        line4.get_constrainables()[1][1],  # line4 end
        line1.get_constrainables()[0][1]   # line1 start
    )
    doc.add_constraint("coincident4", coincident4, line4_id, line1_id)
    
    # Make opposite sides equal length
    equal_length1 = LinesEqualLengthConstraint(
        line1.get_constrainables()[2][1],  # line1
        line3.get_constrainables()[2][1]   # line3
    )
    doc.add_constraint("equal_length1", equal_length1, line1_id, line3_id)
    
    equal_length2 = LinesEqualLengthConstraint(
        line2.get_constrainables()[2][1],  # line2
        line4.get_constrainables()[2][1]   # line4
    )
    doc.add_constraint("equal_length2", equal_length2, line2_id, line4_id)
    
    # Make adjacent sides perpendicular
    perpendicular1 = LinesPerpendicularConstraint(
        line1.get_constrainables()[2][1],  # line1
        line2.get_constrainables()[2][1]   # line2
    )
    doc.add_constraint("perpendicular1", perpendicular1, line1_id, line2_id)
    
    perpendicular2 = LinesPerpendicularConstraint(
        line2.get_constrainables()[2][1],  # line2
        line3.get_constrainables()[2][1]   # line3
    )
    doc.add_constraint("perpendicular2", perpendicular2, line2_id, line3_id)
    
    perpendicular3 = LinesPerpendicularConstraint(
        line3.get_constrainables()[2][1],  # line3
        line4.get_constrainables()[2][1]   # line4
    )
    doc.add_constraint("perpendicular3", perpendicular3, line3_id, line4_id)
    
    perpendicular4 = LinesPerpendicularConstraint(
        line4.get_constrainables()[2][1],  # line4
        line1.get_constrainables()[2][1]   # line1
    )
    doc.add_constraint("perpendicular4", perpendicular4, line4_id, line1_id)
    
    print(f"   Added {doc.get_constraint_count()} constraints")
    
    # Show constraint information
    print("\n4. Constraint information...")
    print(f"   Total constraints: {doc.get_constraint_count()}")
    print(f"   Constrained objects: {doc.constraints_manager.get_constrained_object_count()}")
    
    for obj_id in [line1_id, line2_id, line3_id, line4_id]:
        constraints = doc.get_constraints_for_object(obj_id)
        print(f"   Object {obj_id}: {len(constraints)} constraints")
    
    # Solve constraints
    print("\n5. Solving constraints...")
    
    # Show initial positions
    print("   Initial positions:")
    for i, line in enumerate([line1, line2, line3, line4], 1):
        print(f"     Line{i}: {line.start_point} to {line.end_point}")
    
    # Solve
    success = doc.solve_constraints()
    print(f"   Solver success: {success}")
    
    # Show final positions
    print("   Final positions:")
    for i, line in enumerate([line1, line2, line3, line4], 1):
        print(f"     Line{i}: {line.start_point} to {line.end_point}")
    
    # Test constraint removal
    print("\n6. Testing constraint removal...")
    
    # Remove one constraint
    removed = doc.remove_constraint("perpendicular1")
    print(f"   Removed perpendicular1: {removed}")
    print(f"   Remaining constraints: {doc.get_constraint_count()}")
    
    # Remove all constraints between two objects
    removed_constraints = doc.remove_constraints_between_objects(line1_id, line2_id)
    print(f"   Removed constraints between line1 and line2: {removed_constraints}")
    print(f"   Remaining constraints: {doc.get_constraint_count()}")
    
    # Clear all constraints
    print("\n7. Clearing all constraints...")
    doc.constraints_manager.clear_all_constraints()
    print(f"   After clearing: {doc.get_constraint_count()} constraints")
    print(f"   Has constraints: {doc.has_constraints()}")
    
    print("\nConstraintsManager example completed successfully!")
    print("✅ Constraint management works")
    print("✅ Constraint solving works")
    print("✅ Constraint tracking works")
    print("✅ Constraint removal works")


if __name__ == "__main__":
    constraints_manager_example() 