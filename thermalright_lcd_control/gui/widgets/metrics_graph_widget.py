# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Real-time metrics graphs for CPU, GPU, and Memory"""

import pyqtgraph as pg
from collections import deque
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
from PySide6.QtCore import Qt

from ...device_controller.metrics.cpu_metrics import CpuMetrics
from ...device_controller.metrics.gpu_metrics import GpuMetrics
from ...device_controller.metrics.memory_metrics import MemoryMetrics
from ...common.logging_config import get_gui_logger


class MetricsGraphWidget(QWidget):
    """Widget containing real-time graphs for system metrics"""
    
    def __init__(self, parent=None, history_seconds=60):
        super().__init__(parent)
        self.logger = get_gui_logger()
        
        # Metrics objects
        self.cpu_metrics = CpuMetrics()
        self.gpu_metrics = GpuMetrics()
        self.memory_metrics = MemoryMetrics()
        
        # History settings
        self.history_seconds = history_seconds
        self.update_interval_ms = 500  # Update every 500ms
        self.max_data_points = int(history_seconds * 1000 / self.update_interval_ms)
        
        # Data buffers (deque for efficient rolling window)
        self.time_data = deque(maxlen=self.max_data_points)
        self.cpu_usage_data = deque(maxlen=self.max_data_points)
        self.cpu_temp_data = deque(maxlen=self.max_data_points)
        self.gpu_usage_data = deque(maxlen=self.max_data_points)
        self.gpu_temp_data = deque(maxlen=self.max_data_points)
        self.memory_data = deque(maxlen=self.max_data_points)
        
        self.current_time = 0
        
        # Setup UI
        self.setup_ui()
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(self.update_interval_ms)
        
        # Initial update
        self.update_metrics()
    
    def setup_ui(self):
        """Setup the graph UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Configure PyQtGraph
        pg.setConfigOptions(antialias=True)
        
        # CPU Graph
        cpu_group = QGroupBox("CPU Metrics")
        cpu_layout = QVBoxLayout(cpu_group)
        
        self.cpu_label = QLabel("CPU: -- | Temp: --°C")
        self.cpu_label.setStyleSheet("font-weight: bold; color: #FF6B6B;")
        cpu_layout.addWidget(self.cpu_label)
        
        self.cpu_graph = pg.PlotWidget()
        self.cpu_graph.setBackground('w')
        self.cpu_graph.setLabel('left', 'Usage %', color='black')
        self.cpu_graph.setLabel('bottom', 'Time (seconds)', color='black')
        self.cpu_graph.setYRange(0, 100)
        self.cpu_graph.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_graph.setFixedHeight(150)
        
        self.cpu_usage_curve = self.cpu_graph.plot(pen=pg.mkPen(color='#FF6B6B', width=2))
        self.cpu_temp_curve = self.cpu_graph.plot(pen=pg.mkPen(color='#FFA500', width=2, style=Qt.DashLine))
        
        cpu_layout.addWidget(self.cpu_graph)
        layout.addWidget(cpu_group)
        
        # GPU Graph
        gpu_group = QGroupBox("GPU Metrics")
        gpu_layout = QVBoxLayout(gpu_group)
        
        self.gpu_label = QLabel("GPU: -- | Temp: --°C")
        self.gpu_label.setStyleSheet("font-weight: bold; color: #4ECDC4;")
        gpu_layout.addWidget(self.gpu_label)
        
        self.gpu_graph = pg.PlotWidget()
        self.gpu_graph.setBackground('w')
        self.gpu_graph.setLabel('left', 'Usage %', color='black')
        self.gpu_graph.setLabel('bottom', 'Time (seconds)', color='black')
        self.gpu_graph.setYRange(0, 100)
        self.gpu_graph.showGrid(x=True, y=True, alpha=0.3)
        self.gpu_graph.setFixedHeight(150)
        
        self.gpu_usage_curve = self.gpu_graph.plot(pen=pg.mkPen(color='#4ECDC4', width=2))
        self.gpu_temp_curve = self.gpu_graph.plot(pen=pg.mkPen(color='#FFA500', width=2, style=Qt.DashLine))
        
        gpu_layout.addWidget(self.gpu_graph)
        layout.addWidget(gpu_group)
        
        # Memory Graph
        memory_group = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout(memory_group)
        
        self.memory_label = QLabel("RAM: -- GB / -- GB (--%) | Swap: -- GB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #95E1D3;")
        memory_layout.addWidget(self.memory_label)
        
        self.memory_graph = pg.PlotWidget()
        self.memory_graph.setBackground('w')
        self.memory_graph.setLabel('left', 'Usage %', color='black')
        self.memory_graph.setLabel('bottom', 'Time (seconds)', color='black')
        self.memory_graph.setYRange(0, 100)
        self.memory_graph.showGrid(x=True, y=True, alpha=0.3)
        self.memory_graph.setFixedHeight(150)
        
        self.memory_curve = self.memory_graph.plot(pen=pg.mkPen(color='#95E1D3', width=2))
        
        memory_layout.addWidget(self.memory_graph)
        layout.addWidget(memory_group)
    
    def update_metrics(self):
        """Update all metrics and graphs"""
        try:
            # Update metrics
            self.cpu_metrics.update()
            self.gpu_metrics.update()
            self.memory_metrics.update()
            
            # Append time point
            self.current_time += self.update_interval_ms / 1000.0
            self.time_data.append(self.current_time)
            
            # CPU data
            cpu_usage = self.cpu_metrics.get_cpu_usage()
            cpu_temp = self.cpu_metrics.get_cpu_temp()
            if cpu_temp is None:
                cpu_temp = 0
            
            self.cpu_usage_data.append(cpu_usage)
            self.cpu_temp_data.append(cpu_temp)
            self.cpu_label.setText(f"CPU: {cpu_usage:.1f}% | Temp: {cpu_temp:.1f}°C")
            
            # GPU data
            gpu_usage = self.gpu_metrics.get_gpu_usage()
            gpu_temp = self.gpu_metrics.get_gpu_temp()
            
            self.gpu_usage_data.append(gpu_usage)
            self.gpu_temp_data.append(gpu_temp)
            self.gpu_label.setText(f"GPU: {gpu_usage:.1f}% | Temp: {gpu_temp:.1f}°C")
            
            # Memory data
            mem_percent = self.memory_metrics.get_memory_usage_percent()
            mem_used = self.memory_metrics.get_memory_used_gb()
            mem_total = self.memory_metrics.get_memory_total_gb()
            swap_used = self.memory_metrics.get_swap_used_gb()
            
            self.memory_data.append(mem_percent)
            self.memory_label.setText(
                f"RAM: {mem_used:.1f} GB / {mem_total:.1f} GB ({mem_percent:.1f}%) | Swap: {swap_used:.1f} GB"
            )
            
            # Update graphs
            if len(self.time_data) > 1:
                # Calculate time axis (show last N seconds)
                time_axis = [t - self.current_time for t in self.time_data]
                
                # CPU graph
                self.cpu_usage_curve.setData(time_axis, list(self.cpu_usage_data))
                self.cpu_temp_curve.setData(time_axis, list(self.cpu_temp_data))
                
                # GPU graph
                self.gpu_usage_curve.setData(time_axis, list(self.gpu_usage_data))
                self.gpu_temp_curve.setData(time_axis, list(self.gpu_temp_data))
                
                # Memory graph
                self.memory_curve.setData(time_axis, list(self.memory_data))
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def cleanup(self):
        """Stop updates and cleanup"""
        self.update_timer.stop()
