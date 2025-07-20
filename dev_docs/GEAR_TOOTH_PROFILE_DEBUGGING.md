# Gear Tooth Profile Debugging Guide

## Overview

The `_gear_tooth_profile()` function has been extracted from the main `create_gear()` function to allow independent debugging and testing. This function generates the profile for a single gear tooth using involute curve mathematics.

## Function Signature

```python
def _gear_tooth_profile(
    num_teeth: int,
    pitch_radius: float,
    base_radius: float,
    outer_radius: float,
    root_radius: float,
    clearance: float,
    points_per_involute: int = 30
) -> List[Tuple[float, float]]:
```

## Parameters

- **num_teeth**: Number of teeth on the gear (affects tooth thickness)
- **pitch_radius**: Pitch circle radius (where teeth mesh)
- **base_radius**: Base circle radius (for involute curve generation)
- **outer_radius**: Outer circle radius (tooth tip)
- **root_radius**: Root circle radius (tooth valley)
- **clearance**: Gap between tooth tip and valley
- **points_per_involute**: Number of points to sample the involute curve

## Debugging Tools

### 1. Basic Test Script

Run `test_gear_tooth_profile.py` to test the function with various parameters:

```bash
python test_gear_tooth_profile.py
```

This script:
- Tests the function with different parameter combinations
- Shows point counts and bounding boxes
- Validates symmetry between left and right halves
- Provides detailed output for debugging

### 2. Visualization Script

Run `debug_tooth_profile.py` to visualize the tooth profile:

```bash
python debug_tooth_profile.py
```

This script requires matplotlib and provides:
- 2D plots of the tooth profile
- Reference circles (pitch, base, outer, root)
- Left vs right half comparison
- Point distribution analysis
- Parameter comparison across different gear sizes

### 3. Interactive Debugging

You can also debug interactively in Python:

```python
from BelfryCAD.foo3 import _gear_tooth_profile

# Test with specific parameters
tooth_points = _gear_tooth_profile(
    num_teeth=16,
    pitch_radius=32.0,
    base_radius=30.0,
    outer_radius=36.0,
    root_radius=28.0,
    clearance=1.0,
    points_per_involute=20
)

# Inspect the results
print(f"Generated {len(tooth_points)} points")
for i, (x, y) in enumerate(tooth_points[:5]):
    print(f"Point {i}: ({x:.3f}, {y:.3f})")
```

## Key Debugging Points

### 1. Involute Lookup Table Generation

The function generates a lookup table for the involute curve:

```python
# Generate involute lookup table
involute_lup = []
for i in range(0, int(outer_radius / math.pi / base_radius * 360), 5):
    x, y = involute_point(base_radius, i)
    r, theta = xy_to_polar(x, y)
    if r <= outer_radius * 1.1:
        involute_lup.append((r, 90 - theta))
```

Debug by checking:
- Table size: `len(involute_lup)`
- Radius range: `min(r for r, _ in involute_lup)` to `max(r for r, _ in involute_lup)`
- Angle range: `min(a for _, a in involute_lup)` to `max(a for _, a in involute_lup)`

### 2. Key Angle Calculations

The function calculates several key angles:

```python
a_ang = lookup(outer_radius, involute_lup)  # Outer angle
p_ang = lookup(pitch_radius, involute_lup)  # Pitch angle
b_ang = lookup(base_radius, involute_lup)   # Base angle
r_ang = lookup(root_radius, involute_lup)   # Root angle
```

Debug by printing these values to ensure they're reasonable.

### 3. Tooth Profile Generation

The main profile generation loop:

```python
# Generate left half of tooth
tooth_half = []
for j in range(steps + 1):
    u = j / steps
    r = root_radius + u * (outer_radius - root_radius)
    
    if r > root_radius + clearance and r < outer_radius - clearance:
        angle = lookup(r, involute_lup) + soff
        if angle < 90 + 180/num_teeth:
            x, y = polar_to_xy(r, angle)
            tooth_half.append((x, y))
```

Debug by checking:
- Number of points generated: `len(tooth_half)`
- Radius range covered
- Angle constraints

### 4. Symmetry Validation

The tooth should be symmetric about the Y-axis. Check:

```python
left_points = [(x, y) for x, y in tooth_points if x <= 0]
right_points = [(x, y) for x, y in tooth_points if x >= 0]
print(f"Left: {len(left_points)}, Right: {len(right_points)}")
```

## Common Issues and Solutions

### 1. Too Few Points Generated

**Symptoms**: Tooth profile has gaps or looks jagged
**Solutions**:
- Increase `points_per_involute`
- Check clearance constraints
- Verify radius range calculations

### 2. Asymmetric Tooth Profile

**Symptoms**: Left and right halves don't match
**Solutions**:
- Check the mirroring logic
- Verify angle calculations
- Ensure consistent coordinate transformations

### 3. Tooth Too Large or Small

**Symptoms**: Tooth doesn't fit properly in gear
**Solutions**:
- Check `num_teeth` parameter (affects tooth thickness)
- Verify radius calculations
- Adjust clearance values

### 4. Involute Curve Issues

**Symptoms**: Tooth profile doesn't follow proper involute shape
**Solutions**:
- Check base_radius calculation
- Verify involute_point() function
- Ensure lookup table covers required range

## Integration with Main Gear Function

The `create_gear()` function now uses `_gear_tooth_profile()`:

```python
# Get single tooth profile
tooth_profile = _gear_tooth_profile(
    num_teeth=num_teeth,
    pitch_radius=pitch_radius,
    base_radius=base_radius,
    outer_radius=outer_radius,
    root_radius=root_radius,
    clearance=clearance,
    points_per_involute=points_per_involute
)

# Rotate and duplicate for complete gear
for i in range(num_teeth):
    tooth_rotation = 2 * math.pi * i / num_teeth
    # ... rotation logic
```

## Performance Considerations

- **points_per_involute**: Higher values give smoother curves but slower generation
- **Lookup table step size**: Currently 5 degrees, can be adjusted for precision vs speed
- **Memory usage**: Each tooth profile is stored separately before rotation

## Future Enhancements

1. **Caching**: Cache lookup tables for repeated calls with same parameters
2. **Optimization**: Use numpy for vectorized calculations
3. **Validation**: Add parameter validation and bounds checking
4. **Profiling**: Add performance metrics for optimization 