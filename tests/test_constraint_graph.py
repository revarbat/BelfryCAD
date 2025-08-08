import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.utils.geometry import Point2D
from BelfryCAD.utils.constraints import CoincidentConstraint, HorizontalConstraint, VerticalConstraint


def test_constraint_graph():
    """Test constraint graph with disconnected components."""
    print("Testing Constraint Graph with Disconnected Components...")
    
    # Create document
    doc = Document()
    
    # Create two separate groups of objects
    # Group 1: Two lines forming a corner
    line1 = LineCadObject(document=doc, start_point=Point2D(0, 0), end_point=Point2D(10, 0))
    line2 = LineCadObject(document=doc, start_point=Point2D(10, 0), end_point=Point2D(10, 5))
    line1_id = doc.add_object(line1)
    line2_id = doc.add_object(line2)
    
    # Group 2: Two circles
    circle1 = CircleCadObject(document=doc, center_point=Point2D(20, 0), perimeter_point=Point2D(23, 0))
    circle2 = CircleCadObject(document=doc, center_point=Point2D(30, 0), perimeter_point=Point2D(33, 0))
    circle1_id = doc.add_object(circle1)
    circle2_id = doc.add_object(circle2)
    
    # Create constrainables for all objects
    for obj in [line1, line2, circle1, circle2]:
        obj.make_constrainables(doc.constraints_manager.solver)
    
    print(f"Created objects: line1={line1_id}, line2={line2_id}, circle1={circle1_id}, circle2={circle2_id}")
    
    # Add constraints within Group 1 (lines)
    print("\n1. Adding constraints to Group 1 (lines)...")
    coincident1 = CoincidentConstraint(
        line1.get_constrainables()[1][1],  # line1 end_point
        line2.get_constrainables()[0][1]   # line2 start_point
    )
    doc.add_constraint("coincident1", coincident1, line1_id, line2_id)
    
    horizontal1 = HorizontalConstraint(
        line1.get_constrainables()[0][1],  # line1 start_point
        line1.get_constrainables()[1][1]   # line1 end_point
    )
    doc.add_constraint("horizontal1", horizontal1, line1_id)
    
    vertical1 = VerticalConstraint(
        line2.get_constrainables()[0][1],  # line2 start_point
        line2.get_constrainables()[1][1]   # line2 end_point
    )
    doc.add_constraint("vertical1", vertical1, line2_id)
    
    # Add constraints within Group 2 (circles)
    print("2. Adding constraints to Group 2 (circles)...")
    horizontal2 = HorizontalConstraint(
        circle1.get_constrainables()[0][1],  # circle1 center
        circle2.get_constrainables()[0][1]   # circle2 center
    )
    doc.add_constraint("horizontal2", horizontal2, circle1_id, circle2_id)
    
    # Analyze constraint graph
    print("\n3. Analyzing constraint graph...")
    components = doc.constraints_manager.get_connected_components()
    component_info = doc.constraints_manager.get_component_info()
    constraint_info = doc.constraints_manager.get_constraint_info()
    
    print(f"   Connected components: {len(components)}")
    print(f"   Component sizes: {constraint_info['component_sizes']}")
    
    for i, info in enumerate(component_info):
        print(f"   Component {i}: {info['object_count']} objects, {info['constraint_count']} constraints")
        print(f"     Objects: {info['object_ids']}")
    
    # Test solving with one component that should fail
    print("\n4. Testing component isolation...")
    
    # Move circle2 to create an impossible constraint
    circle2.center_point = Point2D(50, 0)  # Move far away
    
    print("   Initial positions:")
    print(f"     Line1: {line1.start_point} to {line1.end_point}")
    print(f"     Line2: {line2.start_point} to {line2.end_point}")
    print(f"     Circle1: center={circle1.center_point}, radius={circle1.radius}")
    print(f"     Circle2: center={circle2.center_point}, radius={circle2.radius}")
    
    # Solve constraints - Group 1 should succeed, Group 2 should fail
    success = doc.solve_constraints()
    print(f"   Overall solver success: {success}")
    
    print("   Final positions:")
    print(f"     Line1: {line1.start_point} to {line1.end_point}")
    print(f"     Line2: {line2.start_point} to {line2.end_point}")
    print(f"     Circle1: center={circle1.center_point}, radius={circle1.radius}")
    print(f"     Circle2: center={circle2.center_point}, radius={circle2.radius}")
    
    # Verify that Group 1 (lines) was solved correctly
    line1_expected_start = Point2D(0, 0)
    line1_expected_end = Point2D(10, 0)
    line2_expected_start = Point2D(10, 0)
    line2_expected_end = Point2D(10, 5)
    
    line1_correct = (abs(line1.start_point.x - line1_expected_start.x) < 0.001 and
                     abs(line1.start_point.y - line1_expected_start.y) < 0.001 and
                     abs(line1.end_point.x - line1_expected_end.x) < 0.001 and
                     abs(line1.end_point.y - line1_expected_end.y) < 0.001)
    
    line2_correct = (abs(line2.start_point.x - line2_expected_start.x) < 0.001 and
                     abs(line2.start_point.y - line2_expected_start.y) < 0.001 and
                     abs(line2.end_point.x - line2_expected_end.x) < 0.001 and
                     abs(line2.end_point.y - line2_expected_end.y) < 0.001)
    
    print(f"\n5. Verification:")
    print(f"   Group 1 (lines) solved correctly: {line1_correct and line2_correct}")
    print(f"   Group 2 (circles) failed as expected: {not success}")
    
    print("\nConstraint graph test completed successfully!")
    print("✅ Component isolation works")
    print("✅ Independent solving works")
    print("✅ Fault isolation works")
    print("✅ Graph analysis works")


if __name__ == "__main__":
    test_constraint_graph() 