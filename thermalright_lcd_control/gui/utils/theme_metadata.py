# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Theme metadata manager for storing theme names and properties
"""

import json
from pathlib import Path
from typing import Optional, Dict


class ThemeMetadata:
    """Manager for theme metadata (names, descriptions, etc.)"""
    
    def __init__(self, metadata_file: Path):
        self.metadata_file = metadata_file
        self.metadata: Dict[str, Dict[str, str]] = {}
        self.load()
    
    def load(self):
        """Load metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}
        else:
            self.metadata = {}
    
    def save(self):
        """Save metadata to JSON file"""
        try:
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Failed to save theme metadata: {e}")
    
    def get_name(self, config_filename: str) -> Optional[str]:
        """Get user-friendly name for a theme config file"""
        return self.metadata.get(config_filename, {}).get('name')
    
    def set_name(self, config_filename: str, name: str):
        """Set user-friendly name for a theme config file"""
        if config_filename not in self.metadata:
            self.metadata[config_filename] = {}
        self.metadata[config_filename]['name'] = name
        self.save()
    
    def delete(self, config_filename: str):
        """Remove metadata for a theme"""
        if config_filename in self.metadata:
            del self.metadata[config_filename]
            self.save()
    
    def get_display_name(self, config_filename: str) -> str:
        """Get display name (custom name or fallback to filename)"""
        custom_name = self.get_name(config_filename)
        if custom_name:
            return custom_name
        
        # Fallback: clean up filename
        name = Path(config_filename).stem
        if name.startswith('config_'):
            name = name.replace('config_', '')
        return name
