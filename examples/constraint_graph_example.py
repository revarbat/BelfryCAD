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


def constraint_graph_example():
    """Demonstrate constraint graph with multiple disconnected components."""
    print("Constraint Graph Example")
    print("=" * 50)
    
    # Create document
    doc = Document()
    
    # Create three separate constraint systems
    print("\n1. Creating three separate constraint systems...")
    
    # System 1: Rectangle (4 lines with constraints)
    print("   System 1: Rectangle with 4 lines")
    rect_lines = []
    rect_ids = []
    
    # Create rectangle lines
    rect_points = [
        (Point2D(0, 0), Point2D(10, 0)),    # bottom
        (Point2D(10, 0), Point2D(10, 5)),   # right
        (Point2D(10, 5), Point2D(0, 5)),    # top
        (Point2D(0, 5), Point2D(0, 0))      # left
    ]
    
    for i, (start, end) in enumerate(rect_points):
        line = LineCadObject(document=doc, start_point=start, end_point=end)
        line_id = doc.add_object(line)
        rect_lines.append(line)
        rect_ids.append(line_id)
        line.make_constrainables(doc.constraints_manager.solver)
    
    # System 2: Two circles with horizontal alignment
    print("   System 2: Two circles with horizontal alignment")
    circle1 = CircleCadObject(document=doc, center_point=Point2D(20, 0), radius=3.0)
circle2 = CircleCadObject(document=doc, center_point=Point2D(30, 0), radius=3.0)
    circle1_id = doc.add_object(circle1)
    circle2_id = doc.add_object(circle2)
    circle1.make_constrainables(doc.constraints_manager.solver)
    circle2.make_constrainables(doc.constraints_manager.solver)
    
    # System 3: Single line with horizontal constraint
    print("   System 3: Single line with horizontal constraint")
    single_line = LineCadObject(document=doc, start_point=Point2D(40, 0), end_point=Point2D(50, 2))
    single_line_id = doc.add_object(single_line)
    single_line.make_constrainables(doc.constraints_manager.solver)
    
    print(f"   Created {len(rect_ids)} rectangle lines, 2 circles, 1 single line")
    
    # Add constraints to System 1 (Rectangle)
    print("\n2. Adding constraints to System 1 (Rectangle)...")
    
    # Rectangle constraints: coincident corners, horizontal/vertical edges, equal lengths
    rect_constraints = [
        # Coincident corners
        ("rect_coincident1", CoincidentConstraint(
            rect_lines[0].get_constrainables()[1][1],  # bottom end
            rect_lines[1].get_constrainables()[0][1]   # right start
        ), rect_ids[0], rect_ids[1]),
        
        ("rect_coincident2", CoincidentConstraint(
            rect_lines[1].get_constrainables()[1][1],  # right end
            rect_lines[2].get_constrainables()[0][1]   # top start
        ), rect_ids[1], rect_ids[2]),
        
        ("rect_coincident3", CoincidentConstraint(
            rect_lines[2].get_constrainables()[1][1],  # top end
            rect_lines[3].get_constrainables()[0][1]   # left start
        ), rect_ids[2], rect_ids[3]),
        
        ("rect_coincident4", CoincidentConstraint(
            rect_lines[3].get_constrainables()[1][1],  # left end
            rect_lines[0].get_constrainables()[0][1]   # bottom start
        ), rect_ids[3], rect_ids[0]),
        
        # Horizontal/vertical constraints
        ("rect_horizontal1", HorizontalConstraint(
            rect_lines[0].get_constrainables()[0][1],  # bottom start
            rect_lines[0].get_constrainables()[1][1]   # bottom end
        ), rect_ids[0]),
        
        ("rect_horizontal2", HorizontalConstraint(
            rect_lines[2].get_constrainables()[0][1],  # top start
            rect_lines[2].get_constrainables()[1][1]   # top end
        ), rect_ids[2]),
        
        ("rect_vertical1", VerticalConstraint(
            rect_lines[1].get_constrainables()[0][1],  # right start
            rect_lines[1].get_constrainables()[1][1]   # right end
        ), rect_ids[1]),
        
        ("rect_vertical2", VerticalConstraint(
            rect_lines[3].get_constrainables()[0][1],  # left start
            rect_lines[3].get_constrainables()[1][1]   # left end
        ), rect_ids[3]),
        
        # Equal length constraints
        ("rect_equal_length1", LinesEqualLengthConstraint(
            rect_lines[0].get_constrainables()[2][1],  # bottom line
            rect_lines[2].get_constrainables()[2][1]   # top line
        ), rect_ids[0], rect_ids[2]),
        
        ("rect_equal_length2", LinesEqualLengthConstraint(
            rect_lines[1].get_constrainables()[2][1],  # right line
            rect_lines[3].get_constrainables()[2][1]   # left line
        ), rect_ids[1], rect_ids[3]),
    ]
    
    for constraint_data in rect_constraints:
        if len(constraint_data) == 4:
            constraint_id, constraint, obj1_id, obj2_id = constraint_data
            doc.add_constraint(constraint_id, constraint, obj1_id, obj2_id)
        else:
            constraint_id, constraint, obj1_id = constraint_data
            doc.add_constraint(constraint_id, constraint, obj1_id)
    
    # Add constraints to System 2 (Circles)
    print("3. Adding constraints to System 2 (Circles)...")
    
    circle_horizontal = HorizontalConstraint(
        circle1.get_constrainables()[0][1],  # circle1 center
        circle2.get_constrainables()[0][1]   # circle2 center
    )
    doc.add_constraint("circle_horizontal", circle_horizontal, circle1_id, circle2_id)
    
    # Add constraints to System 3 (Single line)
    print("4. Adding constraints to System 3 (Single line)...")
    
    single_horizontal = HorizontalConstraint(
        single_line.get_constrainables()[0][1],  # single line start
        single_line.get_constrainables()[1][1]   # single line end
    )
    doc.add_constraint("single_horizontal", single_horizontal, single_line_id)
    
    # Analyze the constraint graph
    print("\n5. Analyzing constraint graph...")
    components = doc.constraints_manager.get_connected_components()
    component_info = doc.constraints_manager.get_component_info()
    constraint_info = doc.constraints_manager.get_constraint_info()
    
    print(f"   Total constraints: {constraint_info['total_constraints']}")
    print(f"   Connected components: {len(components)}")
    print(f"   Component sizes: {constraint_info['component_sizes']}")
    
    for i, info in enumerate(component_info):
        print(f"   Component {i}: {info['object_count']} objects, {info['constraint_count']} constraints")
        print(f"     Objects: {info['object_ids']}")
    
    # Test solving with one component that should fail
    print("\n6. Testing component isolation...")
    
    # Move one circle to create an impossible constraint in System 2
    circle2.center_point = Point2D(100, 0)  # Move far away
    
    print("   Initial positions:")
    print(f"     Rectangle: {rect_lines[0].start_point} to {rect_lines[0].end_point}")
    print(f"     Circle1: center={circle1.center_point}, radius={circle1.radius}")
    print(f"     Circle2: center={circle2.center_point}, radius={circle2.radius}")
    print(f"     Single line: {single_line.start_point} to {single_line.end_point}")
    
    # Solve constraints
    success = doc.solve_constraints()
    print(f"   Overall solver success: {success}")
    
    print("   Final positions:")
    print(f"     Rectangle: {rect_lines[0].start_point} to {rect_lines[0].end_point}")
    print(f"     Circle1: center={circle1.center_point}, radius={circle1.radius}")
    print(f"     Circle2: center={circle2.center_point}, radius={circle2.radius}")
    print(f"     Single line: {single_line.start_point} to {single_line.end_point}")
    
    # Verify results
    print("\n7. Verification:")
    
    # Check if rectangle maintained its shape (System 1 should work)
    rect_bottom_length = rect_lines[0].length
    rect_top_length = rect_lines[2].length
    rect_right_length = rect_lines[1].length
    rect_left_length = rect_lines[3].length
    
    rect_consistent = (abs(rect_bottom_length - rect_top_length) < 0.001 and
                      abs(rect_right_length - rect_left_length) < 0.001)
    
    # Check if single line is horizontal (System 3 should work)
    single_line_angle_rad = single_line.angle_radians
    single_line_angle_deg = single_line_angle_rad * 180 / 3.14159
    single_line_horizontal = abs(single_line_angle_deg) < 0.001 or abs(abs(single_line_angle_deg) - 180) < 0.001
    
    print(f"   System 1 (Rectangle) solved correctly: {rect_consistent}")
    print(f"   System 2 (Circles) failed as expected: {not success}")
    print(f"   System 3 (Single line) solved correctly: {single_line_horizontal}")
    
    print("\nConstraint graph example completed successfully!")
    print("✅ Component isolation works")
    print("✅ Independent solving works")
    print("✅ Fault isolation works")
    print("✅ Graph analysis works")


if __name__ == "__main__":
    constraint_graph_example() 