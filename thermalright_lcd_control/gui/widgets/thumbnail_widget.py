# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""
Thumbnail widget for displaying media file previews
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize, QThread
from PySide6.QtGui import QPixmap, QMovie, QImage
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QProgressBar

from ...common.logging_config import get_gui_logger


class VideoThumbnailLoader(QThread):
    """Thread for loading video thumbnails asynchronously"""
    thumbnail_ready = Signal(QPixmap)
    thumbnail_failed = Signal(str)
    progress_updated = Signal(int)  # Progress percentage 0-100

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.logger = get_gui_logger()

    def run(self):
        """Load video thumbnail in background thread"""
        try:
            import cv2

            self.progress_updated.emit(10)  # Starting

            # Open video file
            cap = cv2.VideoCapture(self.file_path)
            self.progress_updated.emit(30)  # File opened

            if cap.isOpened():
                # Get total frame count
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.progress_updated.emit(50)  # Metadata read

                # Seek to 10% of video duration
                if frame_count > 10:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 10)

                self.progress_updated.emit(70)  # Seeking complete

                # Read frame
                ret, frame = cap.read()

                if ret:
                    self.progress_updated.emit(85)  # Frame read

                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert to QImage
                    height, width, channel = rgb_frame.shape
                    bytes_per_line = 3 * width
                    q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

                    self.progress_updated.emit(95)  # Image conversion complete

                    # Convert to QPixmap and scale
                    pixmap = QPixmap.fromImage(q_image)
                    scaled = pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    self.progress_updated.emit(100)  # Complete
                    self.thumbnail_ready.emit(scaled)
                else:
                    self.thumbnail_failed.emit("Could not read frame")

                cap.release()
            else:
                self.thumbnail_failed.emit("Could not open video file")

        except ImportError:
            self.thumbnail_failed.emit("OpenCV not available")
        except Exception as e:
            self.thumbnail_failed.emit(str(e))


class ThumbnailWidget(QWidget):
    """Custom widget to display a thumbnail with filename"""
    clicked = Signal(str)  # Signal emitted with file path

    def __init__(self, file_path, file_name):
        super().__init__()
        self.logger = get_gui_logger()
        self.file_path = file_path
        self.file_name = file_name
        self.media_player = None
        self.audio_output = None
        self.is_video = False
        self.video_loader = None  # Track loader thread

        self.setFixedSize(120, 100)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QWidget:hover {
                background-color: #f0f0f0;
                border: 2px solid #0078d4;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Container for thumbnail content
        self.content_container = QWidget()
        self.content_container.setFixedSize(110, 70)

        # Stack widget to switch between label and video
        self.content_stack = QStackedWidget(self.content_container)
        self.content_stack.setGeometry(0, 0, 110, 70)

        # Label for images and gifs
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(110, 70)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: #333;
            }
        """)

        # Video widget for videos
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(110, 70)
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)

        # Add to stack
        self.content_stack.addWidget(self.thumb_label)   # Index 0
        self.content_stack.addWidget(self.video_widget)  # Index 1
        self.content_stack.setCurrentIndex(0)  # Start with label

        # Progress bar for video loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(110, 8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        self.progress_bar.setVisible(False)  # Hidden by default

        # Label for filename
        self.name_label = QLabel(file_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                font-size: 10px;
                color: #FFFFFF;
            }
        """)

        layout.addWidget(self.content_container)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.name_label)

        # Generate thumbnail
        self.generate_thumbnail()

    def generate_thumbnail(self):
        """Generate thumbnail based on file type"""
        try:
            file_path = Path(self.file_path)
            extension = file_path.suffix.lower()

            if extension in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}:
                self.create_image_thumbnail()
            elif extension == '.gif':
                self.create_gif_thumbnail()
            elif extension in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.m4v', '.webm'}:
                self.create_video_thumbnail()
            else:
                self.content_stack.setCurrentIndex(0)
                self.thumb_label.setText("?")

        except Exception as e:
            self.content_stack.setCurrentIndex(0)
            self.thumb_label.setText("Error")
            self.logger.error(f"Thumbnail generation error for {self.file_path}: {e}")

    def create_image_thumbnail(self):
        """Create thumbnail for an image"""
        self.content_stack.setCurrentIndex(0)

        pixmap = QPixmap(self.file_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("Image\nUnavailable")

    def create_gif_thumbnail(self):
        """Create thumbnail for a GIF"""
        self.content_stack.setCurrentIndex(0)

        try:
            movie = QMovie(self.file_path)
            if movie.isValid():
                movie.setScaledSize(QSize(110, 70))
                self.thumb_label.setMovie(movie)
                movie.start()
            else:
                self.thumb_label.setText("GIF\nUnavailable")
        except Exception as e:
            self.thumb_label.setText("GIF\nError")
            self.logger.error(f"GIF thumbnail error: {e}")

    def create_video_thumbnail(self):
        """Create static thumbnail for a video using OpenCV asynchronously"""
        self.content_stack.setCurrentIndex(0)  # Use label

        # Show loading spinner and progress bar
        self.show_loading_spinner()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Create and start loader thread
        self.video_loader = VideoThumbnailLoader(self.file_path)
        self.video_loader.thumbnail_ready.connect(self.on_video_thumbnail_ready)
        self.video_loader.thumbnail_failed.connect(self.on_video_thumbnail_failed)
        self.video_loader.progress_updated.connect(self.on_progress_updated)
        self.video_loader.finished.connect(self.on_video_loader_finished)
        self.video_loader.start()

    def show_loading_spinner(self):
        """Show a loading indicator"""
        self.thumb_label.setText("⏳\nLoading...")
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: #666;
                font-size: 10px;
            }
        """)

    def on_video_thumbnail_ready(self, pixmap):
        """Handle successful video thumbnail load"""
        self.thumb_label.setPixmap(pixmap)
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: #333;
            }
        """)
        self.progress_bar.setVisible(False)

    def on_video_thumbnail_failed(self, error_msg):
        """Handle video thumbnail load failure"""
        self.logger.error(f"Video thumbnail error: {error_msg}")
        self.thumb_label.setText("📹\nVIDEO")
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: white;
                font-size: 14px;
            }
        """)
        self.progress_bar.setVisible(False)

    def on_progress_updated(self, progress):
        """Update progress bar value"""
        self.progress_bar.setValue(progress)

    def on_video_loader_finished(self):
        """Cleanup when loader thread finishes"""
        if self.video_loader:
            self.video_loader.deleteLater()
            self.video_loader = None

    def mousePressEvent(self, event):
        """Handle click on thumbnail"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)

    def cleanup_video(self):
        """Clean up video resources"""
        # Stop and cleanup loader thread
        if self.video_loader and self.video_loader.isRunning():
            self.video_loader.wait(1000)  # Wait up to 1 second
            if self.video_loader.isRunning():
                self.video_loader.terminate()
            self.video_loader = None
            
        if self.media_player:
            self.media_player.stop()
            if hasattr(self.media_player, 'mediaStatusChanged'):
                try:
                    self.media_player.mediaStatusChanged.disconnect()
                except:
                    pass
            self.media_player.setVideoOutput(None)
            self.media_player = None
        if self.audio_output:
            self.audio_output = None

    def __del__(self):
        """Cleanup when widget is destroyed"""
        self.cleanup_video()