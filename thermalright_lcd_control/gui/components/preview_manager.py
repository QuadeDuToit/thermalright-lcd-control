# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Preview manager for display generation and frame updates"""

from pathlib import Path

from PySide6.QtCore import QTimer, QThread, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QLabel

from ...device_controller.display.config import DisplayConfig, BackgroundType
from ...device_controller.display.generator import DisplayGenerator
from .video_preview_player import VideoPreviewPlayer


class DisplayGeneratorLoader(QThread):
    """Thread for loading DisplayGenerator asynchronously"""
    generator_ready = Signal(object)  # DisplayGenerator object
    generator_failed = Signal(str)  # Error message
    progress_updated = Signal(str)  # Progress message
    progress_percentage = Signal(int)  # Progress percentage 0-100

    def __init__(self, display_config):
        super().__init__()
        self.display_config = display_config
        self.current_progress = 10
        self.is_loading = True

    def run(self):
        """Load DisplayGenerator in background thread"""
        try:
            self.progress_updated.emit("Initializing video loader...")
            self.progress_percentage.emit(10)
            
            # Start progress simulation
            from PySide6.QtCore import QTimer
            import time
            
            self.progress_updated.emit("Loading video frames...")
            
            # Simulate progress while loading
            start_time = time.time()
            self.progress_percentage.emit(20)
            
            # Load in a way that allows us to check progress
            # This runs in thread, so DisplayGenerator blocks here
            import threading
            result = {'generator': None, 'error': None}
            
            def load():
                try:
                    result['generator'] = DisplayGenerator(self.display_config)
                except Exception as e:
                    result['error'] = str(e)
            
            load_thread = threading.Thread(target=load)
            load_thread.start()
            
            # Update progress while waiting
            progress = 30
            while load_thread.is_alive():
                load_thread.join(0.5)  # Wait 500ms
                if progress < 90:
                    progress += 10
                    elapsed = time.time() - start_time
                    self.progress_percentage.emit(progress)
                    self.progress_updated.emit(f"Loading video... ({elapsed:.1f}s)")
            
            if result['error']:
                self.generator_failed.emit(result['error'])
            else:
                self.progress_percentage.emit(100)
                self.progress_updated.emit("Complete!")
                self.generator_ready.emit(result['generator'])
                
        except Exception as e:
            self.generator_failed.emit(str(e))


class PreviewManager:
    """Manages display generation and frame updates for preview"""

    def __init__(self, config, preview_label: QLabel, text_style, progress_bar=None, overlay_raise_callback=None):
        self.config = config
        self.preview_label = preview_label
        self.text_style = text_style
        self.progress_bar = progress_bar
        self.overlay_raise_callback = overlay_raise_callback

        # Display properties
        self.preview_width = 320
        self.preview_height = 240
        self.current_background_path = None
        self.current_foreground_path = None
        self.foreground_opacity = 0.5

        # Components
        self.display_generator = None
        self.generator_loader = None  # Track loader thread
        self.video_player = None  # Fast video preview player
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview_frame)

    def set_device_dimensions(self, width: int, height: int):
        """Set preview dimensions from detected device"""
        self.preview_width = width
        self.preview_height = height

    def initialize_default_background(self, backgrounds_dir: str):
        """Initialize with the first background file found"""
        try:
            backgrounds_path = Path(backgrounds_dir)
            if not backgrounds_path.exists():
                self.preview_label.setText("Background directory\nnot found")
                return

            supported_formats = self.config.get('supported_formats', {})
            supported_extensions = (set(supported_formats.get('images', [])) |
                                    set(supported_formats.get('videos', [])) |
                                    set(supported_formats.get('gifs', [])))

            for file_path in backgrounds_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    self.current_background_path = str(file_path)
                    self.create_display_generator()
                    return

            self.preview_label.setText("No background files\nfound")
        except Exception as e:
            self.preview_label.setText(f"Error loading\nbackground: {e}")

    def determine_background_type(self, file_path):
        """Determine BackgroundType from file extension"""
        if not file_path:
            return BackgroundType.IMAGE

        if Path(file_path).is_dir():
            return BackgroundType.IMAGE_COLLECTION

        extension = Path(file_path).suffix.lower()
        supported_formats = self.config.get('supported_formats', {})

        if extension in supported_formats.get('videos', []):
            return BackgroundType.VIDEO
        elif extension in supported_formats.get('gifs', []):
            return BackgroundType.GIF
        return BackgroundType.IMAGE

    def create_display_generator(self):
        """Create or recreate DisplayGenerator with current settings"""
        if not self.current_background_path:
            return

        # Stop any existing loader
        if self.generator_loader and self.generator_loader.isRunning():
            self.generator_loader.wait(1000)
            self.generator_loader = None

        try:
            background_type = self.determine_background_type(self.current_background_path)
            
            display_config = DisplayConfig(
                background_path=self.current_background_path,
                background_type=background_type,
                output_width=self.preview_width,
                output_height=self.preview_height,
                global_font_path=self.text_style.font_family,
                foreground_image_path=self.current_foreground_path,
                foreground_position=(0, 0),
                foreground_alpha=self.foreground_opacity
            )

            # Check if it's a video - if so, use fast preview player
            if background_type == BackgroundType.VIDEO:
                # Stop any existing video player
                if self.video_player:
                    self.video_player.cleanup()
                    self.video_player = None
                
                # Stop display generator mode
                if self.display_generator:
                    self.display_generator.cleanup()
                    self.display_generator = None
                self.preview_timer.stop()
                
                # Show loading briefly
                self.preview_label.setText("⏳\nLoading video preview...")
                if self.progress_bar:
                    self.progress_bar.setValue(0)
                    self.progress_bar.setVisible(True)
                
                # Create fast video preview player
                self.video_player = VideoPreviewPlayer(
                    self.current_background_path,
                    self.preview_width,
                    self.preview_height,
                    foreground_path=self.current_foreground_path,
                    foreground_opacity=self.foreground_opacity
                )
                
                # Connect signals
                self.video_player.first_frame_ready.connect(self.on_video_first_frame)
                self.video_player.frame_ready.connect(self.on_video_frame)
                self.video_player.error_occurred.connect(self.on_video_error)
                
                # Initialize and play
                if self.video_player.initialize():
                    self.video_player.play()
                    if self.progress_bar:
                        self.progress_bar.setVisible(False)
                
            else:
                # For images/gifs, load synchronously (fast enough)
                # Stop and cleanup video player if it was running
                if self.video_player:
                    self.video_player.cleanup()
                    self.video_player = None
                
                # Clean up existing generator
                if self.display_generator:
                    self.display_generator.cleanup()
                    
                self.display_generator = DisplayGenerator(display_config)
                self.update_preview_frame()
                
        except Exception as e:
            self.preview_label.setText(f"Error creating\nDisplayGenerator:\n{str(e)}")

    def update_preview_frame(self):
        """Update preview with next frame from DisplayGenerator"""
        if not self.display_generator:
            return

        try:
            pil_image, duration = self.display_generator.get_frame_with_duration()
            qpixmap = self.pil_image_to_qpixmap(pil_image)

            if qpixmap and not qpixmap.isNull():
                self.preview_label.setPixmap(qpixmap)
            else:
                self.preview_label.setText("Error converting\nimage")
            next_update_ms = max(int(duration * 1000), 33)
            self.preview_timer.setSingleShot(True)
            self.preview_timer.start(next_update_ms)
        except Exception as e:
            self.preview_label.setText(f"Error updating\npreview:\n{str(e)}")

    def pil_image_to_qpixmap(self, pil_image):
        """Convert PIL Image to QPixmap"""
        try:
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            width, height = pil_image.size
            image_data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(image_data, width, height, QImage.Format_RGB888)
            return QPixmap.fromImage(qimage)
        except Exception:
            return None

    def show_loading_indicator(self, message: str):
        """Show loading indicator in preview"""
        self.preview_label.setText(f"⏳\n{message}")
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                background-color: #f0f0f0;
            }
        """)
        if self.progress_bar:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)

    def on_generator_ready(self, display_generator):
        """Handle successful generator creation"""
        self.display_generator = display_generator
        self.preview_label.setStyleSheet("")  # Reset stylesheet
        if self.progress_bar:
            self.progress_bar.setVisible(False)
        self.update_preview_frame()

    def on_generator_failed(self, error_msg):
        """Handle generator creation failure"""
        self.preview_label.setText(f"Error creating\nDisplayGenerator:\n{error_msg}")
        self.preview_label.setStyleSheet("""
            QLabel {
                color: red;
                font-size: 11px;
            }
        """)
        if self.progress_bar:
            self.progress_bar.setVisible(False)

    def on_generator_progress(self, message):
        """Update loading progress message"""
        self.preview_label.setText(f"⏳\n{message}")

    def on_generator_progress_percentage(self, percentage):
        """Update progress bar percentage"""
        if self.progress_bar:
            self.progress_bar.setValue(percentage)

    def on_generator_loader_finished(self):
        """Cleanup when loader thread finishes"""
        if self.generator_loader:
            self.generator_loader.deleteLater()
            self.generator_loader = None

    def on_video_first_frame(self, pixmap):
        """Handle first frame from fast video player"""
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setStyleSheet("")  # Reset stylesheet
        if self.progress_bar:
            self.progress_bar.setVisible(False)
        # Ensure overlay widgets stay on top
        if self.overlay_raise_callback:
            self.overlay_raise_callback()

    def on_video_frame(self, pixmap):
        """Handle subsequent frames from fast video player"""
        self.preview_label.setPixmap(pixmap)
        # Ensure overlay widgets stay on top
        if self.overlay_raise_callback:
            self.overlay_raise_callback()

    def on_video_error(self, error_msg):
        """Handle video player error"""
        self.preview_label.setText(f"Video Error:\n{error_msg}")
        self.preview_label.setStyleSheet("""
            QLabel {
                color: red;
                font-size: 11px;
            }
        """)
        if self.progress_bar:
            self.progress_bar.setVisible(False)

    def set_background(self, file_path: str):
        """Set background media"""
        self.current_background_path = file_path
        self.create_display_generator()

    def set_foreground(self, file_path: str):
        """Set foreground media"""
        self.current_foreground_path = file_path
        self.create_display_generator()

    def set_foreground_opacity(self, opacity: float):
        """Set foreground opacity (0.0 to 1.0)"""
        self.foreground_opacity = opacity
        self.create_display_generator()

    def clear_background(self, backgrounds_dir: str):
        """Clear background media"""
        self.current_background_path = None
        self.initialize_default_background(backgrounds_dir)

    def clear_foreground(self):
        """Clear foreground media"""
        self.current_foreground_path = None
        self.create_display_generator()

    def clear_all(self, backgrounds_dir: str):
        """Clear all media"""
        self.current_foreground_path = None
        self.current_background_path = None
        self.initialize_default_background(backgrounds_dir)

    def cleanup(self):
        """Cleanup resources"""
        self.preview_timer.stop()
        
        # Stop and cleanup video player
        if self.video_player:
            self.video_player.cleanup()
            self.video_player = None
        
        # Stop and cleanup loader thread
        if self.generator_loader and self.generator_loader.isRunning():
            self.generator_loader.wait(1000)
            if self.generator_loader.isRunning():
                self.generator_loader.terminate()
            self.generator_loader = None
            
        if self.display_generator:
            self.display_generator.cleanup()
