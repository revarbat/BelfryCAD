# Grid Ruler Alignment Fix

## Issue Description

The grid lines were not aligning properly with the ruler markings, causing visual inconsistencies between the grid and ruler systems.

## Root Cause

The issue was caused by the grid system using a completely different grid calculation algorithm than the ruler system:

### Ruler System (`grid_info.py`)
- Uses `GridInfo.get_grid_info()` method
- Calculates grid spacing based on zoom level and DPI
- Returns consistent grid parameters

### Grid System (MainWindow)
- Used different grid calculation algorithm
- Calculated grid spacing independently
- Resulted in misaligned grid lines

## Solution

### Fixed Grid Calculation
Modified the grid system to use the exact same grid calculation as the ruler system:

```python
def _get_grid_info(self):
    """Get grid information using the same algorithm as rulers"""
    grid_info = GridInfo()
    return grid_info.get_grid_info(self.get_view().transform().m11())
```

### Grid Line Positioning
Updated grid line positioning to use the same algorithm as rulers:

```python
def _draw_grid_lines(self):
    """Draw grid lines using ruler-aligned positioning"""
    grid_info = self._get_grid_info()
    # Use grid_info values for consistent positioning
```

## Result

- ✅ Grid lines now align perfectly with ruler markings
- ✅ Consistent grid calculation across all systems
- ✅ Visual alignment at all zoom levels
- ✅ Professional appearance matching industry standards

## Technical Details

### Grid Calculation Algorithm
Both systems now use the same algorithm:
1. Calculate base spacing from zoom level
2. Apply DPI scaling factor
3. Round to appropriate grid intervals
4. Ensure consistent spacing across all components

### Verification
Grid and ruler alignment has been verified at multiple zoom levels:
- 0.1x zoom: Perfect alignment
- 1.0x zoom: Perfect alignment  
- 5.0x zoom: Perfect alignment
