"""
Color utilities for BelfryCAD GUI components.

This module provides a centralized Colors class for all color-related
operations including HSV conversions, color parsing, and color manipulation
functions.
"""

from typing import Tuple, Union

from PySide6.QtGui import QColor


class Colors:
    """
    Utility class for color operations and conversions.

    This class provides static methods for:
    - Converting between QColor and HSV values
    - Parsing color specifications from strings
    - Adjusting color properties like saturation
    - Color manipulation functions
    """

    @staticmethod
    def to_hsv(color: Union[QColor, str]) -> Tuple[float, float, float]:
        """
        Convert QColor to HSV values.

        Args:
            color: QColor object or color string

        Returns:
            Tuple of (hue, saturation, value) where:
            - hue is in range 0-360 degrees
            - saturation is in range 0-1 
            - value is in range 0-1
        """
        if isinstance(color, str):
            color = QColor(color)
        elif isinstance(color, QColor):
            pass
        else:
            color = QColor(0, 255, 255)  # Default cyan

        # Get HSV values from QColor
        h = color.hueF()
        s = color.saturationF()
        v = color.valueF()
        return (h * 360.0 if h >= 0 else 0.0, s, v)

    @staticmethod
    def from_hsv(hue: float, saturation: float, value: float) -> QColor:
        """
        Create QColor from HSV values.

        Args:
            hue: Hue in degrees (0-360)
            saturation: Saturation (0-1)
            value: Value/brightness (0-1)

        Returns:
            QColor object
        """
        color = QColor()
        color.setHsvF(hue / 360.0, saturation, value)
        return color

    @staticmethod
    def adjust_saturation(color: Union[QColor, str], factor: float) -> QColor:
        """
        Adjust color saturation by given factor.

        Args:
            color: QColor object, color string, or other color specification
            factor: Multiplication factor for saturation
            (e.g., 0.5 = half saturation)

        Returns:
            QColor with adjusted saturation
        """
        if isinstance(color, str):
            color = QColor(color)
        elif not isinstance(color, QColor):
            color = QColor(color)

        hue = color.hueF()
        saturation = min(1.0, color.saturationF() * factor)
        value = color.valueF()

        result = QColor()
        result.setHsvF(hue, saturation, value)
        return result

    @staticmethod
    def parse(color_spec: Union[QColor, str, None]) -> QColor:
        """
        Parse color specification into QColor.

        Args:
            color_spec: Color specification - can be:
                - QColor object (returned as-is)
                - String color name or hex code
                - None (returns default cyan)

        Returns:
            QColor object
        """
        if isinstance(color_spec, QColor):
            return color_spec
        elif isinstance(color_spec, str):
            if color_spec.startswith('#'):
                return QColor(color_spec)
            else:
                return Colors._parse_named_color(color_spec)
        else:
            return QColor(0, 255, 255)  # Default cyan

    @staticmethod
    def _parse_named_color(color_name: str) -> QColor:
        """
        Parse named color to QColor.

        Args:
            color_name: Named color string

        Returns:
            QColor object
        """
        color_name = color_name.lower()

        # Common color mappings
        color_map = {
            "black": QColor(0, 0, 0),
            "white": QColor(255, 255, 255),
            "red": QColor(255, 0, 0),
            "green": QColor(0, 255, 0),
            "blue": QColor(0, 0, 255),
            "yellow": QColor(255, 255, 0),
            "cyan": QColor(0, 255, 255),
            "magenta": QColor(255, 0, 255),
            "gray": QColor(128, 128, 128),
            "grey": QColor(128, 128, 128),
        }

        if color_name in color_map:
            return color_map[color_name]
        else:
            try:
                # Try Qt's built-in color parsing
                return QColor(color_name)
            except Exception:
                return QColor(0, 0, 0)  # Default to black

    @staticmethod
    def adjust_brightness(color: Union[QColor, str], factor: float) -> QColor:
        """
        Adjust color brightness/value by given factor.

        Args:
            color: QColor object or color string
            factor: Multiplication factor for brightness
            (e.g., 1.2 = 20% brighter)

        Returns:
            QColor with adjusted brightness
        """
        if isinstance(color, str):
            color = QColor(color)
        elif not isinstance(color, QColor):
            color = QColor(color)

        hue = color.hueF()
        saturation = color.saturationF()
        value = min(1.0, color.valueF() * factor)

        result = QColor()
        result.setHsvF(hue, saturation, value)
        return result

    @staticmethod
    def adjust_hue(color: Union[QColor, str], hue_shift: float) -> QColor:
        """
        Adjust color hue by shifting it by degrees.

        Args:
            color: QColor object or color string
            hue_shift: Degrees to shift hue (+/- 360)

        Returns:
            QColor with adjusted hue
        """
        if isinstance(color, str):
            color = QColor(color)
        elif not isinstance(color, QColor):
            color = QColor(color)

        current_hue = color.hueF() * 360.0 if color.hueF() >= 0 else 0.0
        new_hue = (current_hue + hue_shift) % 360.0
        saturation = color.saturationF()
        value = color.valueF()

        result = QColor()
        result.setHsvF(new_hue / 360.0, saturation, value)
        return result

    @staticmethod
    def blend(color1: Union[QColor, str], color2: Union[QColor, str],
              ratio: float = 0.5) -> QColor:
        """
        Blend two colors together.

        Args:
            color1: First color
            color2: Second color  
            ratio: Blend ratio (0.0 = all color1, 1.0 = all color2)

        Returns:
            QColor representing the blended result
        """
        if isinstance(color1, str):
            color1 = Colors.parse(color1)
        if isinstance(color2, str):
            color2 = Colors.parse(color2)

        ratio = max(0.0, min(1.0, ratio))  # Clamp to 0-1

        r = int(color1.red() * (1 - ratio) + color2.red() * ratio)
        g = int(color1.green() * (1 - ratio) + color2.green() * ratio)
        b = int(color1.blue() * (1 - ratio) + color2.blue() * ratio)
        a = int(color1.alpha() * (1 - ratio) + color2.alpha() * ratio)

        return QColor(r, g, b, a)

    @staticmethod
    def to_hex(color: QColor) -> str:
        """
        Convert QColor to hex string representation.

        Args:
            color: QColor object

        Returns:
            Hex color string (e.g., "#ff0000")
        """
        return color.name()

    @staticmethod
    def get_contrast_color(color: Union[QColor, str]) -> QColor:
        """
        Get a contrasting color (black or white) for text on colored
        background.

        Args:
            color: Background color

        Returns:
            QColor that contrasts well (black or white)
        """
        if isinstance(color, str):
            color = Colors.parse(color)

        # Calculate luminance using standard formula
        r = color.redF()
        g = color.greenF()
        b = color.blueF()

        # Convert to linear RGB
        def to_linear(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r_linear = to_linear(r)
        g_linear = to_linear(g)
        b_linear = to_linear(b)

        # Calculate relative luminance
        luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear

        # Return white for dark backgrounds, black for light backgrounds
        return QColor(255, 255, 255) if luminance < 0.5 else QColor(0, 0, 0)
