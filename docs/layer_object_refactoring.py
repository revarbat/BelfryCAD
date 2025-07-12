# Update document.py to properly use Layer objects instead of layer IDs

"""
DOCUMENT.PY REFACTORING SUMMARY

This update removes all legacy layer ID usage and updates document.py 
to work exclusively with Layer objects.

CHANGES MADE:
1. Updated _serialize_native() to use Layer objects directly
2. Updated _deserialize_native() to use Layer objects directly
3. Removed all layer_id and get_layer_ids() references
4. Use layer.name for serialization instead of layer IDs
5. Use LayerManager methods that work with Layer objects

LAYER OBJECT INTEGRATION:
- Objects now store direct references to Layer objects
- Serialization uses layer.name as identifier
- Deserialization reconstructs Layer object references
- No more layer ID to Layer object mapping needed

KEY METHODS USED:
- self.layers.get_all_layers() - Get all Layer objects
- self.layers.create_layer(name) - Create new Layer object
- self.layers.get_current_layer() - Get current Layer object
- layer.name, layer.color, layer.visible, layer.locked - Layer properties

BACKWARDS COMPATIBILITY:
- Old format files with layer IDs are converted to Layer objects
- New format files use layer names as identifiers
- Objects created in old format get proper Layer object references
"""

# Example of the key changes made:

# OLD (layer ID based):
# obj_data = {
#     "layer": obj.layer_id,  # Integer ID
#     ...
# }
# 
# layers = {
#     layer_id: self.layers.serialize_layer(layer_id)
#     for layer_id in self.layers.get_layer_ids()
# }

# NEW (Layer object based):
# obj_data = {
#     "layer": obj.layer.name,  # Layer name string
#     ...
# }
# 
# layers = {
#     layer.name: {
#         "name": layer.name,
#         "color": layer.color,
#         ...
#     }
#     for layer in self.layers.get_all_layers()
# }

# Benefits of Layer Object Approach:
# 1. Direct object references - no ID lookup needed
# 2. Type safety - Layer objects have known properties
# 3. Extensibility - easy to add new Layer properties
# 4. Consistency - all layer operations use same objects
# 5. Performance - no ID-to-object mapping overhead

print("Document.py has been updated to use Layer objects exclusively")
print("Layer IDs and get_layer_ids() are no longer used")
print("All layer operations now work with Layer objects directly")