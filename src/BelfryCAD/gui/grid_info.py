
import math
from typing import Union, Tuple, List
from enum import Enum

from PySide6.QtWidgets import (
    QVBoxLayout,
    QGraphicsView,
    QLabel,
    QDialog,
    QComboBox,
    QDialogButtonBox,
)
from PySide6.QtGui import (
    QColor,
)


class GridUnits(Enum):
    """Grid units for the scene."""
    INCHES_DECIMAL = "Inches (Decimal)"
    INCHES_FRACTION = "Inches (Fraction)"
    FEET_DECIMAL = "Feet (Decimal)"
    FEET_FRACTION = "Feet (Fraction)"
    YARDS_DECIMAL = "Yards (Decimal)"
    YARDS_FRACTION = "Yards (Fraction)"
    MILLIMETERS = "Millimeters"
    CENTIMETERS = "Centimeters"
    METERS = "Meters"


class GridInfo(object):
    """Grid info for the scene."""
    def __init__(
            self,
            units: GridUnits = GridUnits.INCHES_FRACTION,
            base_color="#0000ff",
            decimal_places=3
    ):
        self._units = units
        self._base_color = QColor(base_color)
        self._decimal_places = decimal_places

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value: GridUnits):
        self._units = value

    @property
    def base_color(self):
        return self._base_color

    @base_color.setter
    def base_color(self, value: Union[str, QColor]):
        if isinstance(value, str):
            value = QColor(value)
        self._base_color = value

    @property
    def decimal_places(self):
        return self._decimal_places

    @decimal_places.setter
    def decimal_places(self, value: int):
        self._decimal_places = value

    @property
    def grid_spacings(self):
        return {
            GridUnits.INCHES_DECIMAL: [
                    120.0, 60.0, 10.0, 5.0, 1.0, 0.5,
                    0.1, 0.05, 0.01, 0.005, 0.001
                ],
            GridUnits.INCHES_FRACTION: [
                    120.0, 36.0, 12.0, 3.0, 1.0,
                    1/4, 1/16, 1/64, 1/256
                ],
            GridUnits.FEET_DECIMAL: [
                    100.0, 50.0, 10.0, 5.0, 1.0, 0.5,
                    0.1, 0.05, 0.01, 0.005, 0.001
                ],
            GridUnits.FEET_FRACTION: [
                    100.0, 50.0, 10.0, 5.0, 1.0,
                    1/2, 1/4, 1/12, 1/12/4, 1/12/16,
                    1/12/64, 1/12/256
                ],
            GridUnits.YARDS_DECIMAL: [
                    100.0, 50.0, 10.0, 5.0, 1.0,
                    0.5, 0.1, 0.05, 0.01
                ],
            GridUnits.YARDS_FRACTION: [
                    100.0, 50.0, 10.0, 5.0, 1.0,
                    1/3, 1/3/2, 1/3/4, 1/3/12, 1/3/12/4,
                    1/3/12/16, 1/3/12/64, 1/3/12/256
                ],
            GridUnits.MILLIMETERS: [
                    10000.0, 5000.0, 1000.0, 500.0, 100.0, 50.0,
                    10.0, 5.0, 1.0, 0.5, 0.1
                ],
            GridUnits.CENTIMETERS: [
                    1000.0, 500.0, 100.0, 50.0, 10.0, 5.0,
                    1.0, 0.5, 0.1, 0.05, 0.01
                ],
            GridUnits.METERS: [
                    100.0, 50.0, 10.0, 5.0, 1.0, 0.5,
                    0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001
                ],
        }[self.units]

    @property
    def unit_label(self):
        return {
            GridUnits.INCHES_DECIMAL: "Inch",
            GridUnits.INCHES_FRACTION: "Inch",
            GridUnits.FEET_DECIMAL: "Foot",
            GridUnits.FEET_FRACTION: "Foot",
            GridUnits.YARDS_DECIMAL: "Yard",
            GridUnits.YARDS_FRACTION: "Yard",
            GridUnits.MILLIMETERS: "mm",
            GridUnits.CENTIMETERS: "cm",
            GridUnits.METERS: "m",
        }[self.units]

    @property
    def use_fractions(self):
        return {
            GridUnits.INCHES_DECIMAL: False,
            GridUnits.INCHES_FRACTION: True,
            GridUnits.FEET_DECIMAL: False,
            GridUnits.FEET_FRACTION: True,
            GridUnits.YARDS_DECIMAL: False,
            GridUnits.YARDS_FRACTION: True,
            GridUnits.MILLIMETERS: False,
            GridUnits.CENTIMETERS: False,
            GridUnits.METERS: False,
        }[self.units]

    @property
    def is_metric(self):
        if self.units in [
            GridUnits.MILLIMETERS,
            GridUnits.CENTIMETERS,
            GridUnits.METERS
        ]:
            return True
        return False

    @property
    def unit_scale(self):
        return {
            GridUnits.INCHES_DECIMAL: 1.0,
            GridUnits.INCHES_FRACTION: 1.0,
            GridUnits.FEET_DECIMAL: 12.0,
            GridUnits.FEET_FRACTION: 12.0,
            GridUnits.YARDS_DECIMAL: 36.0,
            GridUnits.YARDS_FRACTION: 36.0,
            GridUnits.MILLIMETERS: 1/25.4,
            GridUnits.CENTIMETERS: 1/2.54,
            GridUnits.METERS: 1/0.0254,
        }[self.units]

    def get_relevant_spacings(self, scaling: float) \
            -> Tuple[List[float], float]:
        """Get the relevant grid spacings for the given scaling factor."""
        unit_scale = self.unit_scale
        spacings = [
            space * unit_scale for space in self.grid_spacings
            if space * unit_scale * scaling >= 10.0
        ]
        if len(spacings) > 4:
            spacings = spacings[-4:]
        while len(spacings) < 4:
            spacings.insert(0, spacings[0] * 10.0)
        label_spacing = spacings[-2]
        while label_spacing * scaling > 75.0:
            label_spacing /= 2.0
        while label_spacing * scaling < 30.0:
            label_spacing *= 2.0
        return (spacings, label_spacing)

    def grid_line_color(self, level: int) -> QColor:
        """Get the color for the grid line at the given level."""
        color = self.base_color
        hue = color.hueF()
        saturation = min(1.0, color.saturationF() * math.pow(0.65, level))
        value = color.valueF()
        result = QColor()
        result.setHsvF(hue, saturation, value)
        return result

    def _superscript_numbers(self, value: int) -> str:
        """Get the superscript for the given number string."""
        superscripts = {
            "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
            "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        }
        valstr = f"{value}"
        for digit, superscript in superscripts.items():
            valstr = valstr.replace(digit, superscript)
        return valstr

    def _subscript_numbers(self, value: int) -> str:
        """Get the subscript for the given number string."""
        subscripts = {
            "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
            "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
        }
        valstr = f"{value}"
        for digit, subscript in subscripts.items():
            valstr = valstr.replace(digit, subscript)
        return valstr

    def _fractionize(self, value: float, no_subs: bool = False) -> str:
        """Fractionize the given value."""
        sign = "" if value >= 0 else "-"
        whole = int(abs(value))
        fraction = abs(value) - whole
        denominator = 1024
        numerator = round(fraction * denominator)
        while numerator > 0 and numerator % 2 == 0:
            numerator //= 2
            denominator //= 2
        if numerator == 0:
            fracstr = "0" if whole == 0 else ""
        elif no_subs:
            fracstr = f"{numerator}/{denominator}"
        elif numerator == 1 and denominator == 8:
            fracstr = "⅛"
        elif numerator == 1 and denominator == 4:
            fracstr = "¼"
        elif numerator == 3 and denominator == 8:
            fracstr = "⅜"
        elif numerator == 1 and denominator == 2:
            fracstr = "½"
        elif numerator == 5 and denominator == 8:
            fracstr = "⅝"
        elif numerator == 3 and denominator == 4:
            fracstr = "¾"
        elif numerator == 7 and denominator == 8:
            fracstr = "⅞"
        else:
            numerstr = self._superscript_numbers(numerator)
            denomstr = self._subscript_numbers(denominator)
            fracstr = f"{numerstr}\u2044{denomstr}"
        if whole == 0:
            return f"{sign}{fracstr}"
        if numerator == 0:
            return f"{sign}{whole}"
        return f"{sign}{whole}\n{fracstr}"

    def format_label(self, value: float, no_subs: bool = False) -> str:
        """Format the label for the grid."""
        value /= self.unit_scale
        if self.units == GridUnits.FEET_FRACTION:
            frac = round((abs(value) - int(abs(value))) * 12.0, 8)
            fracstr = self._fractionize(frac, no_subs)
            if fracstr == "0":
                return f"{int(value)}'"
            if fracstr:
                fracstr += '"'
            if int(abs(value)) == 0:
                sign = "" if value >= 0 else "-"
                return f"{sign}{fracstr}"
            if not fracstr:
                return f"{int(value)}'"
            return f"{int(value)}' {fracstr}"
        elif self.units == GridUnits.YARDS_FRACTION:
            frac = round((abs(value) - int(abs(value))) * 36.0, 8)
            fracstr = self._fractionize(frac, no_subs)
            if int(abs(value)) == 0:
                return f"{fracstr}\""
            if fracstr == "0":
                return f"{int(value)}y"
            return f"{int(value)}y {fracstr}\""
        if self.use_fractions:
            return self._fractionize(value, no_subs)
        elif value.is_integer():
            return f"{int(value)}"
        else:
            return f"{value:.{self.decimal_places}f}".rstrip("0").rstrip(".")

    @staticmethod
    def get_dpi(view: QGraphicsView) -> float:
        """Get the DPI from the view."""
        return view.physicalDpiX()
    
    @staticmethod
    def get_zoom(view: QGraphicsView) -> float:
        """Get the zoom level, in percentage."""
        dpi = GridInfo.get_dpi(view)
        return view.transform().m11() / dpi * 100

    @staticmethod
    def set_zoom(view: QGraphicsView, zoom: float) -> float:
        """Set the zoom level, in percentage."""
        dpi = GridInfo.get_dpi(view)
        view.resetTransform()
        view.scale(dpi, -dpi)
        view.scale(zoom / 100.0, zoom / 100.0)
        view.update()
        return zoom

    @staticmethod
    def zoom_adjust(view: QGraphicsView, increase: bool = True) -> float:
        """Adjust the scaling factor to the next/previous zoom level."""
        zoom_levels = [
            1, 2, 3, 5, 8, 10, 15, 20, 33, 50, 75,
            100, 150, 200, 300, 400, 500, 600, 800,
            1000, 1500, 2000, 3000, 4000, 5000, 6000, 8000,
            10000,
        ]
        old_zoom = round(GridInfo.get_zoom(view))
        if increase:
            zooms = [x for x in zoom_levels if x > old_zoom]
            new_zoom = zooms[0] if zooms else zoom_levels[-1]
        else:
            zooms = [x for x in zoom_levels if x < old_zoom]
            new_zoom = zooms[-1] if zooms else zoom_levels[0]
        new_zoom = max(zoom_levels[0], min(new_zoom, zoom_levels[-1]))
        GridInfo.set_zoom(view, new_zoom)
        return new_zoom


class UnitSelectionDialog(QDialog):
    """Dialog for selecting grid units."""

    def __init__(self, current_unit: GridUnits, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Grid Units")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Create combo box for unit selection
        self.unit_combo = QComboBox()
        for unit in GridUnits:
            self.unit_combo.addItem(unit.value, unit)

        # Set current selection
        index = self.unit_combo.findData(current_unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)

        layout.addWidget(QLabel("Grid Units:"))
        layout.addWidget(self.unit_combo)

        # Add OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.resize(300, 100)

    def get_selected_unit(self) -> GridUnits:
        """Get the selected grid unit."""
        return self.unit_combo.currentData()

