from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, 
    QGraphicsRectItem, QGraphicsDropShadowEffect, QGraphicsItem
)
from PySide6.QtGui import QBrush
from PySide6.QtCore import Qt
import sys

class SelectableRect(QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setBrush(QBrush(Qt.green))
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def setSelected(self, selected):
        super().setSelected(selected)
        self.updateEffect()

    def updateEffect(self):
        if self.isSelected():
            effect = QGraphicsDropShadowEffect()
            effect.setColor(Qt.blue)
            effect.setBlurRadius(30)
            effect.setOffset(0)
            #effect = QGraphicsColorizeEffect()
            #effect.setColor(Qt.red)  # selection color tint
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

app = QApplication(sys.argv)

scene = QGraphicsScene()
view = QGraphicsView(scene)
view.setRenderHint(view.renderHints() | view.renderHints().Antialiasing)
view.setDragMode(QGraphicsView.RubberBandDrag)

# Create selectable items
for x in range(0, 300, 120):
    item = SelectableRect(0, 0, 100, 50)
    item.setPos(x, 0)
    scene.addItem(item)

# Update effects on selection changes
def updateAll():
    for item in scene.items():
        if isinstance(item, SelectableRect):
            item.updateEffect()

scene.selectionChanged.connect(updateAll)

scene.setSceneRect(-50, -50, 400, 200)
view.show()
sys.exit(app.exec())

