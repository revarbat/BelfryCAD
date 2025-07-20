# Bezier Path Conversion Functions

This document describes the Bezier path conversion functions that allow you to convert a list of (x,y) tuples into a smooth Bezier curve that preserves sharp corners.

## Overview

The functions in `src/BelfryCAD/utils/bezutils.py` provide tools to convert polyline paths into smooth Bezier curves while preserving important geometric features like sharp corners. This is particularly useful for:

- Converting imported geometry to editable Bezier curves
- Smoothing rough paths while preserving key features
- Creating Bezier approximations of complex shapes
- Integrating with the BelfryCAD drawing system

## Key Functions

### `path_to_bezier()`

Converts a list of (x,y) tuples into a `BezierPath` object with corner preservation.

```python
from BelfryCAD.utils.bezutils import path_to_bezier

points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (2.0, 1.0)]
bezier_path = path_to_bezier(points, corner_threshold=30.0, smoothness=0.3)
```

**Parameters:**
- `points`: List of (x,y) tuples representing the path
- `corner_threshold`: Angle in degrees below which a corner is considered sharp (default: 30.0)
- `smoothness`: Factor controlling curve smoothness (0.0 = sharp, 1.0 = very smooth, default: 0.3)

**Returns:** `BezierPath` object

### `path_to_bezier_with_tension()`

Alternative conversion using tension-based control points.

```python
from BelfryCAD.utils.bezutils import path_to_bezier_with_tension

bezier_path = path_to_bezier_with_tension(points, tension=0.5, corner_threshold=30.0)
```

**Parameters:**
- `points`: List of (x,y) tuples representing the path
- `tension`: Tension factor (0.0 = loose, 1.0 = tight, default: 0.5)
- `corner_threshold`: Angle in degrees below which a corner is considered sharp (default: 30.0)

**Returns:** `BezierPath` object

### `simplify_path_for_bezier()`

Removes redundant points from a path before conversion.

```python
from BelfryCAD.utils.bezutils import simplify_path_for_bezier

simplified = simplify_path_for_bezier(points, tolerance=0.1)
```

**Parameters:**
- `points`: List of (x,y) tuples representing the path
- `tolerance`: Distance tolerance for point removal (default: 0.1)

**Returns:** Simplified list of (x,y) tuples

### `points_to_qpainter_path()`

Direct conversion to QPainterPath for use with Qt graphics.

```python
from BelfryCAD.utils.bezutils import points_to_qpainter_path

qpath = points_to_qpainter_path(points, corner_threshold=30.0, smoothness=0.3)
```

**Parameters:**
- `points`: List of (x,y) tuples representing the path
- `corner_threshold`: Angle in degrees below which a corner is considered sharp (default: 30.0)
- `smoothness`: Factor controlling curve smoothness (default: 0.3)

**Returns:** `QPainterPath` object ready for drawing

### `bezier_path_to_qpainter_path()`

Converts a `BezierPath` to a `QPainterPath`.

```python
from BelfryCAD.utils.bezutils import bezier_path_to_qpainter_path

qpath = bezier_path_to_qpainter_path(bezier_path)
```

**Parameters:**
- `bezier_path`: The `BezierPath` to convert

**Returns:** `QPainterPath` object

### `simplify_bezier_path()`

Simplifies a Bezier path by reducing the number of control points while preserving features.

```python
from BelfryCAD.utils.bezutils import simplify_bezier_path

simplified = simplify_bezier_path(original_bezier, tolerance=0.1, corner_threshold=30.0)
```

**Parameters:**
- `bezier_path`: The `BezierPath` to simplify
- `tolerance`: Distance tolerance for point removal (default: 0.1)
- `corner_threshold`: Angle in degrees below which a corner is considered sharp (default: 30.0)
- `max_segments`: Maximum number of segments to allow (default: None, no limit)

**Returns:** Simplified `BezierPath` object

### `simplify_bezier_path_adaptive()`

Simplifies a Bezier path adaptively to achieve a target number of segments.

```python
from BelfryCAD.utils.bezutils import simplify_bezier_path_adaptive

simplified = simplify_bezier_path_adaptive(original_bezier, target_segments=10, corner_threshold=30.0)
```

**Parameters:**
- `bezier_path`: The `BezierPath` to simplify
- `target_segments`: Target number of segments (default: 10)
- `corner_threshold`: Angle in degrees below which a corner is considered sharp (default: 30.0)

**Returns:** Simplified `BezierPath` object with approximately target_segments segments

### `bezier_path_quality_metrics()`

Calculates quality metrics for comparing original and simplified Bezier paths.

```python
from BelfryCAD.utils.bezutils import bezier_path_quality_metrics

metrics = bezier_path_quality_metrics(original_bezier, simplified_bezier)
```

**Parameters:**
- `original`: The original `BezierPath`
- `simplified`: The simplified `BezierPath`

**Returns:** Dictionary containing quality metrics including segment reduction, length error, and closure preservation

## Usage Examples

### Basic Conversion

```python
# Simple path with sharp corners
points = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (2.0, 1.0)]

# Convert to Bezier with corner preservation
bezier_path = path_to_bezier(points, corner_threshold=30.0, smoothness=0.3)

# Convert to QPainterPath for drawing
qpath = points_to_qpainter_path(points, corner_threshold=30.0, smoothness=0.3)
```

### Path Simplification

```python
# Dense path with redundant points
dense_points = [(0.0, 0.0), (0.1, 0.01), (0.2, 0.02), ..., (1.0, 0.0)]

# Simplify first
simplified = simplify_path_for_bezier(dense_points, tolerance=0.1)

# Then convert to Bezier
bezier_path = path_to_bezier(simplified, corner_threshold=30.0, smoothness=0.3)
```

### Different Smoothness Levels

```python
# Same path with different smoothness
points = [(0.0, 0.0), (1.0, 0.5), (2.0, 0.0)]

# Sharp curves
bezier_sharp = path_to_bezier(points, smoothness=0.1)

# Smooth curves
bezier_smooth = path_to_bezier(points, smoothness=0.8)
```

### Tension Control

```python
# Using tension-based control
points = [(0.0, 0.0), (1.0, 0.5), (2.0, 0.0)]

# Loose curves
bezier_loose = path_to_bezier_with_tension(points, tension=0.2)

# Tight curves
bezier_tight = path_to_bezier_with_tension(points, tension=0.8)
```

### Bezier Path Simplification

```python
# Create a complex Bezier path
original_bezier = path_to_bezier(complex_points, corner_threshold=30.0, smoothness=0.3)

# Standard simplification
simplified = simplify_bezier_path(original_bezier, tolerance=0.1, corner_threshold=30.0)

# Adaptive simplification to target segments
adaptive_simplified = simplify_bezier_path_adaptive(original_bezier, target_segments=5, corner_threshold=30.0)

# Aggressive simplification with segment limit
aggressive_simplified = simplify_bezier_path(original_bezier, tolerance=0.3, max_segments=3)

# Compare quality
metrics = bezier_path_quality_metrics(original_bezier, simplified)
print(f"Segment reduction: {metrics['segment_reduction']:.1f}%")
print(f"Length error: {metrics['length_error_percent']:.2f}%")
```

### Closed Path Simplification

```python
# Simplify a closed path (like a gear)
original_bezier = path_to_bezier(gear_points, corner_threshold=15.0, smoothness=0.2)

# Simplify while preserving closure
simplified = simplify_bezier_path(original_bezier, tolerance=0.1, corner_threshold=15.0)

# Verify closure is preserved
metrics = bezier_path_quality_metrics(original_bezier, simplified)
print(f"Closure preserved: {metrics['closure_preserved']}")
```

## Integration with BelfryCAD

### In a CAD Item

```python
from BelfryCAD.utils.bezutils import points_to_qpainter_path

class MyCadItem(CadItem):
    def __init__(self, points):
        super().__init__()
        self._points = points
        self._path = points_to_qpainter_path(points, corner_threshold=30.0, smoothness=0.3)
    
    def paint_item(self, painter, option, widget=None):
        painter.drawPath(self._path)
```

### Converting Imported Geometry

```python
# Imported points from external source
imported_points = [(x1, y1), (x2, y2), ...]

# Convert to Bezier for editing
bezier_path = path_to_bezier(imported_points, corner_threshold=30.0, smoothness=0.3)

# Create CAD item
cad_item = CubicBezierCadItem.from_bezier_path(bezier_path)
```

## Parameter Guidelines

### Corner Threshold

- **15°**: Very sensitive to corners, preserves most sharp features
- **30°**: Balanced approach, good for most applications
- **45°**: Less sensitive, creates smoother curves
- **60°**: Very smooth, may lose some sharp features

### Smoothness

- **0.1**: Very sharp curves, close to original path
- **0.3**: Balanced smoothness (recommended default)
- **0.5**: Smooth curves
- **0.8**: Very smooth curves
- **1.0**: Maximum smoothness

### Tension

- **0.2**: Loose curves, control points far from path
- **0.5**: Balanced tension (recommended default)
- **0.8**: Tight curves, control points close to path

## Performance Considerations

- **Path simplification** can significantly reduce the number of Bezier segments
- **Corner threshold** affects the number of segments created
- **Large paths** (>1000 points) should be simplified first
- **Real-time conversion** works well for paths with <100 points

## Best Practices

1. **Simplify first**: Use `simplify_path_for_bezier()` on dense paths
2. **Test parameters**: Try different corner thresholds and smoothness values
3. **Preserve features**: Use lower corner thresholds for important sharp features
4. **Consider editing**: If the result will be edited, use moderate smoothness
5. **Performance**: For real-time applications, keep paths under 100 points

## Troubleshooting

### Curves too smooth
- Decrease `smoothness` parameter
- Decrease `corner_threshold`
- Use `path_to_bezier_with_tension()` with higher tension

### Curves too sharp
- Increase `smoothness` parameter
- Increase `corner_threshold`
- Use `path_to_bezier_with_tension()` with lower tension

### Too many segments
- Simplify the path first
- Increase `corner_threshold`
- Use higher `smoothness`

### Performance issues
- Simplify dense paths
- Reduce number of input points
- Use lower corner thresholds for large paths 