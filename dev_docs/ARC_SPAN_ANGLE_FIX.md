# Arc Span Angle Calculation Fix

## Problem Description
The ArcCadObject was incorrectly treating the span_angle as an ending angle rather than the actual angular span from the start angle. This caused confusion in XML serialization where the span_angle value was actually the end_angle.

## Root Cause
In `src/BelfryCAD/models/cad_objects/arc_cad_object.py`, the `_update_arc()` method was incorrectly passing `end_angle` as the fourth parameter to the Arc constructor:

```python
# INCORRECT (before fix):
def _update_arc(self):
    radius = self._center_point.distance_to(self._start_point)
    start_angle = (self._start_point - self._center_point).angle_radians
    end_angle = (self._end_point - self._center_point).angle_radians
    self.arc = Arc(self._center_point, radius, start_angle, end_angle)  # ❌ Wrong!
```

However, the Arc geometry class constructor expects `span_angle` as the fourth parameter:
```python
# Arc constructor signature:
def __init__(self, center: Point2D, radius: float, start_angle: float, span_angle: float)
```

This mismatch caused the Arc object to store the `end_angle` value as its `span_angle`, which then propagated through to the XML serialization.

## Solution
Fixed the `_update_arc()` method to correctly calculate the span angle and handle wraparound cases:

```python
# CORRECT (after fix):
def _update_arc(self):
    radius = self._center_point.distance_to(self._start_point)
    start_angle = (self._start_point - self._center_point).angle_radians
    end_angle = (self._end_point - self._center_point).angle_radians
    
    # Calculate span angle (handling wraparound)
    span_angle = end_angle - start_angle
    
    # Normalize span angle to handle wraparound cases
    # If the span would be negative or very large, assume the shorter arc is intended
    if span_angle > math.pi:
        span_angle -= 2 * math.pi
    elif span_angle < -math.pi:
        span_angle += 2 * math.pi
        
    self.arc = Arc(self._center_point, radius, start_angle, span_angle)  # ✅ Correct!
```

## Changes Made

### File: `src/BelfryCAD/models/cad_objects/arc_cad_object.py`

1. **Added import**: `import math` for angle calculations
2. **Fixed `_update_arc()` method**:
   - Calculate actual span angle: `span_angle = end_angle - start_angle`
   - Handle wraparound with normalization logic
   - Pass correct `span_angle` to Arc constructor

### Angle Normalization Logic
The fix includes intelligent angle normalization to handle cases where arcs cross the 0°/360° boundary:

- **If span > 180°**: Assumes the shorter arc was intended, subtracts 360°
- **If span < -180°**: Assumes the shorter arc was intended, adds 360°
- **Otherwise**: Uses the calculated span as-is

This ensures that arcs spanning across the 0° boundary (e.g., 330° to 30°) are correctly interpreted as 60° spans rather than 300° spans.

## Impact on XML Serialization

### Before Fix
```xml
<!-- span_angle was actually the end_angle -->
<belfry:arc id="1" name="arc1" color="black" line_width="0.5" visible="true" locked="false">
  <belfry:center_point x="500.0" y="300.0" />
  <belfry:radius value="250.0" />
  <belfry:start_angle value="45.0" />
  <belfry:span_angle value="165.0" />  <!-- ❌ This was end_angle, not span! -->
</belfry:arc>
```

### After Fix
```xml
<!-- span_angle is now the actual angular span -->
<belfry:arc id="1" name="arc1" color="black" line_width="0.5" visible="true" locked="false">
  <belfry:center_point x="500.0" y="300.0" />
  <belfry:radius value="250.0" />
  <belfry:start_angle value="45.0" />
  <belfry:span_angle value="120.0" />  <!-- ✅ Correct span_angle! -->
</belfry:arc>
```

## Testing Results

### Test Cases Verified

1. **Quarter Circle (90°)**:
   - Start: 0°, End: 90°, Expected Span: 90°
   - ✅ Result: Span = 90°

2. **Half Circle (180°)**:
   - Start: 0°, End: 180°, Expected Span: 180°
   - ✅ Result: Span = 180°

3. **120° Arc**:
   - Start: 45°, End: 165°, Expected Span: 120°
   - ✅ Result: Span = 120°

4. **Wraparound Arc**:
   - Start: 330°, End: 30°, Expected Span: 60° (short arc)
   - ✅ Result: Span = 60°

5. **XML Round-trip**:
   - Original span preserved through save/load cycle
   - ✅ All test cases maintain correct span_angle values

## Benefits

### Accuracy
- Arc span_angle now represents the actual angular span
- XML serialization correctly reflects geometric intent
- Wraparound cases handled intelligently

### Consistency
- Arc geometry and ArcCadObject now consistent
- XML format matches the actual geometric parameters
- Eliminates confusion between span_angle and end_angle

### Reliability
- Round-trip serialization preserves correct values
- Predictable behavior for all angle combinations
- Proper handling of edge cases (wraparound, negative spans)

## Backward Compatibility

### No Breaking Changes
- ArcCadObject constructor signature unchanged
- External API remains the same
- Existing code continues to work

### XML Compatibility
- New XML files will have correct span_angle values
- Loading behavior improved (more accurate reconstruction)
- The fix is purely corrective, not format-changing

## Technical Details

### Angle Calculation
```python
span_angle = end_angle - start_angle

# Handle wraparound cases
if span_angle > math.pi:        # > 180°
    span_angle -= 2 * math.pi   # Choose shorter arc
elif span_angle < -math.pi:     # < -180°
    span_angle += 2 * math.pi   # Choose shorter arc
```

### Arc Constructor Call
```python
# Now correctly passes span_angle (not end_angle)
self.arc = Arc(self._center_point, radius, start_angle, span_angle)
```

### Property Consistency
The `span_angle` property now returns the true span:
```python
@property
def span_angle(self) -> float:
    return self.arc.span_angle  # Now correctly reflects actual span
```

## Conclusion

This fix resolves a fundamental issue in arc geometry calculation that was causing incorrect XML serialization. The span_angle now correctly represents the angular span from start_angle, making the XML format accurate and intuitive. The fix includes proper wraparound handling and maintains full backward compatibility while significantly improving the accuracy of arc representation in BelfryCAD documents. 