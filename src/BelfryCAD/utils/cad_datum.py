# 
import math
import numbers
from typing import Optional
from .cad_expression import CadExpression


class CadDatum(numbers.Real):
    def __init__(self, cad_expr: CadExpression, value = None, fixed = False):
        self.cad_expr: CadExpression = cad_expr
        self.value: Optional[float] = None
        self.expr: Optional[str] = None
        self.fixed: bool = fixed
        if value is not None:
            self.set(value, fixed)

    def recalculate(self):
        if self.expr is None:
            raise ValueError(f"Cannot evaluate: {self.expr}")
        val = self.cad_expr.evaluate(self.expr)
        if val is None:
            raise ValueError(f"Cannot evaluate: {val}")
        self.value = val

    def set(self, arg, fixed=False):
        if isinstance(arg, (int, float)):
            self.value = float(arg)
            self.fixed = fixed
        elif isinstance(arg, str):
            self.value = None
            self.expr = arg
            self.fixed = True
            self.recalculate()

    def __repr__(self):
        if self.expr is not None:
            if self.value is None:
                try:
                    self.recalculate()
                except(ValueError):
                    pass
            if self.value is None:
                return f"CadDatum({self.expr})"
            return f"CadDatum({self.expr} = {self.value})"
        if self.value is not None:
            return f"CadDatum(self.value)"
        return f"CadDatum(uninitialized)"

    def __str__(self):
        if self.value is not None:
            return str(self.value)
        if self.expr is not None:
            try:
                self.recalculate()
            except(ValueError):
                pass
            if self.value is not None:
                return str(self.value)
            return self.expr
        return "None"

    def __float__(self):
        if self.value is not None:
            return self.value
        if self.expr is not None:
            self.recalculate()
            if self.value is not None:
                return self.value
        raise ValueError(f"Uninitialized")

    def __abs__(self):
        return abs(float(self))

    def __trunc__(self):
        return math.trunc(float(self))

    def __floor__(self):
        return math.floor(float(self))
        
    def __ceil__(self):
        return math.ceil(float(self))
        
    def __round__(self, ndigits=None):
        return round(float(self), ndigits)
        
    def __add__(self, other):
        return float(self) + other

    def __radd__(self, other):
        return other + float(self)

    def __sub__(self, other):
        return float(self) - other

    def __rsub__(self, other):
        return other - float(self)

    def __mul__(self, other):
        return float(self) * other
    
    def __rmul__(self, other):
        return other * float(self)

    def __truediv__(self, other):
        return float(self) / other
    
    def __rtruediv__(self, other):
        return other / float(self)

    def __floordiv__(self, other):
        return float(self) // other
    
    def __rfloordiv__(self, other):
        return other // float(self)

    def __mod__(self, other):
        return float(self) % other
    
    def __rmod__(self, other):
        return other % float(self)

    def __pow__(self, other):
        return float(self) ** other

    def __rpow__(self, other):
        return other ** float(self)

    def _coerce(self, other):
        return float(other)

    def __eq__(self, other):
        return float(self) == other

    def __lt__(self, other):
        return float(self) < other

    def __le__(self, other):
        return float(self) <= other

    def __neg__(self):
        return -float(self)

    def __pos__(self):
        return float(self)

    def __int__(self):
        return int(float(self))
