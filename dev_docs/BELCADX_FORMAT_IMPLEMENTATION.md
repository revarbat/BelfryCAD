# BelfryCAD XML Format (.belcadx) Implementation

## Overview
Successfully implemented support for `.belcadx` files - uncompressed XML versions of the `.belcad` files. This provides users with a human-readable format for BelfryCAD documents that can be easily inspected, edited, and version-controlled.

## File Format Comparison

### .belcad (Compressed Format)
- Zip-compressed archive containing XML and metadata
- Smaller file size
- Binary format (not directly readable)
- Contains `document.xml` and `metadata.json`

### .belcadx (Uncompressed XML Format)  
- Plain XML file with UTF-8 encoding
- Human-readable and editable
- Larger file size
- Identical XML structure to the XML inside .belcad files
- Pretty-printed with proper indentation

## Implementation Details

### 1. XML Serializer Enhancements
**File**: `src/BelfryCAD/utils/xml_serializer.py`

Added new methods to `BelfryCADXMLSerializer` class:
- `save_document_xml()` - Save to uncompressed XML format
- `load_document_xml()` - Load from uncompressed XML format

**Key Features:**
- Uses `ET.indent()` for pretty-printing XML output
- Maintains same namespace and structure as compressed format
- Proper UTF-8 encoding with XML declaration
- Identical parsing logic for both formats

### 2. Convenience Functions
Added global convenience functions:
- `save_belfrycad_xml_document()` - Save .belcadx files
- `load_belfrycad_xml_document()` - Load .belcadx files

### 3. GUI Integration
**File**: `src/BelfryCAD/gui/document_window.py`

**Updated File Dialogs:**
- Open dialog: `"BelfryCAD files (*.belcad *.belcadx);;BelfryCAD Compressed (*.belcad);;BelfryCAD XML (*.belcadx);;All files (*.*)"`
- Save dialog: `"BelfryCAD Compressed (*.belcad);;BelfryCAD XML (*.belcadx);;..."`

**Enhanced File Operations:**
- `load_belcad_file()` - Auto-detects format by extension
- `_save_document_file()` - New helper method for format-aware saving
- Updated `save_file()` and `save_as_file()` methods

**Format Detection Logic:**
```python
if filepath_lower.endswith('.belcadx'):
    # Use XML format
elif filepath_lower.endswith('.belcad'):
    # Use compressed format
else:
    # Default to compressed format
```

## XML Structure Example

```xml
<?xml version="1.0" encoding="utf-8"?>
<belfry:belfrycad_document xmlns:belfry="http://belfrydw.com/xml/BelfryCAD/1.0" version="1.0">
  <belfry:header>
    <belfry:preferences units="mm" precision="2" use_fractions="false" 
                       grid_visible="True" show_rulers="True" 
                       canvas_bg_color="#f0f0f0" grid_color="#d0d0d0" 
                       selection_color="#ff8000" />
  </belfry:header>
  <belfry:parameters>
    <belfry:parameter name="base_width" expression="100.0" />
    <belfry:parameter name="base_height" expression="80.0" />
  </belfry:parameters>
  <belfry:objects>
    <belfry:line id="1" name="line1" color="black" line_width="0.5" 
                 visible="true" locked="false">
      <belfry:start_point x="0.0" y="0.0" />
      <belfry:end_point x="100.0" y="0.0" />
    </belfry:line>
  </belfry:objects>
</belfry:belfrycad_document>
```

## Testing Results

### ✅ Successful Tests
- **Basic Save/Load**: Simple document with line object
- **Complex Document**: 20+ objects with parameters and groups
- **Round-trip Conversion**: .belcad → .belcadx → .belcadx
- **Format Detection**: Automatic detection by file extension
- **File Dialogs**: Updated filters working correctly

### Test Cases Verified
1. **Simple Document Creation**:
   - Created document with single line object
   - Saved as .belcadx format
   - Loaded back successfully
   - Verified object count and properties

2. **Complex Document Conversion**:
   - Loaded existing .belcad file (20 objects)
   - Converted to .belcadx format
   - Verified all objects preserved
   - Checked XML structure and formatting

3. **Round-trip Verification**:
   - .belcadx → load → save → .belcadx
   - Data integrity maintained
   - No loss of information

## Benefits

### For Users
1. **Transparency**: Human-readable file format
2. **Version Control**: Text-based format works well with Git
3. **Debugging**: Easy to inspect document structure
4. **Editing**: Manual editing possible (with care)
5. **Choice**: Can choose between compressed (.belcad) and readable (.belcadx)

### For Developers
1. **Testing**: Easier to create and verify test documents
2. **Debugging**: Can inspect serialized output directly
3. **Documentation**: Example documents can be shared as text
4. **Integration**: Standard XML tools can process files

## File Size Comparison
- `.belcad`: Compressed, typically 70-90% smaller
- `.belcadx`: Uncompressed, larger but human-readable
- Choose based on use case: storage/sharing vs. inspection/editing

## Usage Guidelines

### When to Use .belcadx
- Version control scenarios
- Collaborative editing
- Debugging document issues
- Educational/demonstration purposes
- Manual inspection of document structure

### When to Use .belcad
- Regular document storage
- Sharing via email/web
- Archive storage
- Production use

## Backward Compatibility
- Full backward compatibility maintained
- Existing .belcad files continue to work unchanged
- New .belcadx format is additive, not replacing

## Future Enhancements
- Could add schema validation for .belcadx files
- Potential for XSL transformations
- Integration with external XML tools
- Diff/merge tools for version control

## Conclusion
The .belcadx format implementation successfully provides users with a transparent, editable alternative to the compressed .belcad format while maintaining full compatibility and feature parity. 