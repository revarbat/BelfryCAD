#!/usr/bin/env python3
"""
Example usage of CadExpression for CAD calculations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.cad_expression import CadExpression


def main():
    """Demonstrate CadExpression usage for CAD calculations."""
    print("CadExpression Example - CAD Mathematical Expressions")
    print("=" * 50)
    
    # Create an expression evaluator with CAD variables
    expr = CadExpression({
        'radius': "10.0",
        'height': "25.0",
        'width': "15.0",
        'pi': "3.14159",
        'thickness': "2.0",
        'clearance': "0.5",
    })
    
    print("Available variables:")
    for var, value in expr.expressions.items():
        print(f"  {var} = {value}")
    print()
    
    # Example 1: Circle calculations
    print("Circle Calculations:")
    expressions = [
        ("pi * radius ^ 2", "Area of circle"),
        ("2 * pi * radius", "Circumference"),
        ("pi * radius ^ 2 / 2", "Half circle area"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.4f} ({description})")
    print()
    
    # Example 2: Rectangle calculations
    print("Rectangle Calculations:")
    expressions = [
        ("width * height", "Area of rectangle"),
        ("2 * (width + height)", "Perimeter"),
        ("width * height * thickness", "Volume"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.4f} ({description})")
    print()
    
    # Example 3: Complex CAD calculations
    print("Complex CAD Calculations:")
    expressions = [
        ("pi * (radius + clearance) ^ 2", "Area with clearance"),
        ("(width + 2 * thickness) * (height + 2 * thickness)", "Outer dimensions"),
        ("pi * radius ^ 2 * height", "Cylinder volume"),
        ("2 * pi * radius * height", "Cylinder surface area"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.4f} ({description})")
    print()
    
    # Example 4: Dynamic variable updates
    print("Dynamic Variable Updates:")
    print("  Original radius = 10.0")
    
    # Update radius and recalculate
    expr.set_variable('radius', 15.0)
    result = expr.evaluate("pi * radius ^ 2")
    print(f"  New radius = 15.0, Area = {result:.4f}")
    
    # Update multiple variables
    expr.set_variable('height', 30.0)
    expr.set_variable('width', 20.0)
    result = expr.evaluate("width * height")
    print(f"  New dimensions: {expr.get_variable('width')} x {expr.get_variable('height')}")
    print(f"  New area = {result:.4f}")
    print()
    
    # Example 5: Error handling
    print("Error Handling:")
    error_expressions = [
        ("1 / 0", "Division by zero"),
        ("unknown_var", "Undefined variable"),
        ("2 +", "Incomplete expression"),
        ("(2 + 3", "Unmatched parentheses"),
    ]
    
    for expression, expected_error in error_expressions:
        try:
            result = expr.evaluate(expression)
            print(f"  ERROR: {expression} should have failed but returned {result}")
        except Exception as e:
            print(f"  ✓ {expression}: {e}")
    print()
    
    # Example 6: Advanced mathematical expressions
    print("Advanced Mathematical Expressions:")
    expressions = [
        ("(radius + clearance) ^ 2 - radius ^ 2", "Annulus area"),
        ("sqrt(radius ^ 2 + height ^ 2)", "Diagonal (if sqrt supported)"),
        ("(width + height) / 2", "Average dimension"),
        ("-radius ^ 2", "Negative area"),
        ("(-radius) ^ 2", "Squared negative radius"),
    ]
    
    for expression, description in expressions:
        try:
            result = expr.evaluate(expression)
            print(f"  {expression} = {result:.4f} ({description})")
        except Exception as e:
            print(f"  {expression}: {e}")
    
    print("\nCadExpression is ready for CAD calculations! ✓")


if __name__ == "__main__":
    main() 