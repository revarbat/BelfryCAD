# Grid Display Issue Resolution

## Issue Description

The grid system was experiencing display issues due to incompatible removal systems between the old and new grid implementations.

## Root Causes

1. **Z-value conflicts**: The old grid system used Z-value -1001 for grid items
2. **Incompatible removal systems**: The old grid system created items that were not tagged using the current tagging system, so the new grid's `remove_items_by_tag()` calls couldn't remove them.

## Solution

Modified the grid redraw system to remove both tagged and legacy items:

```python
def redraw_grid(self):
    # Remove both tagged and legacy grid items
    self.remove_items_by_tag("Grid")
    self.remove_items_by_tag("GridLine") 
    self.remove_items_by_tag("GridUnitLine")
    
    # Also remove legacy items by Z-value
    for item in self.scene.items():
        if hasattr(item, 'zValue') and item.zValue() == -1001:
            self.scene.removeItem(item)
```

## Result

- ✅ Grid items are properly removed before redrawing
- ✅ No visual artifacts from old grid items
- ✅ Clean grid display at all zoom levels
