# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Graph renderer for LCD display"""

from collections import deque
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

from .config import GraphConfig


class GraphRenderer:
    """Renders sparkline graphs for metrics on LCD"""
    
    def __init__(self, graph_config: GraphConfig):
        self.config = graph_config
        self.data_buffer = deque(maxlen=60)  # 60 seconds of data
        
        # Initialize with zeros
        for _ in range(60):
            self.data_buffer.append(0)
    
    def update_data(self, value: float):
        """Add new data point to buffer"""
        # Clamp value between 0-100
        clamped_value = max(0, min(100, value))
        self.data_buffer.append(clamped_value)
    
    def render(self, metrics: dict) -> Image.Image:
        """Render the graph as a PIL Image"""
        w = self.config.width
        h = self.config.height
        
        # Create transparent image
        img = Image.new('RGBA', (w, h), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)
        
        # Parse color
        color_rgb = self._hex_to_rgb(self.config.color)
        
        # Draw border
        draw.rectangle([0, 0, w-1, h-1], outline=color_rgb, width=2)
        
        # Get title and current value based on graph type
        title, current_value = self._get_graph_data(metrics)
        
        # Update data buffer
        self.update_data(current_value)
        
        # Load font with configured size
        try:
            font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", self.config.font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Regular.ttf", self.config.font_size)
            except:
                font = ImageFont.load_default()
        
        # Draw title
        draw.text((4, 2), title, fill=(255, 255, 255), font=font)
        
        # Draw current value
        draw.text((4, h - 14), f"{current_value:.1f}%", fill=(255, 255, 255), font=font)
        
        # Draw graph line
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
    
    def _get_graph_data(self, metrics: dict) -> Tuple[str, float]:
        """Get title and current value based on graph type"""
        if self.config.graph_type == 'cpu':
            value = metrics.get('cpu_usage', 0)
            return "CPU", value
        elif self.config.graph_type == 'gpu':
            value = metrics.get('gpu_usage', 0)
            return "GPU", value
        elif self.config.graph_type == 'memory':
            value = metrics.get('memory_usage', 0)
            return "RAM", value
        else:
            return "???", 0
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        if len(hex_color) >= 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        else:
            return (255, 255, 255)  # Default white
