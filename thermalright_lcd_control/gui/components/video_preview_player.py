# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Fast video preview player for GUI - doesn't pre-decode all frames"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from PySide6.QtCore import QTimer, Signal, QObject, Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QLabel

from ...common.logging_config import get_gui_logger


class VideoPreviewPlayer(QObject):
    """Lightweight video player for GUI preview - loads frames on-demand"""
    
    first_frame_ready = Signal(QPixmap)
    frame_ready = Signal(QPixmap)
    error_occurred = Signal(str)
    
    def __init__(self, video_path: str, target_width: int, target_height: int, 
                 foreground_path: str = None, foreground_opacity: float = 0.5):
        super().__init__()
        self.logger = get_gui_logger()
        self.video_path = video_path
        self.target_width = target_width
        self.target_height = target_height
        self.foreground_path = foreground_path
        self.foreground_opacity = foreground_opacity
        
        self.video_capture = None
        self.fps = 30
        self.frame_duration_ms = 33
        self.current_frame = 0
        self.total_frames = 0
        self.foreground_image = None
        
        # Load foreground if provided
        if self.foreground_path:
            self._load_foreground()
        
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._next_frame)
        
    def initialize(self):
        """Initialize video capture and show first frame immediately"""
        try:
            self.video_capture = cv2.VideoCapture(self.video_path)
            
            if not self.video_capture.isOpened():
                self.error_occurred.emit(f"Cannot open video: {self.video_path}")
                return False
            
            # Get video properties
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_duration_ms = int(1000 / self.fps) if self.fps > 0 else 33
            
            self.logger.info(f"Video preview initialized: {Path(self.video_path).name}")
            self.logger.info(f"  FPS: {self.fps:.2f}, Frames: {self.total_frames}, Duration: {self.frame_duration_ms}ms")
            
            # Load and show first frame immediately
            ret, frame = self.video_capture.read()
            if ret:
                pixmap = self._frame_to_pixmap(frame)
                self.first_frame_ready.emit(pixmap)
                self.current_frame = 1
                return True
            else:
                self.error_occurred.emit("Cannot read first frame")
                return False
                
        except Exception as e:
            self.error_occurred.emit(str(e))
            return False
    
    def _load_foreground(self):
        """Load foreground image for overlay"""
        try:
            fg_image = Image.open(self.foreground_path)
            if fg_image.mode != 'RGBA':
                fg_image = fg_image.convert('RGBA')
            # Resize to match target dimensions
            fg_image = fg_image.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
            self.foreground_image = fg_image
            self.logger.debug(f"Foreground loaded: {Path(self.foreground_path).name}")
        except Exception as e:
            self.logger.error(f"Failed to load foreground: {e}")
            self.foreground_image = None
    
    def _composite_foreground(self, background_array):
        """Composite foreground onto background array"""
        if not self.foreground_image:
            return background_array
        
        try:
            # Convert numpy array to PIL Image
            bg_image = Image.fromarray(background_array)
            if bg_image.mode != 'RGBA':
                bg_image = bg_image.convert('RGBA')
            
            # Apply alpha to foreground
            fg_with_alpha = self.foreground_image.copy()
            alpha = fg_with_alpha.split()[3]
            alpha = alpha.point(lambda p: int(p * self.foreground_opacity))
            fg_with_alpha.putalpha(alpha)
            
            # Composite
            composited = Image.alpha_composite(bg_image, fg_with_alpha)
            
            # Convert back to RGB numpy array
            return np.array(composited.convert('RGB'))
        except Exception as e:
            self.logger.error(f"Foreground compositing error: {e}")
            return background_array
    
    def _frame_to_pixmap(self, frame) -> QPixmap:
        """Convert OpenCV frame to QPixmap with optional foreground overlay"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to target dimensions
        frame_resized = cv2.resize(frame_rgb, (self.target_width, self.target_height), 
                                   interpolation=cv2.INTER_LINEAR)
        
        # Apply foreground overlay if present
        if self.foreground_image:
            frame_resized = self._composite_foreground(frame_resized)
        
        # Convert to QImage
        height, width, channel = frame_resized.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_resized.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(q_image)
    
    def _next_frame(self):
        """Load and display next frame"""
        if not self.video_capture or not self.video_capture.isOpened():
            self.stop()
            return
        
        ret, frame = self.video_capture.read()
        
        if ret:
            pixmap = self._frame_to_pixmap(frame)
            self.frame_ready.emit(pixmap)
            self.current_frame += 1
        else:
            # Loop back to start
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
    
    def play(self):
        """Start playing video"""
        if self.video_capture and self.video_capture.isOpened():
            self.playback_timer.start(self.frame_duration_ms)
            self.logger.debug(f"Video preview playback started at {self.fps:.2f} FPS")
    
    def stop(self):
        """Stop playing video"""
        self.playback_timer.stop()
        self.logger.debug("Video preview playback stopped")
    
    def cleanup(self):
        """Release video resources"""
        self.stop()
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
