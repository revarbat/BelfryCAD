# Faithful Translation of OpenSCAD BOSL2 _gear_tooth_profile

## Overview

This document describes the complete and faithful Python translation of the OpenSCAD BOSL2 library's `_gear_tooth_profile()` function. The translation preserves all the sophisticated gear tooth generation features from the original OpenSCAD implementation.

## Key Features Implemented

### 1. Involute Curve Generation
- Exact involute curve calculation using the parametric equations
- Lookup table generation for fast angle-to-radius conversions
- Reverse lookup table for radius-to-angle conversions

### 2. Comprehensive Gear Parameters
- **Circular pitch** (circ_pitch): Distance between teeth centers
- **Module** (mod): Metric gear sizing (pitch diameter / teeth)
- **Diametral pitch** (diam_pitch): Imperial gear sizing (teeth per inch)
- **Pressure angle**: Controls tooth shape (typically 20°)
- **Profile shift**: Allows gear modification for better meshing
- **Backlash**: Gap between meshing teeth
- **Clearance**: Gap between tooth tip and valley
- **Helical angle**: For helical gears
- **Internal gears**: Support for ring gears

### 3. Advanced Calculations

#### Undercut Prevention
The function calculates potential undercuts that would be carved by a meshing rack:
```python
# Calculate the undercut a meshing rack might carve out of this tooth
undercut = []
for a in range(int(math.degrees(math.atan2(ax, rrad))), -91, -1):
    bx = -a/360 * 2*math.pi*prad
    x = bx + ax
    y = prad - circ_pitch/math.pi + profile_shift*circ_pitch/math.pi
    pol = xy_to_polar((x, y))
    if pol[0] < arad*1.05:
        undercut.append((pol[0], pol[1] - a + 180/teeth))
```

#### Clearance Valley Rounding
The function adds proper rounding at the tooth root for clearance:
```python
# Round out the clearance valley
rcircum = 2 * math.pi * (ma_rad if internal else rrad)
rpart = (180/teeth - tang) / 360
round_r = min(maxr, clear, rcircum * rpart)
```

#### Self-Intersection Clipping
Detects and clips self-intersections in the gear profile:
```python
# Look for self-intersections in the gear profile
invalid = []
for i, pt in enumerate(tooth_half):
    angle = math.degrees(math.atan2(pt[1], pt[0]))
    if angle > 90 + 180/teeth:
        invalid.append(i)
```

### 4. Path Optimization
- **Deduplication**: Removes duplicate consecutive points
- **Collinear merging**: Merges points that lie on the same line
- **Resampling**: Optimizes the number of points in the final path

## Function Signature

```python
def _gear_tooth_profile(
    circ_pitch: Optional[float] = None,
    teeth: int = 20,
    pressure_angle: float = 20,
    clearance: Optional[float] = None,
    backlash: float = 0.0,
    helical: float = 0,
    internal: bool = False,
    profile_shift: float = 0.0,
    shorten: float = 0,
    mod: Optional[float] = None,
    diam_pitch: Optional[float] = None,
    pitch: Optional[float] = None,
    center: bool = False,
    gear_steps: int = 16
) -> List[Tuple[float, float]]
```

## Usage Examples

### Standard Spur Gear Tooth
```python
tooth = _gear_tooth_profile(
    teeth=20,
    mod=5.0,
    pressure_angle=20
)
```

### Profile Shifted Gear
```python
tooth = _gear_tooth_profile(
    teeth=20,
    mod=5.0,
    pressure_angle=20,
    profile_shift=0.5  # Positive shift for fewer teeth
)
```

### Internal Gear
```python
tooth = _gear_tooth_profile(
    teeth=60,
    mod=5.0,
    pressure_angle=20,
    internal=True
)
```

### Helical Gear
```python
tooth = _gear_tooth_profile(
    teeth=20,
    mod=5.0,
    pressure_angle=20,
    helical=30  # 30 degree helix angle
)
```

## Verification

The translation has been verified to produce equivalent results to the OpenSCAD implementation:

1. **Involute curve generation** matches the mathematical definition
2. **Undercut calculations** properly prevent weak tooth profiles
3. **Profile shifting** correctly modifies tooth thickness
4. **Internal gears** generate proper tooth spaces
5. **Helical adjustments** properly account for the helix angle

## Differences from Simplified Version

The faithful translation includes many features missing from simplified implementations:

1. **Undercut prevention** - Critical for gears with few teeth
2. **Clearance valley rounding** - Proper root fillet generation
3. **Self-intersection detection** - Prevents invalid geometries
4. **Profile shift support** - Essential for gear optimization
5. **Internal gear support** - For ring gears and planetary systems
6. **Helical gear adjustments** - For non-spur gears
7. **Multiple pitch specifications** - Module, circular pitch, diametral pitch
8. **Path optimization** - Reduces unnecessary points while preserving accuracy

## Testing

The implementation includes comprehensive test scripts:

- `test_gear_tooth_profile.py` - Basic functionality tests
- `compare_gear_profiles.py` - Detailed verification of features
- `debug_tooth_profile.py` - Visualization tools (requires matplotlib)

These tests verify that the Python implementation faithfully reproduces the behavior of the OpenSCAD BOSL2 original. 