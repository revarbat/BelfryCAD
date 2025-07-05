# Snaps System for BelfryCAD

## Overview

The Snaps System provides comprehensive snapping functionality for CAD tools in BelfryCAD. It allows tools to snap to various geometric features including grid points, control points, midpoints, quadrants, and tangent points.

## Features

### Supported Snap Types

1. **Grid Snapping** - Snaps to the nearest grid point based on current grid spacing
2. **Control Points** - Snaps to control points of CAD items (endpoints, handles, centers, etc.)
3. **Midpoints** - Snaps to the midpoints of line segments
4. **Quadrants** - Snaps to the quadrant points of circles (top, right, bottom, left)
5. **Tangents** - Snaps to tangent points on circles from a reference point
6. **Perpendicular** - Snaps to perpendicular points from a reference line
7. **Intersections** - Snaps to intersection points (simplified implementation)
8. **Nearest** - Snaps to the nearest point on any CAD item

### Key Components

#### SnapsSystem Class
The main class that handles all snapping logic:

```python
from BelfryCAD.gui.snaps_system import SnapsSystem

# Create a snaps system
snaps_system = SnapsSystem(scene, grid_info)

# Get a snapped point
snapped_point = snaps_system.get_snap_point(mouse_pos, recent_points)
```

#### SnapPoint Class
Represents a snap point with metadata:

```python
@dataclass
class SnapPoint:
    point: QPointF              # The actual snap point
    snap_type: SnapType         # Type of snap (grid, controlpoints, etc.)
    distance: float             # Distance from mouse to snap point
    source_item: Optional[CadItem] = None  # Source CAD item
    metadata: Dict[str, Any] = None  # Additional metadata
```

## Integration with Tools

### Base Tool Integration
The base `Tool` class has been updated to use the snaps system:

```python
def get_snap_point(self, x: float, y: float) -> Point:
    """Get the snapped point based on snap settings"""
    if hasattr(self.main_window, 'snaps_system'):
        mouse_pos = QPointF(x, y)
        recent_points = [QPointF(p.x, p.y) for p in self.points]
        snapped_point = self.main_window.snaps_system.get_snap_point(mouse_pos, recent_points)
        if snapped_point:
            return Point(snapped_point.x(), snapped_point.y())
    
    return Point(x, y)
```

### Main Window Integration
The main window initializes the snaps system:

```python
# In MainWindow.__init__()
self.snaps_system = None

# In _create_canvas()
self.snaps_system = SnapsSystem(self.cad_scene, self.grid_info)
```

## Usage Examples

### Basic Grid Snapping
```python
# Grid snapping is enabled by default
mouse_pos = QPointF(0.1, 0.1)
snapped = snaps_system.get_snap_point(mouse_pos)
# Result: snapped to (0, 0) if within tolerance
```

### Control Point Snapping
```python
# Enable control point snapping
snaps_pane_info.snap_states['controlpoints'] = True
snaps_pane_info.snap_all = False

mouse_pos = QPointF(-5.1, -5.1)  # Near a line endpoint
snapped = snaps_system.get_snap_point(mouse_pos)
# Result: snapped to the line endpoint if within tolerance
```

### Tangent Snapping
```python
# Enable tangent snapping
snaps_pane_info.snap_states['tangents'] = True

# Use recent construction points for tangent calculations
ref_point = QPointF(5, 0)  # Reference point outside circle
mouse_pos = QPointF(2.1, 1.5)  # Near tangent point
recent_points = [ref_point]

snapped = snaps_system.get_snap_point(mouse_pos, recent_points)
# Result: snapped to tangent point on circle
```

### Quadrant Snapping
```python
# Enable quadrant snapping
snaps_pane_info.snap_states['quadrants'] = True

mouse_pos = QPointF(0.1, 2.1)  # Near top of circle
snapped = snaps_system.get_snap_point(mouse_pos)
# Result: snapped to top quadrant point
```

## Configuration

### Snap Settings
Snap settings are managed through the existing snaps pane:

```python
from BelfryCAD.gui.panes.snaps_pane import snaps_pane_info

# Enable all snaps
snaps_pane_info.snap_all = True

# Enable specific snap types
snaps_pane_info.snap_states['grid'] = True
snaps_pane_info.snap_states['controlpoints'] = True
snaps_pane_info.snap_states['quadrants'] = True
snaps_pane_info.snap_states['tangents'] = True
```

### Snap Tolerance
The snap tolerance can be adjusted:

```python
snaps_system.set_snap_tolerance(15.0)  # 15 pixels
```

## Testing

Run the test script to see the snaps system in action:

```bash
python test_snaps_system.py
```

This will create a test scene with various CAD items and demonstrate different snap types.

## Implementation Details

### Grid Snapping
- Uses the current grid spacing from `GridInfo`
- Calculates the nearest grid point by rounding to grid spacing
- Automatically adjusts based on current view scaling

### Control Point Snapping
- Accesses control points through the scene's control point management
- Handles different types of control points (endpoints, centers, handles)
- Converts local coordinates to scene coordinates

### Tangent Snapping
- Calculates tangent points using geometric construction
- Requires a reference point outside the circle
- Returns two tangent points (user can choose the appropriate one)

### Performance Considerations
- Uses caching for expensive calculations
- Only processes visible CAD items
- Efficient distance calculations using squared distances

## Future Enhancements

1. **Intersection Snapping** - Full implementation of line-line intersections
2. **Parallel Snapping** - Snap to parallel lines
3. **Extension Snapping** - Snap to extended lines
4. **Visual Feedback** - Show snap indicators in the UI
5. **Snap Priority** - Prioritize certain snap types over others
6. **Custom Snap Points** - Allow CAD items to define custom snap points

## Troubleshooting

### Common Issues

1. **No snapping occurs** - Check if snap types are enabled in the snaps pane
2. **Grid snapping not working** - Verify grid spacing and view scaling
3. **Control points not found** - Ensure CAD items have control points created
4. **Tangent snapping requires reference point** - Pass recent construction points

### Debug Mode
Enable debug output by setting the snap tolerance to a large value and checking console output for snap calculations. 