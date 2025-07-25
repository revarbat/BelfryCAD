#!/usr/bin/env python3
"""
Enhanced example usage of CadExpression with all new features.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.cad_expression import CadExpression
import math


def main():
    """Demonstrate enhanced CadExpression features."""
    print("Enhanced CadExpression Example")
    print("=" * 40)
    
    # Create an expression evaluator with CAD variables
    expr = CadExpression({
        'radius': "10.0",
        'height': "25.0",
        'angle': "45.0",
        'thickness': "2.0",
    })
    
    print("Available variables:")
    for var, value in expr.expressions.items():
        print(f"  ${var} = {value}")
    print()
    
    # Example 1: Constants and aliases
    print("Constants and Aliases:")
    expressions = [
        ("e", "Euler's number"),
        ("pi", "Pi"),
        ("π", "Pi (Unicode)"),
        ("phi", "Golden ratio"),
        ("ɸ", "Golden ratio (Unicode)"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.6f} ({description})")
    print()
    
    # Example 2: Math functions
    print("Math Functions:")
    expressions = [
        ("sin(30º)", "Sine of 30 degrees"),
        ("cos(60º)", "Cosine of 60 degrees"),
        ("tan(45º)", "Tangent of 45 degrees"),
        ("sqrt(16)", "Square root of 16"),
        ("pow(2, 8)", "2 to the power of 8"),
        ("abs(-42)", "Absolute value of -42"),
        ("floor(3.7)", "Floor of 3.7"),
        ("ceil(3.2)", "Ceiling of 3.2"),
        ("round(3.5)", "Round 3.5"),
        ("min(5, 3, 8, 1)", "Minimum of 5, 3, 8, 1"),
        ("max(5, 3, 8, 1)", "Maximum of 5, 3, 8, 1"),
        ("hypot(3, 4)", "Hypotenuse of 3-4-5 triangle"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.6f} ({description})")
    print()
    
    # Example 3: Variables with $ syntax
    print("Variables with $ Syntax:")
    expressions = [
        ("$radius", "Radius variable"),
        ("$radius * 2", "Diameter"),
        ("$height", "Height variable"),
        ("$angle", "Angle variable"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.6f} ({description})")
    print()
    
    # Example 4: Degree suffix (º) as postfix operator
    print("Degree Suffix (º) as Postfix Operator:")
    expressions = [
        ("90º", "90 degrees in radians"),
        ("180º", "180 degrees in radians"),
        ("$angleº", "Variable angle in radians"),
        ("30º + 45º", "Sum of 30° and 45° in radians"),
        ("sin(60º)", "Sine of 60 degrees"),
        ("cos($angleº)", "Cosine of variable angle"),
        ("(45º + 30º) * 2", "Complex expression with degrees"),
        ("pi * 90º", "Pi times 90 degrees"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.6f} ({description})")
    print()
    
    # Example 5: Complex CAD calculations
    print("Complex CAD Calculations:")
    expressions = [
        ("pi * $radius ^ 2", "Circle area"),
        ("2 * pi * $radius", "Circle circumference"),
        ("sin($angleº) * $radius", "Y-component of radius at angle"),
        ("cos($angleº) * $radius", "X-component of radius at angle"),
        ("sqrt($radius^2 + $height^2)", "Diagonal distance"),
        ("atan2($height, $radius)", "Angle from radius to diagonal"),
        ("deg(atan2($height, $radius))", "Angle in degrees"),
    ]
    
    for expression, description in expressions:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result:.6f} ({description})")
    print()
    
    # Example 6: Error handling
    print("Error Handling:")
    error_expressions = [
        ("$unknown", "Undefined variable"),
        ("unknown_func(2)", "Unknown function"),
        ("unknown_const", "Unknown constant"),
        ("sin()", "Function with no arguments"),
        ("2 +", "Incomplete expression"),
    ]
    
    for expression, description in error_expressions:
        try:
            result = expr.evaluate(expression)
            print(f"  ERROR: {expression} should have failed but returned {result}")
        except Exception as e:
            print(f"  ✓ {expression}: {e}")
    print()
    
    # Example 7: Dynamic updates
    print("Dynamic Variable Updates:")
    print("  Original angle = 45°")
    expr.set_variable('angle', 90)
    result = expr.evaluate("sin($angleº)")
    print(f"  Updated angle = 90°, sin($angleº) = {result:.6f}")
    
    expr.set_variable('radius', 15)
    result = expr.evaluate("pi * $radius ^ 2")
    print(f"  Updated radius = 15, area = {result:.6f}")
    
    print("\nEnhanced CadExpression is ready for advanced CAD calculations! ✓")


if __name__ == "__main__":
    main() 