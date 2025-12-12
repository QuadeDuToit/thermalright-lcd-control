# SPDX-License-Identifier: Apache-2.0

import psutil
from . import Metrics
from ...common.logging_config import LoggerConfig


class MemoryMetrics(Metrics):
    """
    Memory metrics for RAM usage monitoring
    """
    def __init__(self):
        super().__init__()
        self.logger = LoggerConfig.setup_service_logger()
        self.memory_used_gb = 0.0
        self.memory_total_gb = 0.0
        self.memory_percent = 0.0
        self.swap_used_gb = 0.0
        self.swap_total_gb = 0.0
        self.swap_percent = 0.0

    def update(self):
        """Update memory metrics"""
        try:
            # Get virtual memory (RAM)
            mem = psutil.virtual_memory()
            self.memory_used_gb = mem.used / (1024 ** 3)  # Convert to GB
            self.memory_total_gb = mem.total / (1024 ** 3)
            self.memory_percent = mem.percent

            # Get swap memory
            swap = psutil.swap_memory()
            self.swap_used_gb = swap.used / (1024 ** 3)
            self.swap_total_gb = swap.total / (1024 ** 3)
            self.swap_percent = swap.percent

        except Exception as e:
            self.logger.error(f"Error updating memory metrics: {e}")
            self.memory_percent = 0.0
            self.swap_percent = 0.0

    def get_memory_usage_percent(self):
        """Get current memory usage percentage"""
        return self.memory_percent

    def get_memory_used_gb(self):
        """Get used memory in GB"""
        return self.memory_used_gb

    def get_memory_total_gb(self):
        """Get total memory in GB"""
        return self.memory_total_gb

    def get_swap_usage_percent(self):
        """Get current swap usage percentage"""
        return self.swap_percent

    def get_swap_used_gb(self):
        """Get used swap in GB"""
        return self.swap_used_gb

    def get_swap_total_gb(self):
        """Get total swap in GB"""
        return self.swap_total_gb

    def get_all_metrics(self):
        """Get all memory metrics as a dictionary"""
        return {
            'memory_used_gb': round(self.memory_used_gb, 2),
            'memory_total_gb': round(self.memory_total_gb, 2),
            'memory_percent': round(self.memory_percent, 1),
            'swap_used_gb': round(self.swap_used_gb, 2),
            'swap_total_gb': round(self.swap_total_gb, 2),
            'swap_percent': round(self.swap_percent, 1)
        }

    # Implement abstract methods from Metrics base class
    def get_temperature(self):
        """Memory doesn't have temperature - return None"""
        return None

    def get_usage_percentage(self):
        """Return memory usage percentage"""
        return self.memory_percent

    def get_frequency(self):
        """Memory frequency not tracked - return None"""
        return None

    def get_metric_value(self, metric_name):
        """Get specific metric value by name"""
        metrics_map = {
            'memory_percent': self.memory_percent,
            'memory_used_gb': self.memory_used_gb,
            'memory_total_gb': self.memory_total_gb,
            'swap_percent': self.swap_percent,
            'swap_used_gb': self.swap_used_gb,
            'swap_total_gb': self.swap_total_gb
        }
        return metrics_map.get(metric_name, None)

    def __str__(self):
        """String representation of memory metrics"""
        return (f"Memory: {self.memory_used_gb:.1f}/{self.memory_total_gb:.1f} GB "
                f"({self.memory_percent:.1f}%) | "
                f"Swap: {self.swap_used_gb:.1f}/{self.swap_total_gb:.1f} GB "
                f"({self.swap_percent:.1f}%)")
