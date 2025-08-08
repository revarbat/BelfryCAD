# Construction Items

This document describes the construction graphics items available in BelfryCAD for drawing construction lines, circles, and crosshairs.

## Overview

Construction items are specialized Qt graphics items designed for drawing construction geometry that is:
- **Non-interactive**: Cannot be selected, moved, or modified by user interaction
- **Visually distinct**: Uses gray color (#7f7f7f) to distinguish from regular CAD geometry
- **Configurable**: Supports different dash patterns and styling options
- **High priority**: Renders above other items with high Z-value

## ConstructionLineItem

A `QGraphicsLineItem` subclass for drawing construction lines with optional arrow tips.

### Features

- **Dash Patterns**: Solid, dashed, or centerline patterns
- **Arrow Tips**: Optional arrows at start, end, or both ends
- **Non-interactive**: Ignores all mouse and keyboard events
- **Cosmetic pen**: Maintains consistent width regardless of zoom level

### Usage

```python
from BelfryCAD.gui.views.graphics_items.construction_line_item import (
    ConstructionLineItem, ArrowTip, DashPattern
)
from PySide6.QtCore import QLineF, QPointF

# Create a simple construction line
line = ConstructionLineItem(
    QLineF(QPointF(0, 0), QPointF(100, 0)),
    dash_pattern=DashPattern.SOLID,
    arrow_tips=ArrowTip.END
)

# Add to scene
scene.addItem(line)
```

### Constructor Parameters

- `line`: `QLineF` - The line geometry
- `dash_pattern`: `DashPattern` - Line pattern (default: `DASHED`)
- `arrow_tips`: `ArrowTip` - Arrow configuration (default: `NONE`)
- `parent`: Optional parent graphics item

### Dash Patterns

- `DashPattern.SOLID`: Solid line
- `DashPattern.DASHED`: Dashed line (5px dash, 5px gap)
- `DashPattern.CENTERLINE`: Centerline pattern (10px dash, 2px gap, 2px dash, 2px gap)

### Arrow Tips

- `ArrowTip.NONE`: No arrows
- `ArrowTip.START`: Arrow at start point
- `ArrowTip.END`: Arrow at end point
- `ArrowTip.BOTH`: Arrows at both ends

### Methods

- `setDashPattern(pattern)`: Change the dash pattern
- `setArrowTips(tips)`: Change arrow configuration
- `setLineWidth(width)`: Set line width
- `setConstructionColor(color)`: Set line color

## ConstructionCircleItem

A `QGraphicsEllipseItem` subclass for drawing construction circles.

### Features

- **Dash Patterns**: Solid, dashed, or centerline patterns
- **Outline only**: No fill, transparent brush
- **Non-interactive**: Ignores all mouse and keyboard events
- **Cosmetic pen**: Maintains consistent width regardless of zoom level

### Usage

```python
from BelfryCAD.gui.views.graphics_items.construction_circle_item import (
    ConstructionCircleItem, DashPattern
)
from PySide6.QtCore import QPointF

# Create a construction circle
circle = ConstructionCircleItem(
    center=QPointF(0, 0),
    radius=50,
    dash_pattern=DashPattern.DASHED
)

# Add to scene
scene.addItem(circle)
```

### Constructor Parameters

- `center`: `QPointF` - The center point of the circle
- `radius`: `float` - The radius of the circle
- `dash_pattern`: `DashPattern` - Line pattern (default: `DASHED`)
- `line_width`: `float` - Line width (default: 1.0)
- `parent`: Optional parent graphics item

### Dash Patterns

Same as `ConstructionLineItem`:
- `DashPattern.SOLID`: Solid line
- `DashPattern.DASHED`: Dashed line (3px dash, 3px gap)
- `DashPattern.CENTERLINE`: Centerline pattern (10px dash, 3px gap, 3px dash, 3px gap)

### Methods

- `setDashPattern(pattern)`: Change the dash pattern
- `setLineWidth(width)`: Set line width
- `setConstructionColor(color)`: Set line color

## ConstructionCrossItem

A `QGraphicsItem` subclass for drawing construction crosshairs to mark circle centers.

### Features

- **Dash Patterns**: Solid, dashed, or centerline patterns
- **Crosshair design**: Horizontal and vertical lines intersecting at center
- **Non-interactive**: Ignores all mouse and keyboard events
- **Configurable size**: Adjustable crosshair size

### Usage

```python
from BelfryCAD.gui.views.graphics_items.construction_cross_item import (
    ConstructionCrossItem, DashPattern
)
from PySide6.QtCore import QPointF

# Create a construction crosshair
cross = ConstructionCrossItem(
    center=QPointF(0, 0),
    size=20,
    dash_pattern=DashPattern.CENTERLINE
)

# Add to scene
scene.addItem(cross)
```

### Constructor Parameters

- `center`: `QPointF` - The center point of the crosshair
- `size`: `float` - The size (width/height) of the crosshair (default: 20.0)
- `dash_pattern`: `DashPattern` - Line pattern (default: `CENTERLINE`)
- `line_width`: `float` - Line width (default: 1.0)
- `parent`: Optional parent graphics item

### Dash Patterns

Same as other construction items:
- `DashPattern.SOLID`: Solid line
- `DashPattern.DASHED`: Dashed line (3px dash, 3px gap)
- `DashPattern.CENTERLINE`: Centerline pattern (10px dash, 3px gap, 3px dash, 3px gap)

### Methods

- `setCenter(center)`: Change the center point
- `setSize(size)`: Change the crosshair size
- `setDashPattern(pattern)`: Change the dash pattern
- `setLineWidth(width)`: Set line width
- `setConstructionColor(color)`: Set line color

## Styling

Both construction items use consistent styling:

- **Color**: Gray (#7f7f7f)
- **Line Width**: 1.0 pixels (default)
- **Z-Value**: 1000 (renders above other items)
- **Cosmetic Pen**: True (maintains width during zoom)
- **Transparent Fill**: For circles

## Event Handling

Both items ignore all user interaction events:
- Mouse press, move, release, double-click
- Key press, release
- Focus in, focus out
- Context menu

This ensures they remain purely visual construction aids.

## Examples

See the following example files:
- `examples/construction_line_example.py` - Line item demonstration
- `examples/construction_items_example.py` - Line and circle items together
- `examples/construction_cross_example.py` - Crosshair with circles demonstration
- `tests/simple_arrow_test.py` - Arrow functionality test
- `tests/simple_circle_test.py` - Circle functionality test
- `tests/simple_cross_test.py` - Crosshair functionality test
- `tests/cross_with_circles_test.py` - Crosshairs with circles test 