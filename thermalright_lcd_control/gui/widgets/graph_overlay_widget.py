# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Graph overlay widgets for displaying metrics history on LCD"""

from collections import deque
from PySide6.QtCore import QTimer, Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QLabel
from PIL import Image, ImageDraw


class GraphOverlayWidget(QLabel):
    """Base class for graph overlay widgets that render on LCD"""
    
    def __init__(self, parent, title, color, width=120, height=60):
        super().__init__(parent)
        self.title = title
        self.graph_color = color
        self.graph_width = width
        self.graph_height = height
        self.font_size = 10  # Default font size for text in graph
        
        # Data buffer (last N data points)
        self.max_data_points = 60  # 60 seconds of data
        self.data_buffer = deque(maxlen=self.max_data_points)
        
        # Initialize with zeros
        for _ in range(self.max_data_points):
            self.data_buffer.append(0)
        
        # Widget setup
        self.resize(width, height)  # Use resize() instead of setFixedSize() to allow resizing
        self.setMinimumSize(80, 40)  # Set minimum size
        self.setMaximumSize(300, 200)  # Set maximum size
        self.setMouseTracking(True)  # Enable mouse tracking for resize cursors
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 180);
                border: 2px solid {color};
                border-radius: 4px;
                color: white;
                font-size: 10px;
                padding: 2px;
            }}
        """)
        
        # Update timer - disabled for GUI, only used by LCD service
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        # Don't start timer - we don't need live updates in GUI
        
        # Mouse drag and resize support
        self.dragging = False
        self.resizing = False
        self.drag_position = None
        self.resize_edge = None
        self.resize_margin = 8  # Pixels from edge to trigger resize
    
    def update_data(self):
        """Override this to update data from metrics source"""
        pass
    
    def add_data_point(self, value):
        """Add a new data point to the buffer"""
        self.data_buffer.append(max(0, min(100, value)))  # Clamp 0-100
        # No GUI update needed - data is only for LCD rendering
    
    def paintEvent(self, event):
        """Custom paint event - just show static placeholder in GUI"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw simple placeholder border
        painter.setPen(QPen(QColor(self.graph_color), 2))
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)
        
        # Draw title
        painter.setPen(QColor("white"))
        painter.drawText(4, 12, self.title)
        
        # Draw size info
        painter.drawText(4, self.height() // 2, f"{self.width()}x{self.height()}")
        
        # Draw "Graph" label
        painter.drawText(4, self.height() - 8, "Graph")
    
    def render_to_pil(self, width=None, height=None):
        """Render graph as PIL Image for LCD display"""
        w = width or self.graph_width
        h = height or self.graph_height
        
        # Create image
        img = Image.new('RGBA', (w, h), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)
        
        # Draw border
        color_rgb = QColor(self.graph_color).getRgb()[:3]
        draw.rectangle([0, 0, w-1, h-1], outline=color_rgb, width=2)
        
        # Draw title (simplified for PIL)
        draw.text((4, 2), self.title, fill=(255, 255, 255))
        
        # Draw current value
        if len(self.data_buffer) > 0:
            current_value = self.data_buffer[-1]
            draw.text((4, h - 14), f"{current_value:.1f}%", fill=(255, 255, 255))
        
        # Draw graph
        if len(self.data_buffer) > 1:
            graph_top = 14
            graph_bottom = h - 16
            graph_height = graph_bottom - graph_top
            graph_left = 4
            graph_right = w - 4
            graph_width = graph_right - graph_left
            
            data_list = list(self.data_buffer)
            point_spacing = graph_width / (len(data_list) - 1)
            
            points = []
            for i in range(len(data_list)):
                x = graph_left + (i * point_spacing)
                y = graph_bottom - (data_list[i] / 100.0 * graph_height)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                draw.line(points, fill=color_rgb, width=2)
        
        return img
    
    def _get_resize_edge(self, pos):
        """Determine which edge is being hovered for resize"""
        rect = self.rect()
        margin = self.resize_margin
        
        on_left = pos.x() < margin
        on_right = pos.x() > rect.width() - margin
        on_top = pos.y() < margin
        on_bottom = pos.y() > rect.height() - margin
        
        # Corner resize (diagonal)
        if on_bottom and on_right:
            return 'bottom-right'
        elif on_bottom and on_left:
            return 'bottom-left'
        elif on_top and on_right:
            return 'top-right'
        elif on_top and on_left:
            return 'top-left'
        # Edge resize
        elif on_right:
            return 'right'
        elif on_left:
            return 'left'
        elif on_bottom:
            return 'bottom'
        elif on_top:
            return 'top'
        
        return None
    
    def _update_cursor(self, edge):
        """Update cursor based on resize edge"""
        if edge == 'bottom-right' or edge == 'top-left':
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == 'bottom-left' or edge == 'top-right':
            self.setCursor(Qt.SizeBDiagCursor)
        elif edge == 'right' or edge == 'left':
            self.setCursor(Qt.SizeHorCursor)
        elif edge == 'bottom' or edge == 'top':
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeAllCursor)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and resize cursor"""
        if self.resizing and self.resize_edge:
            # Calculate new size based on mouse position
            global_pos = event.globalPosition().toPoint()
            delta_x = global_pos.x() - self.drag_position.x()
            delta_y = global_pos.y() - self.drag_position.y()
            
            # Calculate new width and height
            new_width = self.width()
            new_height = self.height()
            new_x = self.x()
            new_y = self.y()
            
            # Handle different resize edges
            if 'right' in self.resize_edge:
                new_width += delta_x
            if 'left' in self.resize_edge:
                new_width -= delta_x
                new_x += delta_x
            if 'bottom' in self.resize_edge:
                new_height += delta_y
            if 'top' in self.resize_edge:
                new_height -= delta_y
                new_y += delta_y
            
            # Apply size constraints (min and max are already set on the widget)
            new_width = max(80, min(300, new_width))
            new_height = max(40, min(200, new_height))
            
            # Apply new geometry
            self.setGeometry(new_x, new_y, new_width, new_height)
            self.graph_width = new_width
            self.graph_height = new_height
            self.drag_position = global_pos
            event.accept()
            
        elif self.dragging:
            # Move widget
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            # Update cursor for resize edges
            edge = self._get_resize_edge(event.pos())
            self._update_cursor(edge)
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging or resizing"""
        if event.button() == Qt.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.drag_position = event.globalPosition().toPoint()
            else:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            was_dragging = self.dragging
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            
            # Snap to grid if was dragging (not resizing)
            if was_dragging:
                main_window = self.window()
                if hasattr(main_window, 'snap_to_grid_position'):
                    snapped_x, snapped_y = main_window.snap_to_grid_position(self.x(), self.y())
                    self.move(snapped_x, snapped_y)
            
            event.accept()
    
    def cleanup(self):
        """Stop updates"""
        self.update_timer.stop()


class CpuGraphWidget(GraphOverlayWidget):
    """CPU usage graph overlay"""
    
    def __init__(self, parent, cpu_metrics):
        super().__init__(parent, "CPU", "#FF6B6B", width=120, height=60)
        self.cpu_metrics = cpu_metrics
    
    def update_data(self):
        """Update CPU data"""
        usage = self.cpu_metrics.get_usage_percentage()
        self.add_data_point(usage)


class GpuGraphWidget(GraphOverlayWidget):
    """GPU usage graph overlay"""
    
    def __init__(self, parent, gpu_metrics):
        super().__init__(parent, "GPU", "#4ECDC4", width=120, height=60)
        self.gpu_metrics = gpu_metrics
    
    def update_data(self):
        """Update GPU data"""
        usage = self.gpu_metrics.get_usage_percentage()
        self.add_data_point(usage)


class MemoryGraphWidget(GraphOverlayWidget):
    """Memory usage graph overlay"""
    
    def __init__(self, parent, memory_metrics):
        super().__init__(parent, "RAM", "#95E1D3", width=120, height=60)
        self.memory_metrics = memory_metrics
    
    def update_data(self):
        """Update Memory data"""
        self.memory_metrics.update()
        usage = self.memory_metrics.get_memory_usage_percent()
        self.add_data_point(usage)
