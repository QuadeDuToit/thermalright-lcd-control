# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Configuration YAML generator"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from ...common.logging_config import get_gui_logger


class ConfigGenerator:
    """Generates YAML configuration files from current UI state"""

    def __init__(self, config):
        self.config = config
        self.logger = get_gui_logger()

    def generate_config_data(self, preview_manager, text_style, metric_widgets,
                             date_widget, time_widget, rotation=0) -> Optional[dict]:
        """Generate YAML configuration file based on current preview state"""
        try:
            print(f"[DEBUG] Generating config with rotation={rotation}")
            foreground_path = self._add_resolution_placeholder(preview_manager.current_foreground_path,
                                                               preview_manager.preview_width,
                                                               preview_manager.preview_height)
            config_data = {
                "display": {
                    "rotation": rotation,
                    "background": {
                        "path": preview_manager.current_background_path or "",
                        "type": preview_manager.determine_background_type(preview_manager.current_background_path).value
                    },
                    "foreground": {
                        "enabled": preview_manager.current_foreground_path is not None,
                        "path": foreground_path,
                        "position": {"x": 0, "y": 0},
                        "alpha": preview_manager.foreground_opacity
                    },
                    "metrics": {
                        "enabled": any(widget.enabled for widget in metric_widgets.values()),
                        "configs": []
                    },
                    "date": self._create_date_time_config(date_widget, 310, 15, text_style),
                    "time": self._create_date_time_config(time_widget, 310, 35, text_style)
                }
            }

            # Add metric configurations
            metric_format_defaults = {
                "cpu_frequency": "{label}{value}{unit}",
                "gpu_frequency": "{label}{value}{unit}"
            }

            for metric_name, widget in metric_widgets.items():
                if widget.enabled:  # Only enabled metrics
                    label = widget.get_label()
                    unit = widget.get_unit()
                    default_format = metric_format_defaults.get(metric_name, "{label}{value}{unit}")

                    metric_config = {
                        "name": metric_name,
                        "label": label,
                        "enabled": widget.enabled,
                        "position": {"x": widget.pos().x(), "y": widget.pos().y()},
                        "font_size": text_style.font_size,
                        "color": self._qcolor_to_hex(text_style.color),
                        "format_string": default_format,
                        "unit": unit
                    }
                    config_data["display"]["metrics"]["configs"].append(metric_config)

            print(f"[DEBUG] config_data has rotation: {'rotation' in config_data.get('display', {})}")
            print(f"[DEBUG] rotation value: {config_data.get('display', {}).get('rotation', 'NOT FOUND')}")
            return config_data

        except Exception as e:
            self.logger.error(f"Error generating config YAML: {e}")
            return None

    def generate_config_yaml(self, preview_manager, text_style, metric_widgets,
                             date_widget, time_widget, rotation=0, preview: bool = False) -> Optional[str]:
        """Generate YAML configuration file based on current preview state"""
        try:
            # Check if rotation changed
            services_config_path = self._get_service_config_file_path(preview_manager.preview_width,
                                                                      preview_manager.preview_height)
            rotation_changed = self._check_rotation_changed(services_config_path, rotation)
            
            config_data = self.generate_config_data(preview_manager, text_style, metric_widgets, date_widget,
                                                    time_widget, rotation)

            self._save_config_file(services_config_path, config_data)
            
            # Restart service if rotation changed (only on Apply)
            if preview and rotation_changed:
                import subprocess
                subprocess.Popen(['systemctl', 'restart', 'thermalright-lcd-control'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Service restarted due to rotation change to {rotation}°")

            if not preview:
                # Save configuration
                config_path = self._get_new_config_file_path(preview_manager.preview_width,
                                                             preview_manager.preview_height)
                self._save_config_file(config_path, config_data)
                print(f"Theme saved with rotation={rotation}° to {config_path.name}")
                return f"{config_path.absolute()}"

        except Exception as e:
            self.logger.error(f"Error generating config YAML: {e}")
        return None

    def _create_date_time_config(self, widget, default_x, default_y, text_style):
        """Create widget configuration dictionary"""
        return {
            "enabled": widget.enabled if widget else False,
            "position": {
                "x": widget.pos().x() if widget else default_x,
                "y": widget.pos().y() if widget else default_y
            },
            "font_size": text_style.font_size,
            "color": self._qcolor_to_hex(text_style.color),
            "text": ""
        }

    def _qcolor_to_hex(self, qcolor):
        """Convert QColor to hex string with alpha"""
        r, g, b, a = qcolor.getRgb()
        return f"#{r:02X}{g:02X}{b:02X}{a:02X}"

    def _get_new_config_file_path(self, dev_width, dev_height) -> Path:
        """Generate new configuration file name and path based on current timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{timestamp}.yaml"
        themes_dir = f"{self.config.get('paths', {}).get('themes_dir', './themes')}/{dev_width}{dev_height}"
        return Path(themes_dir) / filename

    def _get_service_config_file_path(self, dev_width, dev_height) -> Optional[Path]:
        try:
            # Use system-wide config path
            service_config_path = f"/usr/share/thermalright-lcd-control/resources/config/config_{dev_width}{dev_height}.yaml"
            print(f"[DEBUG] service_config_path: {service_config_path}")
            return Path(service_config_path)
        except Exception as e:
            self.logger.error(f"Error updating service config: {e}")
            return None

    def _check_rotation_changed(self, config_path: Path, new_rotation: int) -> bool:
        """Check if rotation value has changed in config"""
        try:
            with open(config_path, 'r') as f:
                current_config = yaml.safe_load(f)
            current_rotation = current_config.get('display', {}).get('rotation', 0)
            return current_rotation != new_rotation
        except:
            return False

    def _save_config_file(self, config_path: Path, config_data: dict) -> str:
        print(f"[DEBUG] Attempting to save config to: {config_path}")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"[DEBUG] Successfully saved config to: {config_path}")
        except Exception as e:
            print(f"[DEBUG] Failed to save config: {e}")
            raise
        return str(config_path)

    def _add_resolution_placeholder(self, path: str, width: int, height: int) -> Optional[str]:

        return path.replace(f"/{width}{height}/", "/{resolution}/") if path is not None else None
