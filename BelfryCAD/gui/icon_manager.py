"""
Icon Manager for BelfryCAD GUI.

This module provides centralized icon loading and caching functionality
for all GUI components in BelfryCAD.
"""

import os
from typing import Optional, Dict
from PySide6.QtGui import QIcon


class IconManager:
    """
    Centralized icon manager that handles loading and caching of icons
    from various resource locations.
    """
    
    _instance: Optional['IconManager'] = None
    _icon_cache: Dict[str, QIcon] = {}
    
    def __new__(cls) -> 'IconManager':
        """Ensure singleton pattern for icon manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the icon manager."""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Define search paths for icons in order of preference
        self._search_paths = [
            "BelfryCAD/resources/icons/",
            "resources/icons/",
            "images/",  # Legacy fallback
            "icons/",   # Legacy fallback
        ]
        
        # Supported file extensions in order of preference
        self._extensions = [".svg", ".png", ".gif"]
    
    def get_icon(self, icon_name: str) -> QIcon:
        """
        Get an icon by name, loading and caching it if necessary.
        
        Args:
            icon_name: Name of the icon (without extension) or full path
            
        Returns:
            QIcon object (may be null if icon not found)
        """
        if not icon_name:
            return QIcon()
        
        # Check cache first
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]
        
        # Load the icon
        icon = self._load_icon(icon_name)
        
        # Cache the result (even if it's a null icon to avoid repeated searches)
        self._icon_cache[icon_name] = icon
        
        return icon
    
    def _load_icon(self, icon_name: str) -> QIcon:
        """
        Load an icon from the file system.
        
        Args:
            icon_name: Name of the icon (without extension) or full path
            
        Returns:
            QIcon object (may be null if icon not found)
        """
        # If icon_name is already a full path, try it directly first
        if os.path.sep in icon_name or icon_name.endswith(tuple(self._extensions)):
            if os.path.exists(icon_name):
                icon = QIcon(icon_name)
                if not icon.isNull():
                    return icon
        
        # Try all combinations of search paths and extensions
        icon_paths = []
        
        # Generate all possible paths
        for search_path in self._search_paths:
            for extension in self._extensions:
                icon_paths.append(f"{search_path}{icon_name}{extension}")
        
        # Also try the icon_name as a direct path (last resort)
        icon_paths.append(icon_name)
        
        # Try to load from each path
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    return icon
        
        # Return empty icon if not found
        return QIcon()
    
    def preload_icons(self, icon_names: list[str]) -> None:
        """
        Preload a list of icons into the cache.
        
        Args:
            icon_names: List of icon names to preload
        """
        for icon_name in icon_names:
            self.get_icon(icon_name)
    
    def clear_cache(self) -> None:
        """Clear the icon cache."""
        self._icon_cache.clear()
    
    def get_cache_size(self) -> int:
        """Get the number of cached icons."""
        return len(self._icon_cache)
    
    def is_cached(self, icon_name: str) -> bool:
        """Check if an icon is already cached."""
        return icon_name in self._icon_cache
    
    @classmethod
    def get_instance(cls) -> 'IconManager':
        """Get the singleton instance of IconManager."""
        return cls()


# Global convenience function for easy access
def get_icon(icon_name: str) -> QIcon:
    """
    Convenience function to get an icon using the global IconManager instance.
    
    Args:
        icon_name: Name of the icon (without extension) or full path
        
    Returns:
        QIcon object (may be null if icon not found)
    """
    return IconManager.get_instance().get_icon(icon_name)


# Preload commonly used icons
def preload_common_icons():
    """Preload commonly used icons for better performance."""
    common_icons = [
        # Layer icons
        "layer-visible",
        "layer-invisible", 
        "layer-locked",
        "layer-unlocked",
        "layer-cam",
        "layer-nocam",
        "layer-new",
        "layer-delete",
        
        # Snap icons
        "snap-center",
        "snap-centerlines",
        "snap-contours",
        "snap-controlpoints",
        "snap-endpoint",
        "snap-grid",
        "snap-intersection",
        "snap-midpoint",
        "snap-nearest",
        "snap-perpendicular",
        "snap-quadrant",
        "snap-tangent",
        
        # Tool icons (common ones)
        "tool-line",
        "tool-circle",
        "tool-rectangle",
        "tool-arc",
        "tool-bezier",
        "tool-point",
        "tool-text",
        "tool-objsel",
        "tool-nodesel",
    ]
    
    IconManager.get_instance().preload_icons(common_icons)


# Initialize common icons when module is imported
preload_common_icons() 