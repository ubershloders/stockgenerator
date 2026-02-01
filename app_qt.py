#!/usr/bin/env python3
"""
StockMaker GUI - PyQt drag and drop application for generating stock CSVs.
Requires: pip install PyQt6
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
from threading import Thread

from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QFrame,
    QPushButton,
    QGraphicsBlurEffect,
)

from main import (
    generate_image_description,
    generate_image_keywords,
    infer_shutterstock_categories,
)


class LogSignals(QObject):
    """Signals for thread-safe logging."""

    message = pyqtSignal(str)
    image_ready = pyqtSignal(str)  # Signal with image file path


class DropZone(QFrame):
    """Drag and drop zone for images."""

    def __init__(self, on_files_dropped=None):
        super().__init__()
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.is_dragging = False
        self.setMinimumHeight(80)
        self.files_dropped = False

        # Create layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(20, 15, 20, 15)

        # Icon/emoji
        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont("Arial", 32))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_label)

        # Main text
        self.main_text = QLabel("Drag images here")
        self.main_font = QFont("Arial", 16)
        self.main_font.setBold(True)
        self.main_text.setFont(self.main_font)
        self.main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_text.setStyleSheet("color: #ebdbb2;")
        self.layout.addWidget(self.main_text)

        # Subtitle
        self.subtitle = QLabel("JPG, PNG, GIF, BMP supported")
        self.sub_font = QFont("Arial", 9)
        self.sub_font.setItalic(True)
        self.subtitle.setFont(self.sub_font)
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("color: #928374;")
        self.layout.addWidget(self.subtitle)

        # File list (hidden initially)
        self.file_list = QTextEdit()
        self.file_list.setReadOnly(True)
        self.file_list.setFont(QFont("Monospace", 9))
        self.file_list.setVisible(False)
        self.file_list.setStyleSheet(
            """
            QTextEdit {
                background-color: transparent;
                color: #d5c4a1;
                border: none;
                padding: 10px;
            }
        """
        )
        self.layout.addWidget(self.file_list)

        self.layout.addStretch()

        self.setLayout(self.layout)
        self.update_style()

    def show_file_list(self, files):
        """Show the list of files in the drop zone."""
        self.files_dropped = True
        self.icon_label.setVisible(False)
        self.main_text.setVisible(False)
        self.subtitle.setVisible(False)

        file_text = "📋 Files in Queue:\n\n"
        for idx, file_path in enumerate(files, 1):
            file_text += f"{idx}. {Path(file_path).name}\n"

        self.file_list.setText(file_text)
        self.file_list.setVisible(True)

    def update_style(self):
        """Update the style based on dragging state."""
        if self.is_dragging:
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px dashed #458588;
                    border-radius: 12px;
                    background-color: #3c3836;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px dashed #458588;
                    border-radius: 12px;
                    background-color: #3c3836;
                }
            """
            )

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.is_dragging = True
            self.update_style()

    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self.is_dragging = False
        self.update_style()

    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        self.is_dragging = False
        self.update_style()

        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            files.append(file_path)

        if self.on_files_dropped:
            self.on_files_dropped(files)

        event.acceptProposedAction()


class StockMakerApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("StockMaker - Stock Image CSV Generator")
        self.setGeometry(100, 100, 1400, 900)
        self.is_processing = False
        self.current_progress = 0
        self.max_progress = 15000  # 150 seconds in 100ms increments

        # Create signal emitter
        self.log_signals = LogSignals()

        # Create central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #282828;")
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - Drop zone
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        # Title
        title = QLabel("StockTAGMaker by ubersholder")
        title_font = QFont("Arial", 28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #fda029;")
        left_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Generate CSV files for stock platforms")
        sub_font = QFont("Arial", 11)
        sub_font.setItalic(True)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet("color: #d5c4a1;")
        left_layout.addWidget(subtitle)

        # Drop zone
        self.drop_zone = DropZone(on_files_dropped=self.process_files)
        left_layout.addWidget(self.drop_zone, 1)

        # Thumbnail display
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setMinimumHeight(471)
        self.thumbnail_label.setMaximumHeight(471)
        self.thumbnail_label.setMinimumWidth(840)
        self.thumbnail_label.setMaximumWidth(840)
        self.thumbnail_label.setText("Waiting for images...")
        self.thumbnail_label.setFont(QFont("Arial", 10))
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet(
            """
            QLabel {
                background-color: #3c3836;
                border: 2px solid #458588;
                border-radius: 6px;
                color: #928374;
            }
        """
        )
        left_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Info text
        info = QLabel("💡 Tip: Supports multiple images at once")
        info_font = QFont("Arial", 10)
        info.setFont(info_font)
        info.setStyleSheet("color: #d5c4a1; padding: 10px; background-color: #3c3836; border-radius: 5px;")
        left_layout.addWidget(info)

        left_panel.setLayout(left_layout)
        left_panel.setStyleSheet("background-color: #3c3836;")

        # Right panel - Log
        right_panel = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        # Log title
        log_title = QLabel("Processing Log")
        log_font = QFont("Arial", 14)
        log_font.setBold(True)
        log_title.setFont(log_font)
        log_title.setStyleSheet("color: #fda029;")
        right_layout.addWidget(log_title)

        # Log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Monospace", 9))
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1d2021;
                color: #b8bb26;
                border: 2px solid #458588;
                border-radius: 6px;
                padding: 10px;
                selection-background-color: #458588;
            }
            QScrollBar:vertical {
                background-color: #3c3836;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #928374;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #458588;
            }
        """
        )
        right_layout.addWidget(self.log_text, 1)

        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.clear_log)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3c3836;
                color: #ebdbb2;
                border: 1px solid #928374;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #504945;
                border: 1px solid #458588;
            }
            QPushButton:pressed {
                background-color: #282828;
            }
        """
        )
        right_layout.addWidget(clear_btn)

        right_panel.setLayout(right_layout)
        right_panel.setStyleSheet("background-color: #282828;")

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3)

        central_widget.setLayout(main_layout)

        # Connect signal to slot
        self.log_signals.message.connect(self.log_message)
        self.log_signals.image_ready.connect(self.display_thumbnail)

        # Initial log message
        self.log("🚀 StockMaker started")
        self.log("Ready to process images...")
        self.log("")

    def process_files(self, files):
        """Process dropped files."""
        if self.is_processing:
            self.log("⏳ Already processing... please wait.")
            return

        # Filter valid image files
        image_files = []
        for file_path in files:
            path = Path(file_path)
            if path.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".bmp"):
                image_files.append(path)

        if not image_files:
            self.log("❌ No valid image files found.")
            return

        # Display file list in drop zone
        self.drop_zone.show_file_list([str(p) for p in image_files])

        self.log("")
        self.log(f"📸 Found {len(image_files)} image(s). Starting processing...")
        self.log("")

        # Process in background thread
        thread = Thread(target=self.process_images, args=(image_files,))
        thread.daemon = True
        thread.start()

    def process_images(self, image_files):
        """Process images and generate CSVs."""
        self.is_processing = True

        adobe_rows = []
        shutterstock_rows = []

        for idx, image_path in enumerate(image_files, 1):
            try:
                self.log_signals.message.emit(
                    f"[{idx}/{len(image_files)}] 🔄 Processing {image_path.name}..."
                )

                # Signal to display thumbnail
                self.log_signals.image_ready.emit(str(image_path))

                keywords_list = generate_image_keywords(str(image_path))
                description = generate_image_description(str(image_path))
                categories = infer_shutterstock_categories(keywords_list)

                keywords = ", ".join(keywords_list)

                adobe_rows.append(
                    {
                        "Filename": image_path.name,
                        "Title": description,
                        "Keywords": keywords,
                        "Category": "3",
                        "Releases": "Ivan Karpenko",
                    }
                )

                shutterstock_rows.append(
                    {
                        "Filename": image_path.name,
                        "Description": description,
                        "Keywords": keywords,
                        "Categories": categories,
                        "Editorial": "no",
                        "Mature content": "no",
                        "illustration": "no",
                    }
                )

                self.log_signals.message.emit(f"✅ {description}")
                self.log_signals.message.emit(f"   📌 Tags: {len(keywords_list)} keywords")
                self.log_signals.message.emit(f"   📂 Categories: {categories or 'None'}")
                self.log_signals.message.emit("")

            except Exception as e:
                self.log_signals.message.emit(f"❌ Error processing {image_path.name}:")
                self.log_signals.message.emit(f"   {str(e)}")
                self.log_signals.message.emit("")

        # Determine output directory
        output_dir = image_files[0].parent

        # Write CSVs
        try:
            adobe_csv_path = output_dir / "adobe_stock_upload.csv"
            with open(adobe_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["Filename", "Title", "Keywords", "Category", "Releases"],
                )
                writer.writeheader()
                writer.writerows(adobe_rows)

            shutterstock_csv_path = output_dir / "shutterstock_upload.csv"
            with open(shutterstock_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "Filename",
                        "Description",
                        "Keywords",
                        "Categories",
                        "Editorial",
                        "Mature content",
                        "illustration",
                    ],
                )
                writer.writeheader()
                writer.writerows(shutterstock_rows)

            self.log_signals.message.emit("=" * 60)
            self.log_signals.message.emit("✨ SUCCESS! CSV files generated")
            self.log_signals.message.emit("=" * 60)
            self.log_signals.message.emit(f"📄 Adobe: {adobe_csv_path.name}")
            self.log_signals.message.emit(f"📄 Shutterstock: {shutterstock_csv_path.name}")
            self.log_signals.message.emit(f"📁 Location: {output_dir}")
            self.log_signals.message.emit("")

        except Exception as e:
            self.log_signals.message.emit(f"❌ Error writing CSV files: {e}")
            self.log_signals.message.emit("")

        self.is_processing = False

    def log(self, message):
        """Append message to log from main thread."""
        current_text = self.log_text.toPlainText()
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}" if message and not message.startswith("=") else message
        new_text = (
            (current_text + formatted_msg + "\n")
            if current_text
            else (formatted_msg + "\n")
        )
        self.log_text.setText(new_text)
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def log_message(self, message):
        """Slot for receiving log messages from background thread."""
        self.log(message)

    def display_thumbnail(self, image_path):
        """Display thumbnail with blur-to-clear animation."""
        try:
            pixmap = QPixmap(image_path)

            # Scale to fit thumbnail size (840x471 at 16:9) while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(840, Qt.TransformationMode.SmoothTransformation)

            # If height is still larger than container, scale by height
            if scaled_pixmap.height() > 471:
                scaled_pixmap = pixmap.scaledToHeight(471, Qt.TransformationMode.SmoothTransformation)

            # Set the pixmap
            self.thumbnail_label.setPixmap(scaled_pixmap)

            # Create and apply blur effect
            blur_effect = QGraphicsBlurEffect()
            blur_effect.setBlurRadius(30)  # Start with heavy blur
            self.thumbnail_label.setGraphicsEffect(blur_effect)

            # Animate blur from 20 to 0 over 60 seconds
            self.blur_animation = QPropertyAnimation(blur_effect, b"blurRadius")
            self.blur_animation.setDuration(95000)  # 95 seconds in milliseconds
            self.blur_animation.setStartValue(30)
            self.blur_animation.setEndValue(0)
            self.blur_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.blur_animation.start()

        except Exception as e:
            self.thumbnail_label.setText(f"Error loading image")

    def clear_log(self):
        """Clear the log text."""
        self.log_text.clear()
        self.log("📝 Log cleared")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = StockMakerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
