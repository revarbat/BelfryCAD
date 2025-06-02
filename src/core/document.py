import json
from pathlib import Path
from typing import Optional
from .cad_objects import CADObjectManager


class Document:
    """Manages the current CAD document, file I/O, and modification state."""
    def __init__(self):
        self._filename: Optional[str] = None
        self._modified: bool = False
        self.objects = CADObjectManager()

    @property
    def filename(self) -> Optional[str]:
        return self._filename

    @filename.setter
    def filename(self, value: str):
        self._filename = value

    def is_modified(self) -> bool:
        return self._modified

    def mark_modified(self):
        self._modified = True

    def clear_modified(self):
        self._modified = False

    def new(self):
        self.objects.clear_all()
        self._filename = None
        self.clear_modified()

    def save(self, filename: Optional[str] = None):
        if filename:
            self._filename = filename
        if not self._filename:
            raise ValueError("No filename specified for saving.")
        ext = Path(self._filename).suffix.lower()
        if ext == ".tkcad":
            self._save_native()
        else:
            raise NotImplementedError(
                f"Saving format '{ext}' not supported yet."
            )
        self.clear_modified()

    def load(self, filename: str):
        ext = Path(filename).suffix.lower()
        if ext == ".tkcad":
            self._load_native(filename)
        else:
            raise NotImplementedError(
                f"Loading format '{ext}' not supported yet."
            )
        self._filename = filename
        self.clear_modified()

    def get_filename(self) -> Optional[str]:
        return self._filename

    def set_filename(self, filename: str):
        self._filename = filename

    def _save_native(self):
        data = self._serialize_native()
        with open(self._filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_native(self, filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._deserialize_native(data)

    def _serialize_native(self):
        # Serialize all objects and layers (simple version)
        return {
            "objects": [
                obj.__dict__ for obj in self.objects.get_all_objects()
            ],
            "layers": self.objects.layers,
            "current_layer": self.objects.current_layer,
        }

    def _deserialize_native(self, data):
        # Clear and restore objects and layers
        self.objects.clear_all()
        self.objects.layers = data.get(
            "layers", {0: ["Layer 0", "black", True, False]}
        )
        self.objects.current_layer = data.get("current_layer", 0)
        # Restore objects
        objects_data = data.get("objects", [])
        for obj_data in objects_data:
            # Try to reconstruct the object using the manager's create_object
            try:
                object_type = obj_data.get("object_type")
                if hasattr(object_type, "value"):
                    object_type = object_type.value
                # Map string to ObjectType enum if needed
                from .cad_objects import ObjectType, Point
                if isinstance(object_type, str):
                    object_type_enum = ObjectType(object_type)
                else:
                    object_type_enum = object_type
                # Rebuild coords
                coords = [Point(**pt) for pt in obj_data.get("coords", [])]
                # Use attributes, layer, etc.
                obj = self.objects.create_object(
                    object_type_enum,
                    *coords,
                    layer=obj_data.get("layer", 0),
                    **obj_data.get("attributes", {})
                )
                obj.selected = obj_data.get("selected", False)
                obj.visible = obj_data.get("visible", True)
                obj.locked = obj_data.get("locked", False)
            except Exception:
                continue
