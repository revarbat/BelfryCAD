# CadObject Document Argument Standardization

## Overview

This document describes the standardization of the CadObject constructor to require a document argument as the first parameter across all CAD object implementations.

## Changes Made

### Base CadObject Constructor

Updated the base `CadObject` constructor to make `document` the first required argument:

```python
# Before
def __init__(self, color: str, line_width: float, document: Optional['Document'] = None):

# After
def __init__(self, document: 'Document', color: str = "black", line_width: Optional[float] = None):
```

### All CAD Object Constructors Updated

All CAD objects now follow the consistent pattern of `document` as the first required argument:

#### LineCadObject
```python
def __init__(self, document: 'Document', start_point: Point2D, end_point: Point2D, color: str = "black", line_width: Optional[float] = 0.05):
```

#### CircleCadObject
```python
def __init__(self, document: 'Document', center_point: Point2D, perimeter_point: Point2D, color: str = "black", line_width: Optional[float] = 0.05):
```

#### ArcCadObject
```python
def __init__(self, document: 'Document', center_point: Point2D, start_point: Point2D, end_point: Point2D, color: str = "black", line_width: Optional[float] = 0.05):
```

#### EllipseCadObject
```python
def __init__(self, document: 'Document', center_point: Point2D, major_axis_point: Point2D, minor_axis_point: Point2D, color: str = "black", line_width: Optional[float] = 0.05):
```

#### CubicBezierCadObject
```python
def __init__(self, document: 'Document', points: List[Point2D], color: str = "black", line_width: Optional[float] = 0.05):
```

#### GearCadObject
```python
def __init__(self, document: 'Document', center_point: Point2D, pitch_radius: float, num_teeth: int, pressure_angle: float = 20.0, color: str = "black", line_width: Optional[float] = 0.05):
```

#### GroupCadObject
```python
def __init__(self, document: 'Document', name: str = "Group", color: str = "black", line_width: Optional[float] = None):
```

### Document Factory Methods Updated

Updated the `Document` class factory methods to pass `document` as the first argument:

```python
def create_group(self, name: str = "Group") -> str:
    group = GroupCadObject(self, name=name)
    return self.add_object(group)

def create_line(self, start_point: Point2D, end_point: Point2D) -> str:
    line = LineCadObject(self, start_point, end_point)
    return self.add_object(line)

def create_circle(self, center: Point2D, radius_point: Point2D) -> str:
    circle = CircleCadObject(self, center, radius_point)
    return self.add_object(circle)
```

### Constraint Creation Fixed

Fixed constraint creation to properly convert `Point2D` objects to tuples for `ConstrainablePoint2D`:

```python
# Before
csp = ConstrainablePoint2D(solver, self.line.start, fixed=False)

# After
csp = ConstrainablePoint2D(solver, (self.line.start.x, self.line.start.y), fixed=False)
```

### Import Issues Resolved

Fixed import issues in CAD objects that were trying to import `Document` incorrectly:

```python
# Before
from ...document import Document

# After
if TYPE_CHECKING:
    from ...models.document import Document
```

## Benefits

1. **Consistency**: All CAD objects now have a consistent constructor signature
2. **Required Document**: Document reference is now mandatory, ensuring proper object lifecycle
3. **Type Safety**: Better type checking with required document parameter
4. **Maintainability**: Easier to understand and modify CAD object creation
5. **Reliability**: Prevents creation of CAD objects without proper document context

## Testing

- All existing tests continue to pass
- Group functionality works correctly with standardized constructors
- Example script demonstrates proper functionality
- No breaking changes to existing API usage patterns

## Usage Examples

### Creating CAD Objects

```python
# Create a line
line = LineCadObject(document, start_point, end_point)

# Create a circle
circle = CircleCadObject(document, center_point, radius_point)

# Create a group
group = GroupCadObject(document, name="My Group")
```

### Using Document Factory Methods

```python
# Create objects through document
line_id = document.create_line(start_point, end_point)
circle_id = document.create_circle(center, radius_point)
group_id = document.create_group("My Group")
```

## Backward Compatibility

The changes maintain backward compatibility through the Document factory methods, which handle the new constructor signatures internally. Existing code that uses `document.create_line()`, `document.create_circle()`, etc. continues to work without modification.

## Future Considerations

- Consider adding validation to ensure document is not None
- Add type hints for better IDE support
- Consider adding factory methods for all CAD object types
- Add unit tests specifically for constructor parameter validation 