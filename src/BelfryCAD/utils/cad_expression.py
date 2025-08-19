# -*- coding: utf-8 -*-

"""
belfrycad.utils.cad_expression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
CadExpression - A mathematical expression evaluator for CAD calculations.

Supports:
- Basic arithmetic: +, -, *, /, % (modulo)
- Exponentiation: ^ or **
- Unary operators: +, -
- Parentheses for grouping
- Variables with values stored in a dictionary, referenced as $name
- Proper PEMDAS operation ordering
- Float number literals
- Constants: e, pi, phi, π (alias for pi), ɸ (alias for phi)
- Math functions: sin, cos, tan, asin, acos, atan, atan2, pow, sqrt, exp,
  log10, log2, ln, abs, sign, floor, ceil, round, min, max, hypot, deg, rad
- With a suffix of º or °, the result is converted from degrees to radians
- With a suffix of ², the result is squared
- With a suffix of ³, the result is cubed
- With a suffix of ', the result is converted from feet to inches (12x)
- With a suffix of ", the result is left unchanged (Inches).
"""

import re
import math
from typing import Dict, Union, List, Tuple, Callable


class CadExpression:
    """
    A mathematical expression evaluator for CAD calculations.

    Supports:
    - Basic arithmetic: +, -, *, /, % (modulo)
    - Exponentiation: ^ or **
    - Unary operators: +, -
    - Parentheses for grouping
    - Variables with values stored in a dictionary, referenced as $name
    - Proper PEMDAS operation ordering
    - Float number literals
    - Constants: e, pi, phi, π (alias for pi), ɸ (alias for phi)
    - Math functions: sin, cos, tan, asin, acos, atan, atan2, pow, sqrt, exp,
      log10, log2, ln, abs, sign, floor, ceil, round, min, max, hypot, deg, rad
    - With a suffix of º or °, the result is converted from degrees to radians
    - With a suffix of ², the result is squared
    - With a suffix of ³, the result is cubed
    - With a suffix of ', the result is converted from feet to inches (12x)
    - With a suffix of ", the result is left unchanged (Inches).
    - Parameters store their expressions as strings, not just values.
    - When a parameter is referenced, its expression is evaluated recursively.
    - Cycle detection prevents infinite recursion.
    """

    _CONSTANTS = {
        'e': math.e,
        'pi': math.pi,
        'π': math.pi,
        'phi': (1 + math.sqrt(5)) / 2,
        'ɸ': (1 + math.sqrt(5)) / 2,
    }

    _FUNCTIONS: Dict[str, Callable] = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'atan2': math.atan2,
        'pow': math.pow,
        'sqrt': math.sqrt,
        'exp': math.exp,
        'log10': math.log10,
        'log2': math.log2,
        'ln': math.log,
        'abs': abs,
        'sign': lambda x: (x > 0) - (x < 0),
        'floor': math.floor,
        'ceil': math.ceil,
        'round': round,
        'min': min,
        'max': max,
        'hypot': math.hypot,
        'deg': math.degrees,
        'rad': math.radians,
    }

    def __init__(self, expressions: Dict[str, str] | None = None):
        self.expressions = expressions or {}  # param name -> expression string
        self._tokens = []
        self._current_token_index = 0
        self._token_cache = {}  # expression string -> token list

    def set_variable(self, name: str, expr):
        """Set a parameter's expression (as a string)."""
        self.expressions[name] = str(expr)

    def get_variable(self, name: str, _seen=None) -> float:
        """Evaluate a parameter by recursively evaluating its expression."""
        if name not in self.expressions:
            raise ValueError(f"Variable '{name}' not found")
        if _seen is None:
            _seen = set()
        if name in _seen:
            raise ValueError(f"Cyclic dependency detected in parameter '{name}'")
        _seen.add(name)
        expr_str = self.expressions[name]
        # Save current parsing state
        old_tokens = self._tokens
        old_index = self._current_token_index
        old_seen = getattr(self, '_seen', None)
        # Evaluate the variable's expression
        result = self.evaluate(expr_str, _seen=_seen)
        # Restore parsing state
        self._tokens = old_tokens
        self._current_token_index = old_index
        if old_seen is not None:
            self._seen = old_seen
        else:
            if hasattr(self, '_seen'):
                delattr(self, '_seen')
        _seen.remove(name)  # Remove variable from _seen after evaluation
        return result

    def clear_variables(self):
        self.expressions.clear()

    def evaluate(self, expression: str, _seen=None) -> float:
        expression = expression.strip()
        if not expression:
            raise ValueError("Empty expression")
        self._tokens = self._tokenize(expression)
        self._current_token_index = 0
        self._seen = _seen  # For cycle detection in variable evaluation
        result = self._parse_expression()
        if self._current_token_index < len(self._tokens):
            raise ValueError(f"Unexpected token: {self._tokens[self._current_token_index]}")
        return result

    def _tokenize(self, expression: str) -> List[Tuple[str, str]]:
        if expression in self._token_cache:
            return self._token_cache[expression]
        patterns = [
            (r'\s+', None),
            (r'(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?', 'NUMBER'),
            (r'\$[a-zA-Z_][a-zA-Z0-9_]*', 'VARIABLE'),
            (r'[a-zA-Z_πɸ][a-zA-Z0-9_πɸ]*', 'IDENT'),  # function names, constants, π, ɸ
            (r'\+', 'PLUS'),
            (r'-', 'MINUS'),
            (r'\*', 'MULTIPLY'),
            (r'/', 'DIVIDE'),
            (r'%', 'MODULO'),
            (r'(\^|\*\*)', 'POWER'),
            (r',', 'COMMA'),
            (r'\(', 'LPAREN'),
            (r'\)', 'RPAREN'),
            # The degree sign (º, 0xb0) and the masculine ordinal indicator (°, 0xba)
            # look almost exactly the same, so we accept either.
            (r'(º|°)', 'DEGREE_SUFFIX'),  # Postfix degree operator
            (r'²', 'SQUARE_SUFFIX'),  # Postfix square operator
            (r'³', 'CUBE_SUFFIX'),  # Postfix cube operator
            (r"'", 'FOOT_SUFFIX'),  # Postfix foot operator
            (r'"', 'INCH_SUFFIX'),  # Postfix inch operator
        ]
        tokens = []
        pos = 0
        while pos < len(expression):
            match = None
            for pattern, token_type in patterns:
                regex = re.compile(pattern)
                match = regex.match(expression, pos)
                if match:
                    if token_type is not None:
                        tokens.append((token_type, match.group()))
                    pos = match.end()
                    break
            if not match:
                raise ValueError(f"Invalid character at position {pos}: '{expression[pos]}'")
        self._token_cache[expression] = tokens
        return tokens

    def _current_token(self) -> Tuple[str, str]:
        if self._current_token_index >= len(self._tokens):
            return ("", "")
        return self._tokens[self._current_token_index]

    def _advance(self):
        self._current_token_index += 1

    def _expect(self, expected_type: str):
        token_type, token_value = self._current_token()
        if token_type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {token_type}: '{token_value}'")
        self._advance()
        return token_value

    def _parse_expression(self) -> float:
        left = self._parse_term()
        while True:
            token_type, token_value = self._current_token()
            if token_type == 'PLUS':
                self._advance()
                left += self._parse_term()
            elif token_type == 'MINUS':
                self._advance()
                left -= self._parse_term()
            else:
                break
        return left

    def _parse_unary_expression(self) -> float:
        token_type, token_value = self._current_token()
        if token_type == 'PLUS':
            self._advance()
            return self._parse_unary_expression()
        elif token_type == 'MINUS':
            self._advance()
            return -self._parse_unary_expression()
        else:
            return self._parse_power()

    def _parse_term(self) -> float:
        left = self._parse_unary_expression()
        while True:
            token_type, token_value = self._current_token()
            if token_type == 'MULTIPLY':
                self._advance()
                left *= self._parse_unary_expression()
            elif token_type == 'DIVIDE':
                self._advance()
                divisor = self._parse_unary_expression()
                if divisor == 0:
                    raise ValueError("Division by zero")
                left /= divisor
            elif token_type == 'MODULO':
                self._advance()
                divisor = self._parse_unary_expression()
                if divisor == 0:
                    raise ValueError("Modulo by zero")
                left %= divisor
            else:
                break
        return left

    def _parse_power(self) -> float:
        left = self._parse_factor()
        token_type, token_value = self._current_token()
        if token_type == 'POWER':
            self._advance()
            right = self._parse_unary_expression()
            return left ** right
        return left

    def _parse_factor(self) -> float:
        token_type, token_value = self._current_token()
        if token_type == 'LPAREN':
            self._advance()
            result = self._parse_expression()
            self._expect('RPAREN')
            return self._parse_postfix_operators(result)
        elif token_type == 'NUMBER':
            self._advance()
            result = float(token_value)
            return self._parse_postfix_operators(result)
        elif token_type == 'VARIABLE':
            self._advance()
            varname = token_value[1:]  # Remove leading $
            # Recursively evaluate the variable's expression
            var_result = self.get_variable(varname, _seen=getattr(self, '_seen', None))
            return self._parse_postfix_operators(var_result)
        elif token_type == 'IDENT':
            # Could be a constant or a function call
            ident = token_value
            self._advance()
            next_type, _ = self._current_token()
            if next_type == 'LPAREN':
                result = self._parse_function_call(ident)
                return self._parse_postfix_operators(result)
            # Constant
            if ident in self._CONSTANTS:
                result = self._CONSTANTS[ident]
                return self._parse_postfix_operators(result)
            raise ValueError(f"Unknown identifier: {ident}")
        else:
            raise ValueError(f"Unexpected token: {token_type} '{token_value}'")

    def _parse_function_call(self, func_name: str) -> float:
        self._expect('LPAREN')
        args = []
        # Support zero-argument functions
        if self._current_token()[0] == 'RPAREN':
            self._advance()
            if func_name not in self._FUNCTIONS:
                raise ValueError(f"Unknown function: {func_name}")
            return self._FUNCTIONS[func_name]()
        while True:
            args.append(self._parse_expression())
            token_type, _ = self._current_token()
            if token_type == 'COMMA':
                self._advance()
            elif token_type == 'RPAREN':
                self._advance()
                break
            else:
                raise ValueError(f"Expected ',' or ')', got {token_type}")
        if func_name not in self._FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")
        try:
            return self._FUNCTIONS[func_name](*args)
        except Exception as e:
            raise ValueError(f"Error in function '{func_name}': {e}")

    def _parse_postfix_operators(self, value: float) -> float:
        """Parse postfix operators like º (degree to radian conversion)."""
        token_type, token_value = self._current_token()
        if token_type == 'DEGREE_SUFFIX':
            self._advance()
            return math.radians(value)
        elif token_type == 'SQUARE_SUFFIX':
            self._advance()
            return value * value
        elif token_type == 'CUBE_SUFFIX':
            self._advance()
            return value * value * value
        elif token_type == 'FOOT_SUFFIX':
            self._advance()
            return value * 12.0
        elif token_type == 'INCH_SUFFIX':
            self._advance()
            return value
        return value


def test_cad_expression():
    """Test the CadExpression class with various expressions."""
    print("Testing CadExpression...")
    
    # Create expression evaluator with some variables
    expr = CadExpression({
        'radius': "5.0",
        'height': "10.0",
        'pi': "3.14159",
        'x': "2.0",
        'y': "3.0"
    })
    
    # Test basic arithmetic
    tests = [
        ("2 + 3", 5.0),
        ("2 - 3", -1.0),
        ("2 * 3", 6.0),
        ("6 / 2", 3.0),
        ("2 ^ 3", 8.0),
        ("2 + 3 * 4", 14.0),  # PEMDAS: multiplication first
        ("(2 + 3) * 4", 20.0),  # Parentheses override PEMDAS
        ("2 ^ 3 ^ 2", 512.0),  # Right-associative: 2^(3^2) = 2^9 = 512
        ("-5", -5.0),
        ("+5", 5.0),
        ("2 * -3", -6.0),
        ("-2 * -3", 6.0),
    ]
    
    for expression, expected in tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"
    
    # Test variables
    var_tests = [
        ("radius", 5.0),
        ("radius * 2", 10.0),
        ("radius + height", 15.0),
        ("pi * radius ^ 2", 78.53975),  # Area of circle
        ("x + y", 5.0),
        ("x * y", 6.0),
    ]
    
    for expression, expected in var_tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-5, f"Expected {expected}, got {result}"
    
    # Test complex expressions
    complex_tests = [
        ("(radius + height) * 2", 30.0),
        ("pi * radius ^ 2 / 2", 39.269875),  # Half circle area
        ("x ^ 2 + y ^ 2", 13.0),  # x² + y²
        ("(x + y) ^ 2", 25.0),  # (x + y)²
    ]
    
    for expression, expected in complex_tests:
        result = expr.evaluate(expression)
        print(f"  {expression} = {result} (expected {expected})")
        assert abs(result - expected) < 1e-5, f"Expected {expected}, got {result}"
    
    # Test error cases
    error_tests = [
        ("1 / 0", "Division by zero"),
        ("unknown_var", "Variable 'unknown_var' not found"),
        ("2 +", "Unexpected token"),
        ("(2 + 3", "Expected RPAREN"),
    ]
    
    for expression, expected_error in error_tests:
        try:
            result = expr.evaluate(expression)
            print(f"  ERROR: {expression} should have failed but returned {result}")
            assert False, f"Expected error for {expression}"
        except (ValueError, KeyError) as e:
            print(f"  ✓ {expression} correctly raised: {e}")
    
    print("  ✓ All CadExpression tests passed!")


if __name__ == "__main__":
    test_cad_expression() 
