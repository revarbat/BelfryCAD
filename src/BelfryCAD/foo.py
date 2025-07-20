from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsItem, QStyle
)
from PySide6.QtGui import QPainter, QPen, QPalette
from PySide6.QtCore import QRectF, Qt
import sys

# Custom QGraphicsItem that draws its own selection
class MyCustomItem(QGraphicsItem):
    def boundingRect(self):
        return QRectF(-30, -20, 60, 40)

    def paint(self, painter, option, widget):
        # Draw the shape
        painter.setPen(Qt.black)
        painter.setBrush(Qt.yellow)
        painter.drawEllipse(self.boundingRect())

        # Draw selection outline
        if option.state & QStyle.State_Selected:
            palette = widget.palette()
            hl_color = palette.color(QPalette.ColorRole.Highlight)
            pen = QPen(Qt.DashLine)
            pen.setColor(hl_color)
            pen.setWidth(2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())

    def __init__(self):
        super().__init__()
        self.setFlags(QGraphicsItem.ItemIsSelectable)

app = QApplication(sys.argv)

scene = QGraphicsScene()

# Set up QGraphicsView to allow rubberband selection
view = QGraphicsView(scene)
view.setRenderHint(QPainter.Antialiasing)
view.setDragMode(QGraphicsView.RubberBandDrag)  # enables click & drag selection

# OPTIONAL: customize the palette to change default selection outline color
palette = view.palette()
palette.setColor(QPalette.Highlight, Qt.red)
view.setPalette(palette)

# A built-in QGraphicsRectItem with default selection handling
rect_item = QGraphicsRectItem(0, 0, 100, 50)
rect_item.setBrush(Qt.green)
rect_item.setFlag(QGraphicsItem.ItemIsSelectable)
rect_item.setPos(-120, 0)
scene.addItem(rect_item)

# Our custom item that draws its own selection
custom_item = MyCustomItem()
custom_item.setPos(100, 0)
scene.addItem(custom_item)

# Set scene rect
scene.setSceneRect(-200, -100, 400, 200)

view.show()
sys.exit(app.exec())

