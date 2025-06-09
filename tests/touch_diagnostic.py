#!/usr/bin/env python3
"""
Touch Event Diagnostic Script

This script creates a simple window that logs all touch events to help diagnose
why pinch-to-zoom might not be working.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QTouchEvent

class TouchEventLogger(QMainWindow):
    """Simple window that logs all touch events"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Touch Event Diagnostic")
        self.setGeometry(100, 100, 600, 400)
        
        # Enable touch events
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.log_label = QLabel(
            "Touch Event Diagnostic\n\n"
            "Try the following gestures:\n"
            "• Single finger touch and move\n"
            "• Two finger touch and move\n"
            "• Pinch gestures\n"
            "• Trackpad gestures (on macOS)\n\n"
            "Events will be logged below:\n"
            "=" * 40
        )
        self.log_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_label.setWordWrap(True)
        layout.addWidget(self.log_label)
        
        self.event_count = 0
    
    def event(self, event):
        """Override to catch all events"""
        event_type = event.type()
        
        # Log touch-related events
        if event_type in [QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd]:
            self.log_touch_event(event)
            return True
        
        # Also log mouse events for comparison
        elif event_type in [QEvent.Type.MouseButtonPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonRelease]:
            self.log_mouse_event(event)
        
        return super().event(event)
    
    def log_touch_event(self, event):
        """Log touch event details"""
        self.event_count += 1
        event_type_name = {
            QEvent.Type.TouchBegin: "TouchBegin",
            QEvent.Type.TouchUpdate: "TouchUpdate", 
            QEvent.Type.TouchEnd: "TouchEnd"
        }.get(event.type(), f"Touch({event.type()})")
        
        touch_points = event.touchPoints() if hasattr(event, 'touchPoints') else []
        num_points = len(touch_points)
        
        log_text = f"\n[{self.event_count}] {event_type_name}: {num_points} touch points"
        
        if num_points > 0:
            for i, point in enumerate(touch_points):
                pos = point.pos()
                log_text += f"\n  Point {i}: ({pos.x():.1f}, {pos.y():.1f})"
                
        # Calculate distance for 2-point gestures
        if num_points == 2:
            p1, p2 = touch_points[0].pos(), touch_points[1].pos()
            distance = ((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)**0.5
            log_text += f"\n  Distance: {distance:.1f}"
        
        self.update_log(log_text)
        event.accept()
    
    def log_mouse_event(self, event):
        """Log mouse event for comparison"""
        if hasattr(event, 'pos'):
            pos = event.pos()
            event_name = {
                QEvent.Type.MouseButtonPress: "MousePress",
                QEvent.Type.MouseMove: "MouseMove",
                QEvent.Type.MouseButtonRelease: "MouseRelease"
            }.get(event.type(), "Mouse")
            
            log_text = f"\n[Mouse] {event_name}: ({pos.x()}, {pos.y()})"
            self.update_log(log_text)
    
    def update_log(self, new_text):
        """Update the log display"""
        current_text = self.log_label.text()
        lines = current_text.split('\n')
        
        # Keep only the header and last 20 log lines
        header_end = None
        for i, line in enumerate(lines):
            if "=" * 40 in line:
                header_end = i
                break
        
        if header_end is not None:
            header = '\n'.join(lines[:header_end + 1])
            log_lines = lines[header_end + 1:]
            
            # Add new log entry
            log_lines.extend(new_text.split('\n'))
            
            # Keep only last 20 log entries
            if len(log_lines) > 20:
                log_lines = log_lines[-20:]
            
            updated_text = header + '\n' + '\n'.join(log_lines)
            self.log_label.setText(updated_text)

def run_touch_diagnostic():
    """Run the touch event diagnostic"""
    app = QApplication(sys.argv)
    
    window = TouchEventLogger()
    window.show()
    
    print("Touch Event Diagnostic started.")
    print("Try various touch gestures in the window.")
    print("Check the console and window for event logs.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    run_touch_diagnostic()
