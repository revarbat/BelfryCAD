# ConstructionLineItem

A specialized `QGraphicsLineItem` for drawing construction lines with configurable dash patterns and optional arrow tips.

## Overview

The `ConstructionLineItem` class provides a dedicated graphics item for drawing construction lines in CAD applications. It inherits from `QGraphicsLineItem` and adds specialized styling for construction geometry.

## Features

- **Construction Color**: Uses `#7f7f7f` (gray) color by default
- **Cosmetic Pen**: Lines scale with zoom level
- **Configurable Dash Patterns**: Solid, dashed, or centerline patterns
- **Optional Arrow Tips**: Arrow tips at start, end, or both ends
- **High Z-Value**: Appears above other graphics items
- **Hit Testing**: Proper shape detection including arrow tips
- **Non-Interactive**: Unselectable, unmovable, and undraggable

## Usage

### Basic Usage

```python
from PySide6.QtCore import QPointF, QLineF
from src.BelfryCAD.gui.views.graphics_items.construction_line_item import (
    ConstructionLineItem, DashPattern, ArrowTip
)

# Create a simple construction line
start_point = QPointF(0, 0)
end_point = QPointF(100, 100)
line = QLineF(start_point, end_point)

# Default dashed construction line
item = ConstructionLineItem(line)
scene.addItem(item)
```

### Creating Different Types

```python
from src.BelfryCAD.gui.views.graphics_items.construction_line_item import (
    ConstructionLineItem, DashPattern, ArrowTip
)

# Create different types of construction lines
solid_line = ConstructionLineItem(QLineF(QPointF(0, 0), QPointF(100, 100)), DashPattern.SOLID)
dashed_line = ConstructionLineItem(QLineF(QPointF(0, 20), QPointF(100, 120)), DashPattern.DASHED)
centerline = ConstructionLineItem(QLineF(QPointF(0, 40), QPointF(100, 140)), DashPattern.CENTERLINE)

# Create with arrow tips
arrow_line = ConstructionLineItem(
    QLineF(QPointF(0, 60), QPointF(100, 160)),
    DashPattern.DASHED, ArrowTip.BOTH
)
```

## Dash Patterns

### DashPattern Enum

- **SOLID**: Solid line with no dashes
- **DASHED**: Standard dashed line (5.0, 5.0 pattern)
- **CENTERLINE**: Centerline pattern (10.0, 2.0, 2.0, 2.0)

```python
# Create with specific dash pattern
item = ConstructionLineItem(line, DashPattern.SOLID)
item.setDashPattern(DashPattern.CENTERLINE)
```

## Arrow Tips

### ArrowTip Enum

- **NONE**: No arrow tips
- **START**: Arrow tip at the start point
- **END**: Arrow tip at the end point
- **BOTH**: Arrow tips at both ends

```python
# Create with arrow tips
item = ConstructionLineItem(line, DashPattern.DASHED, ArrowTip.END)
item.setArrowTips(ArrowTip.BOTH)
```

## Styling

### Color and Width

```python
# Set custom color
item.setConstructionColor(QColor(255, 0, 0))  # Red

# Set custom line width
item.setLineWidth(2.0)
```

### Default Properties

- **Color**: `#7f7f7f` (gray)
- **Line Width**: 1.0
- **Cosmetic**: True (scales with zoom)
- **Z-Value**: 1000 (appears above other items)

## Example: Complete Construction Line Setup

```python
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import QPointF, QLineF
from src.BelfryCAD.gui.views.graphics_items.construction_line_item import (
    ConstructionLineItem, DashPattern, ArrowTip
)

# Create scene
scene = QGraphicsScene()

# Create various construction lines
lines = [
    # Solid line
    ConstructionLineItem(QLineF(QPointF(0, 0), QPointF(100, 0)), DashPattern.SOLID),
    
    # Dashed line with start arrow
    ConstructionLineItem(
        QLineF(QPointF(0, 20), QPointF(100, 20)),
        DashPattern.DASHED, ArrowTip.START
    ),
    
    # Centerline with end arrow
    ConstructionLineItem(
        QLineF(QPointF(0, 40), QPointF(100, 40)),
        DashPattern.CENTERLINE, ArrowTip.END
    ),
    
    # Solid line with both arrows
    ConstructionLineItem(
        QLineF(QPointF(0, 60), QPointF(100, 60)),
        DashPattern.SOLID, ArrowTip.BOTH
    )
]

# Add to scene
for line in lines:
    scene.addItem(line)
```

## Integration with Existing Code

### Replacing draw_construction_line()

Instead of using the `draw_construction_line()` method in `CadItem`, you can now use `ConstructionLineItem`:

```python
# Old way (in paint method)
def paint_item(self, painter, option, widget=None):
    self.draw_construction_line(painter, point1, point2)

# New way (create items)
def create_construction_lines(self):
    line_item = create_dashed_construction_line(point1, point2)
    self.scene().addItem(line_item)
```

### In GearView

```python
class GearView(CadItem):
    def __init__(self, main_window, viewmodel):
        super().__init__(main_window, viewmodel)
        
        # Create construction lines
        self._construction_lines = []
        
    def _add_construction_line(self, start: QPointF, end: QPointF):
        """Add a construction line to the gear view"""
        line_item = ConstructionLineItem(QLineF(start, end), DashPattern.DASHED)
        line_item.setParentItem(self)
        self._construction_lines.append(line_item)
```

## Benefits

1. **Reusable**: Can be used across different CAD objects
2. **Configurable**: Easy to change dash patterns and arrow tips
3. **Performance**: Efficient rendering with Qt's graphics system
4. **Consistent**: Standardized construction line appearance
5. **Interactive**: Proper hit testing and selection
6. **Non-Interactive**: Cannot be selected, moved, or dragged - purely visual aids

## Non-Interactive Behavior

Construction lines are designed to be purely visual aids and are completely non-interactive:

- **Unselectable**: Cannot be selected with mouse clicks
- **Unmovable**: Cannot be moved or dragged
- **Unfocusable**: Cannot receive keyboard focus
- **Event Ignoring**: All mouse and keyboard events are ignored

This ensures that construction lines don't interfere with the selection and manipulation of actual CAD objects while still providing visual guidance.

```python
# Construction lines are automatically non-interactive
item = ConstructionLineItem(line)
assert not item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
assert not item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
assert not item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
```

## Testing

Run the test suite to verify functionality:

```bash
python tests/test_construction_line_item.py
```

## Example Demo

Run the demonstration to see all construction line types:

```bash
python examples/construction_line_example.py
```

This will open a window showing various construction line styles and configurations. 