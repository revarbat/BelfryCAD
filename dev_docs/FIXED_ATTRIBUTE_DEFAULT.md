# Fixed Attribute Default Change

## Overview

Changed the XML format to make `fixed="false"` the default assumption for object properties, eliminating the need to explicitly specify `fixed="false"` in most cases.

## Rationale

- **Cleaner XML**: Reduces verbosity by not requiring explicit `fixed="false"` attributes
- **Common Case Optimization**: Most properties are free (not fixed) by default, so this reduces the most common case
- **Consistency**: Follows the principle that defaults should be the most common case
- **Readability**: Makes XML files more concise and easier to read

## Changes Made

### 1. **`src/BelfryCAD/utils/xml_serializer.py`**
- Removed explicit `fixed="false"` attributes from serialization methods:
  - `_add_circle_data()` - Removed from radius element
  - `_add_gear_data()` - Removed from pitch_radius, num_teeth, and pressure_angle elements

### 2. **`dev_docs/XML_FILE_FORMAT_SPECIFICATION.md`**
- Updated all XML examples to remove `fixed="false"` attributes
- Added documentation section explaining the default behavior
- Updated complete example to show cleaner XML format

## Before and After Examples

### Before (Verbose)
```xml
<belfry:circle id="circle1" name="My Circle">
    <belfry:center_point x="5.0" y="5.0" />
    <belfry:radius value="3.0" fixed="false" />
</belfry:circle>
```

### After (Clean)
```xml
<belfry:circle id="circle1" name="My Circle">
    <belfry:center_point x="5.0" y="5.0" />
    <belfry:radius value="3.0" />
</belfry:circle>
```

### Fixed Properties (Still Explicit)
```xml
<belfry:circle id="circle1" name="My Circle">
    <belfry:center_point x="5.0" y="5.0" />
    <belfry:radius value="3.0" fixed="true" />
</belfry:circle>
```

## Default Behavior

- **`fixed` attribute omitted**: Property is free (can be modified by constraints)
- **`fixed="true"`**: Property is fixed (cannot be modified by constraints)
- **`fixed="false"`**: Property is free (explicit, but redundant)

## Parsing Behavior

The parsing methods remain unchanged and will:
- Assume `fixed="false"` when the attribute is not present
- Only handle `fixed="true"` when explicitly specified
- Ignore `fixed="false"` when present (for backward compatibility)

## Impact

- **XML Size**: Reduced file size by eliminating redundant attributes
- **Readability**: Cleaner, more concise XML format
- **Backward Compatibility**: Existing files with `fixed="false"` still work
- **Functionality**: No change in behavior, just cleaner representation

## Testing

- All 9 tests pass ✅
- Example script works correctly ✅
- No regressions in functionality ✅
- Backward compatibility maintained ✅

## Future Considerations

When implementing the constraint system:
1. Properties without `fixed` attribute should be treated as free
2. Properties with `fixed="true"` should be treated as fixed
3. Properties with `fixed="false"` should be treated as free (for backward compatibility) 