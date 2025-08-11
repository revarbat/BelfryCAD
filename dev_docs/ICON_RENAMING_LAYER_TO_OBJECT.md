# Icon Renaming: Layer to Object

## Overview

Renamed all `layer-*.svg` icons to `object-*.svg` to better reflect their purpose as object visibility indicators rather than layer-related icons.

## Changes Made

### 1. **Icon Files Renamed**

The following icons were renamed in `src/BelfryCAD/resources/icons/`:

- `layer-visible.svg` → `object-visible.svg`
- `layer-invisible.svg` → `object-invisible.svg`
- `layer-locked.svg` → `object-locked.svg`
- `layer-unlocked.svg` → `object-unlocked.svg`
- `layer-cam.svg` → `object-cam.svg`
- `layer-nocam.svg` → `object-nocam.svg`

### 2. **Code Updates**

#### `src/BelfryCAD/gui/panes/object_tree_pane.py`
Updated all icon references from `layer-*` to `object-*`:

```python
# Before
visibility_btn.setIcon(self.icon_manager.get_icon("layer-visible" if group.visible else "layer-invisible"))

# After
visibility_btn.setIcon(self.icon_manager.get_icon("object-visible" if group.visible else "object-invisible"))
```

**Lines Updated:**
- Line 140: Group visibility button
- Line 180: Object visibility button  
- Line 209: Default icon mapping

### 3. **Documentation Updates**

#### `dev_docs/GROUP_SYSTEM_CLARIFICATION.md`
- Updated icon usage explanation to reference `object-*` instead of `layer-*`

#### `dev_docs/LAYER_TO_GROUP_CLARIFICATION.md`
- Updated icon usage clarification to reference `object-*` instead of `layer-*`

## Rationale

### Why Rename?
1. **Accuracy**: Icons represent object visibility states, not layer functionality
2. **Consistency**: Aligns with the group-based organization system
3. **Clarity**: Eliminates confusion about layer vs object functionality
4. **Semantic Correctness**: Icons are used for object visibility toggles

### Icon Usage Context
These icons are used in the Object Tree Pane for:
- Visibility toggle buttons for groups and objects
- Default icons for objects without specific type icons
- Visual indicators of object state (visible/invisible, locked/unlocked)

## Icon Functions

### `object-visible.svg`
- Used when an object or group is visible
- Displayed in visibility toggle buttons
- Default icon for visible objects without specific type icons

### `object-invisible.svg`
- Used when an object or group is hidden
- Displayed in visibility toggle buttons
- Default icon for invisible objects without specific type icons

### `object-locked.svg`
- Used when an object or group is locked
- Prevents modifications to the object/group

### `object-unlocked.svg`
- Used when an object or group is unlocked
- Allows modifications to the object/group

### `object-cam.svg`
- Used for CAM-related object states
- Indicates objects that are CAM-enabled

### `object-nocam.svg`
- Used for non-CAM object states
- Indicates objects that are not CAM-enabled

## Testing Results

- **All 9 tests pass** ✅
- **Example script works correctly** ✅
- **No regressions in functionality** ✅
- **Icons load properly** ✅
- **Old layer-* icons removed** ✅

## Impact

### Benefits
1. **Clearer Naming**: Icon names now accurately reflect their purpose
2. **Reduced Confusion**: No more layer-related naming in a group-based system
3. **Better Maintainability**: Code and icons are semantically aligned
4. **Consistent Architecture**: Supports the group-centric design

### No Breaking Changes
- All functionality remains the same
- Icons display correctly in the UI
- No user-facing changes in behavior
- Backward compatibility maintained through code updates

## Future Considerations

When adding new visibility-related icons:
- Use `object-*` prefix for object state icons
- Use `group-*` prefix for group-specific icons
- Maintain semantic clarity in icon naming
- Update documentation to reflect new naming conventions

## Conclusion

The icon renaming successfully aligns the visual assets with the group-based architecture, eliminating any confusion about layer functionality while maintaining all existing functionality. The new naming convention is more accurate and supports the system's design philosophy. 