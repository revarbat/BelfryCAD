from PySide6.QtWidgets import QGraphicsScene


class CadScene(QGraphicsScene):
    """Custom graphics scene for CAD operations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Dictionary to store tags for each item: {item: set_of_tags}
        self._item_tags = {}
        # Reverse lookup dictionary: {tag: set_of_items}
        self._tag_items = {}
    
    def add_tag_to_item(self, item, tag: str):
        """Add a tag to an item."""
        if item not in self._item_tags:
            self._item_tags[item] = set()
        self._item_tags[item].add(tag)
        
        # Update reverse lookup
        if tag not in self._tag_items:
            self._tag_items[tag] = set()
        self._tag_items[tag].add(item)
    
    def remove_tag_from_item(self, item, tag: str):
        """Remove a tag from an item."""
        if item in self._item_tags:
            self._item_tags[item].discard(tag)
            # Clean up empty tag sets
            if not self._item_tags[item]:
                del self._item_tags[item]
        
        # Update reverse lookup
        if tag in self._tag_items:
            self._tag_items[tag].discard(item)
            # Clean up empty item sets
            if not self._tag_items[tag]:
                del self._tag_items[tag]
    
    def set_item_tags(self, item, tags: list):
        """Set all tags for an item (replaces existing tags)."""
        # Remove item from all existing tags in reverse lookup
        if item in self._item_tags:
            for old_tag in self._item_tags[item]:
                if old_tag in self._tag_items:
                    self._tag_items[old_tag].discard(item)
                    if not self._tag_items[old_tag]:
                        del self._tag_items[old_tag]
        
        # Set new tags
        if tags:
            self._item_tags[item] = set(tags)
            # Update reverse lookup for new tags
            for tag in tags:
                if tag not in self._tag_items:
                    self._tag_items[tag] = set()
                self._tag_items[tag].add(item)
        elif item in self._item_tags:
            del self._item_tags[item]
    
    def get_item_tags(self, item) -> set:
        """Get all tags for an item."""
        return self._item_tags.get(item, set()).copy()
    
    def has_tag(self, item, tag: str) -> bool:
        """Check if an item has a specific tag."""
        return item in self._item_tags and tag in self._item_tags[item]
    
    def get_items_with_tag(self, tag: str) -> list:
        """Get all items that have a specific tag."""
        return list(self._tag_items.get(tag, set()))
    
    def get_items_with_all_tags(self, tags: list) -> list:
        """Get all items that have ALL of the specified tags."""
        if not tags:
            return []
        
        # Start with items that have the first tag, then intersect with others
        result_set = self._tag_items.get(tags[0], set()).copy()
        for tag in tags[1:]:
            if tag in self._tag_items:
                result_set.intersection_update(self._tag_items[tag])
            else:
                # If any tag doesn't exist, no items can have all tags
                return []
        
        return list(result_set)
    
    def get_items_with_any_tags(self, tags: list) -> list:
        """Get all items that have ANY of the specified tags."""
        if not tags:
            return []
        
        # Union all items that have any of the specified tags
        result_set = set()
        for tag in tags:
            if tag in self._tag_items:
                result_set.update(self._tag_items[tag])
        
        return list(result_set)
    
    def clear_item_tags(self, item):
        """Remove all tags from an item."""
        if item in self._item_tags:
            # Remove item from all tags in reverse lookup
            for tag in self._item_tags[item]:
                if tag in self._tag_items:
                    self._tag_items[tag].discard(item)
                    if not self._tag_items[tag]:
                        del self._tag_items[tag]
            del self._item_tags[item]
    
    def removeItem(self, item):
        """Override removeItem to clean up tags when items are removed."""
        super().removeItem(item)
        self.clear_item_tags(item)
