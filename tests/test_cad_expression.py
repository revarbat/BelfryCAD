#!/usr/bin/env python3
"""
Test script for CadExpression class.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.cad_expression import CadExpression
import math


def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    print("Testing basic arithmetic...")
    
    expr = CadExpression()
    
    tests = [
        ("2 + 3", 5.0),
        ("2 - 3", -1.0),
        ("2 * 3", 6.0),
        ("6 / 2", 3.0),
        ("2 ^ 3", 8.0),
        ("10 % 3", 1.0),  # Note: % not supported, should fail
    ]
    
    for expression, expected in tests:
        try:
            result = expr.evaluate(expression)
            print(f"  {expression} = {result} (expected {expected})")
            if abs(result - expected) > 1e-10:
                print(f"    WARNING: Result differs from expected")
        except Exception as e:
            print(f"  {expression} raised: {e}")


def test_pemdas():
    """Test proper PEMDAS operation ordering."""
    print("\nTesting PEMDAS ordering...")
    
    expr = CadExpression()
    
    tests = [
        ("2 + 3 * 4", 14.0),  # Multiplication before addition
        ("2 * 3 + 4", 10.0),  # Multiplication before addition
        ("2 + 3 / 4", 2.75),  # Division before addition
        ("2 * 3 ^ 2", 18.0),  # Exponentiation before multiplication
        ("2 ^ 3 * 4", 32.0),  # Exponentiation before multiplication
        ("2 + 3 * 4 ^ 2", 50.0),  # Full PEMDAS: 2 + 3 * 16 = 2 + 48 = 50
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


def test_parentheses():
    """Test parentheses for grouping."""
    print("\nTesting parentheses...")
    
    expr = CadExpression()
    
    tests = [
        ("(2 + 3) * 4", 20.0),
        ("2 * (3 + 4)", 14.0),
        ("(2 + 3) ^ 2", 25.0),
        ("2 ^ (3 + 1)", 16.0),
        ("((2 + 3) * 4) / 2", 10.0),
        ("(2 + 3) * (4 + 5)", 45.0),
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


def test_unary_operators():
    """Test unary + and - operators."""
    print("\nTesting unary operators...")
    
    expr = CadExpression()
    
    tests = [
        ("-5", -5.0),
        ("+5", 5.0),
        ("-2 * -3", 6.0),
        ("2 * -3", -6.0),
        ("-2 ^ 3", -8.0),
        ("(-2) ^ 3", -8.0),
        ("-2 ^ 2", -4.0),  # -(2²) = -4 (standard mathematical notation)
        ("(-2) ^ 2", 4.0),
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


def test_exponentiation():
    """Test exponentiation with right-associativity."""
    print("\nTesting exponentiation...")
    
    expr = CadExpression()
    
    tests = [
        ("2 ^ 3", 8.0),
        ("2 ^ 3 ^ 2", 512.0),  # Right-associative: 2^(3^2) = 2^9 = 512
        ("(2 ^ 3) ^ 2", 64.0),  # Left-associative with parentheses: (2^3)^2 = 8^2 = 64
        ("2 ^ 0", 1.0),
        ("2 ^ 1", 2.0),
        ("2 ^ -1", 0.5),
        ("0 ^ 0", 1.0),  # Python convention
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


def test_variables():
    """Test variable support."""
    print("\nTesting variables...")
    
    expr = CadExpression({
        'radius': '5.0',
        'height': '10.0',
        'pi': '3.14159',
        'x': '2.0',
        'y': '3.0',
        'zero': '0.0',
        'one': '1.0',
    })
    
    tests = [
        ("$radius", 5.0),
        ("$radius * 2", 10.0),
        ("$radius + $height", 15.0),
        ("$pi * $radius ^ 2", 78.53975),  # Area of circle
        ("$x + $y", 5.0),
        ("$x * $y", 6.0),
        ("$x ^ 2 + $y ^ 2", 13.0),  # x² + y²
        ("($x + $y) ^ 2", 25.0),  # (x + y)²
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-5, f"Expected {expected}, got {result}"


def test_complex_expressions():
    """Test complex expressions with multiple operations."""
    print("\nTesting complex expressions...")
    
    expr = CadExpression({
        'radius': '5.0',
        'height': '10.0',
        'pi': '3.14159',
        'x': '2.0',
        'y': '3.0',
    })
    
    tests = [
        ("($radius + $height) * 2", 30.0),
        ("$pi * $radius ^ 2 / 2", 39.269875),  # Half circle area
        ("$x ^ 2 + $y ^ 2", 13.0),  # x² + y²
        ("($x + $y) ^ 2", 25.0),  # (x + y)²
        ("2 * ($x + $y) ^ 2", 50.0),  # 2 * (x + y)²
        ("($x + $y) ^ 2 * 2", 50.0),  # (x + y)² * 2
        ("-$x ^ 2", -4.0),  # -(x²)
        ("(-$x) ^ 2", 4.0),  # (-x)²
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-5, f"Expected {expected}, got {result}"


def test_error_handling():
    """Test error handling for invalid expressions."""
    print("\nTesting error handling...")
    
    expr = CadExpression()
    
    error_tests = [
        ("1 / 0", "Division by zero"),
        ("unknown_var", "Variable 'unknown_var' not found"),
        ("2 +", "Unexpected token"),
        ("(2 + 3", "Expected RPAREN"),
        ("2 + 3)", "Unexpected token"),
        ("", "Empty expression"),
        # ("2 % 3", "Invalid character"),  # % is actually supported
        ("2 & 3", "Invalid character"),  # & not supported
        ("2 | 3", "Invalid character"),  # | not supported
    ]
    
    for expression, expected_error in error_tests:
        try:
            result = expr.evaluate(expression)
            print(f"  ERROR: {expression} should have failed but returned {result}")
            assert False, f"Expected error for {expression}"
        except (ValueError, KeyError) as e:
            print(f"  ✓ {expression} correctly raised: {e}")


def test_variable_management():
    """Test variable management methods."""
    print("\nTesting variable management...")
    
    expr = CadExpression()
    
    # Test setting variables
    expr.set_variable('x', '5.0')
    expr.set_variable('y', '10.0')
    
    result = expr.evaluate('$x + $y')
    print(f"  $x + $y = {result} (expected 15.0)")
    assert result == 15.0
    
    # Test getting variables
    x_val = expr.get_variable('x')
    print(f"  get_variable('x') = {x_val} (expected 5.0)")
    assert x_val == 5.0
    
    # Test getting non-existent variable
    try:
        unknown_val = expr.get_variable('unknown')
        print(f"  ERROR: get_variable('unknown') should have failed but returned {unknown_val}")
        assert False
    except ValueError as e:
        print(f"  ✓ get_variable('unknown') correctly raised: {e}")
    
    # Test clearing variables
    expr.clear_variables()
    try:
        result = expr.evaluate('$x + $y')
        print(f"  ERROR: Should have failed after clearing variables")
        assert False
    except ValueError as e:
        print(f"  ✓ Correctly failed after clearing variables: {e}")


def test_floating_point():
    """Test floating point arithmetic."""
    print("\nTesting floating point arithmetic...")
    
    expr = CadExpression()
    
    tests = [
        ("2.5 + 3.5", 6.0),
        ("2.5 * 3.0", 7.5),
        ("10.0 / 4.0", 2.5),
        ("2.5 ^ 2", 6.25),
        ("3.14159 * 2", 6.28318),
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-5, f"Expected {expected}, got {result}"


def test_constants_and_aliases():
    print("\nTesting constants and aliases...")
    expr = CadExpression()
    tests = [
        ("e", math.e),
        ("pi", math.pi),
        ("π", math.pi),
        ("phi", (1 + math.sqrt(5)) / 2),
        ("ɸ", (1 + math.sqrt(5)) / 2),
    ]
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10

def test_functions():
    print("\nTesting math functions...")
    expr = CadExpression({'x': '0.5', 'y': '0.25'})
    tests = [
        ("sin($x)", math.sin(0.5)),
        ("cos($x)", math.cos(0.5)),
        ("tan($x)", math.tan(0.5)),
        ("asin($x)", math.asin(0.5)),
        ("acos($x)", math.acos(0.5)),
        ("atan($x)", math.atan(0.5)),
        ("atan2($x, $y)", math.atan2(0.5, 0.25)),
        ("pow($x, 2)", math.pow(0.5, 2)),
        ("sqrt($x)", math.sqrt(0.5)),
        ("exp($x)", math.exp(0.5)),
        ("log10($x)", math.log10(0.5)),
        ("log2($x)", math.log2(0.5)),
        ("ln($x)", math.log(0.5)),
        ("abs(-2)", abs(-2)),
        ("sign(-2)", -1),
        ("sign(0)", 0),
        ("sign(2)", 1),
        ("floor(2.7)", math.floor(2.7)),
        ("ceil(2.1)", math.ceil(2.1)),
        ("round(2.5)", round(2.5)),
        ("min(2, 3, 1)", 1),
        ("max(2, 3, 1)", 3),
        ("hypot(3, 4)", 5),
        ("deg(pi)", 180),
        ("rad(180)", math.pi),
    ]
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-8

def test_variable_syntax():
    print("\nTesting $variable syntax...")
    expr = CadExpression({'foo': '42'})
    assert expr.evaluate("$foo") == 42
    try:
        expr.evaluate("foo")
        assert False, "Should require $ for variable"
    except ValueError as e:
        print(f"  ✓ Missing $ for variable correctly raised: {e}")

def test_degree_suffix():
    """Test degree suffix (º) as a postfix operator."""
    print("\nTesting degree suffix (º)...")
    expr = CadExpression()
    
    # Test basic degree conversion
    deg_val = 180
    result = expr.evaluate(f"{deg_val}º")
    print(f"  {deg_val}º = {result} (expected {math.radians(deg_val)})")
    assert abs(result - math.radians(deg_val)) < 1e-10
    
    # Test degree suffix in expressions
    result = expr.evaluate("90º + 45º")
    expected = math.radians(90) + math.radians(45)
    print(f"  90º + 45º = {result} (expected {expected})")
    assert abs(result - expected) < 1e-10
    
    # Test degree suffix with variables
    expr.set_variable('angle', '60')
    result = expr.evaluate("$angleº")
    expected = math.radians(60)
    print(f"  $angleº = {result} (expected {expected})")
    assert abs(result - expected) < 1e-10
    
    # Test degree suffix in function calls
    result = expr.evaluate("sin(30º)")
    expected = math.sin(math.radians(30))
    print(f"  sin(30º) = {result} (expected {expected})")
    assert abs(result - expected) < 1e-10
    
    # Test degree suffix in complex expressions
    result = expr.evaluate("(45º + 30º) * 2")
    expected = (math.radians(45) + math.radians(30)) * 2
    print(f"  (45º + 30º) * 2 = {result} (expected {expected})")
    assert abs(result - expected) < 1e-10
    
    # Test degree suffix with constants
    result = expr.evaluate("pi * 90º")
    expected = math.pi * math.radians(90)
    print(f"  pi * 90º = {result} (expected {expected})")
    assert abs(result - expected) < 1e-10

def test_errors():
    print("\nTesting error handling for unknowns...")
    expr = CadExpression()
    try:
        expr.evaluate("unknownfunc(2)")
        assert False, "Should error on unknown function"
    except ValueError as e:
        print(f"  ✓ Unknown function correctly raised: {e}")
    try:
        expr.evaluate("unknownconst")
        assert False, "Should error on unknown constant"
    except ValueError as e:
        print(f"  ✓ Unknown constant correctly raised: {e}")
    try:
        expr.evaluate("$unknownvar")
        assert False, "Should error on unknown variable"
    except KeyError as e:
        print(f"  ✓ Unknown variable correctly raised: {e}")

def test_whitespace_handling():
    print("\nTesting whitespace handling...")
    expr = CadExpression({'foo': '2', 'bar': '3'})
    # Whitespace between tokens
    assert expr.evaluate("  $foo   +   $bar ") == 5
    assert expr.evaluate("sin ( 30º ) + cos ( 0 )") == (math.sin(math.radians(30)) + math.cos(0))
    # Whitespace inside variable name should not be allowed (should raise error or treat as two tokens)
    try:
        expr.evaluate("$foo bar")
        print("  ERROR: $foo bar should not be a valid variable name")
        assert False
    except Exception as e:
        print(f"  ✓ $foo bar correctly raised: {e}")
    # Whitespace inside function name should not be allowed (should treat as two tokens)
    try:
        expr.evaluate("sin cos(0)")
        print("  ERROR: sin cos(0) should not be a valid function name")
        assert False
    except Exception as e:
        print(f"  ✓ sin cos(0) correctly raised: {e}")

def test_deep_parameter_subexpressions():
    print("\nTesting deep parameter subexpressions...")
    expr = CadExpression({
        'a': '2',
        'b': '$a + 3',
        'c': '$b * 4',
        'd': '$c - $a',
    })
    # d = ( ( (2) + 3 ) * 4 ) - 2 = (5 * 4) - 2 = 20 - 2 = 18
    assert expr.get_variable('d') == 18
    # Change a and check propagation
    expr.set_variable('a', '10')  # Pass as string
    # d = ( ( (10) + 3 ) * 4 ) - 10 = (13 * 4) - 10 = 52 - 10 = 42
    assert expr.get_variable('d') == 42
    print("  ✓ Deep parameter subexpressions work and propagate correctly.")


def main():
    """Run all CadExpression tests."""
    print("Running CadExpression comprehensive tests...")
    
    try:
        test_basic_arithmetic()
        test_pemdas()
        test_parentheses()
        test_unary_operators()
        test_exponentiation()
        test_variables()
        test_complex_expressions()
        test_error_handling()
        test_variable_management()
        test_floating_point()
        test_constants_and_aliases()
        test_functions()
        test_variable_syntax()
        test_degree_suffix()
        test_whitespace_handling()
        test_deep_parameter_subexpressions()
        print("\nAll CadExpression tests passed! ✓")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 