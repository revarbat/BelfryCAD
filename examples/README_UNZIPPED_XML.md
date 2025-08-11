# Unzipped XML Version

## Overview

The `complex_test_document.xml` file is the unzipped, human-readable version of the complex test document. This allows you to inspect the XML structure directly without needing to extract it from the ZIP file.

## Files Available

### 1. **`complex_test_document.xml`**
- **Size**: 8,909 bytes
- **Format**: Raw XML (uncompressed)
- **Content**: Human-readable XML structure
- **Purpose**: Direct inspection of document structure

### 2. **`complex_test_document_formatted.xml`**
- **Size**: Larger (formatted with indentation)
- **Format**: Pretty-printed XML
- **Content**: Same as above but with proper indentation
- **Purpose**: Easy reading and analysis

### 3. **`complex_test_document.belcad`**
- **Size**: 1,426 bytes
- **Format**: ZIP-compressed XML
- **Content**: Compressed version for storage/transmission
- **Purpose**: Production use (84% compression ratio)

## XML Structure Overview

The XML document follows the BelfryCAD format with the namespace `http://belfrydw.com/xml/BelfryCAD/1.0`:

```xml
<?xml version="1.0" ?>
<belfry:belfrycad_document xmlns:belfry="http://belfrydw.com/xml/BelfryCAD/1.0" version="1.0">
  <belfry:header>
    <belfry:preferences units="mm" precision="2" use_fractions="false" 
                       grid_visible="True" show_rulers="True" 
                       canvas_bg_color="#f0f0f0" grid_color="#d0d0d0" 
                       selection_color="#ff8000"/>
  </belfry:header>
  
  <belfry:parameters>
    <!-- 15 parameters with expressions -->
  </belfry:parameters>
  
  <belfry:objects>
    <!-- 20 objects organized in groups -->
  </belfry:objects>
</belfry:belfrycad_document>
```

## Key Sections

### Header Section
Contains document preferences:
- **Units**: mm
- **Precision**: 2 decimal places
- **Fractions**: false
- **Grid**: visible
- **Rulers**: visible
- **Colors**: Background, grid, and selection colors

### Parameters Section
15 parameters including:
- Simple values: `base_width="100.0"`
- Expressions: `gear_teeth_2="$gear_teeth_1 * $gear_ratio"`

### Objects Section
20 objects organized in 5 groups:
- **Base Assembly**: 4 lines forming rectangle
- **Mounting Holes**: 4 circles
- **Gear Assembly**: 2 gears
- **Mechanism**: Arc, ellipse, bezier curve
- **Reference Elements**: Line and circle

## Object Examples

### Line Object
```xml
<belfry:line id="1" name="Base Line 11" color="black" line_width="0.5" 
             visible="true" locked="false" parent="16">
  <belfry:start_point x="0.0" y="0.0"/>
  <belfry:end_point x="100.0" y="0.0"/>
</belfry:line>
```

### Circle Object
```xml
<belfry:circle id="5" name="Mounting Hole 11" color="blue" line_width="0.3" 
               visible="true" locked="false" parent="17">
  <belfry:center_point x="10.0" y="10.0"/>
  <belfry:radius value="8.0"/>
</belfry:circle>
```

### Gear Object
```xml
<belfry:gear id="9" name="Drive Gear1" color="red" line_width="0.4" 
             visible="true" locked="false" parent="18">
  <belfry:center_point x="25.0" y="40.0"/>
  <belfry:pitch_radius value="25.0"/>
  <belfry:num_teeth value="20"/>
  <belfry:pressure_angle value="20.0"/>
</belfry:gear>
```

### Group Object
```xml
<belfry:group id="16" name="Base Assembly1" color="black" line_width="0.5" 
              visible="true" locked="false">
  <!-- Child objects -->
</belfry:group>
```

## Compression Benefits

The ZIP compression provides significant benefits:
- **Original size**: 8,909 bytes
- **Compressed size**: 1,426 bytes
- **Compression ratio**: 84% reduction
- **Space savings**: 7,483 bytes per file

## Usage

### View the XML
```bash
# View raw XML
cat complex_test_document.xml

# View formatted XML
cat complex_test_document_formatted.xml

# View with syntax highlighting (if available)
less complex_test_document_formatted.xml
```

### Extract from ZIP
```bash
# Extract XML from .belcad file
unzip -p complex_test_document.belcad document.xml > extracted.xml
```

### Validate XML
```bash
# Basic XML validation
xmllint --noout complex_test_document.xml

# Format XML
xmllint --format complex_test_document.xml > formatted.xml
```

## Analysis Benefits

Having the unzipped XML allows you to:

1. **Inspect Structure**: See exactly how objects are organized
2. **Debug Issues**: Identify problems in the XML format
3. **Understand Relationships**: See parent-child group relationships
4. **Verify Parameters**: Check parameter expressions and values
5. **Learn Format**: Understand the XML schema by example
6. **Manual Editing**: Make small changes if needed
7. **Documentation**: Use as reference for format specification

## File Comparison

| File | Size | Format | Purpose |
|------|------|--------|---------|
| `complex_test_document.belcad` | 1,426 bytes | ZIP | Production use |
| `complex_test_document.xml` | 8,909 bytes | Raw XML | Inspection |
| `complex_test_document_formatted.xml` | ~12KB | Pretty XML | Analysis |

## Notes

- The XML file contains the same data as the .belcad file
- The .belcad file also contains metadata.json (not shown in XML)
- Both files can be loaded by BelfryCAD
- The XML version is useful for development and debugging
- The compressed version is better for storage and transmission

This unzipped version provides full transparency into the document structure and is invaluable for understanding and working with the BelfryCAD XML format. 