import os
import zipfile
import subprocess
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTextBrowser, QDialog, QToolTip
)
from PyQt5.QtCore import QTimer, Qt, QEvent
from PyQt5.QtGui import QPalette, QColor, QTextCursor, QCursor
import sys

IMG_DIR = r"E:\python\images"
OUTPUT_DIR = r"E:\python\NaXinh"
ZIP_PATH = "sticker_pack.zip"
ROWS, COLS = 3, 3

class GuidePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hướng dẫn sử dụng")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #111; color: #0f0; font-family: Arial; font-size: 14px;")

        layout = QVBoxLayout()
        title = QLabel("📘 Cách sử dụng công cụ")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        instructions = [
            "▶️ Chạy công cụ: Tách ảnh và tạo ZIP.",
            "♻️ Chạy lại: Xóa kết quả cũ và thực hiện lại.",
            "📂 Mở ZIP: Mở file ZIP sau đếm ngược.",
            "🗑️ Xóa file: Xóa ảnh và ZIP.",
            "🔍 Click tên ảnh: Mở ảnh vừa tạo.",
            "ℹ️ Phiên bản: Kiểm tra cập nhật."
        ]

        for ins in instructions:
            label = QLabel(ins)
            label.setWordWrap(True)
            layout.addWidget(label)

        close_btn = QPushButton("✖ Đóng")
        close_btn.setStyleSheet("background-color: #333; color: lime;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.setLayout(layout)

class ImageTool(QWidget):
    def __init__(self):
        super().__init__()
        self.countdown = 3
        self.image_paths = []
        self.original_img = None
        self.cell_width = 0
        self.cell_height = 0
        self.current_row = 0
        self.hovered_widget = None
        self.du_visible = True

        self.init_ui()
        self.setup_timers()

    def init_ui(self):
        self.setWindowTitle("Công cụ tách ảnh và nén ZIP (PyQt5)")
        self.setGeometry(100, 100, 540, 550)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("black"))
        self.setPalette(palette)

        self.label = QLabel("<b style='color: lime; font-size: 16px;'>Công cụ tách ảnh 3x3 và tạo file ZIP</b>")
        self.label.setAlignment(Qt.AlignCenter)

        self.run_btn = QPushButton("Chạy công cụ")
        self.run_btn.clicked.connect(self.prepare_tool)

        self.again_btn = QPushButton("Chạy lại")
        self.again_btn.setEnabled(False)
        self.again_btn.clicked.connect(self.reset_ui)

        self.open_btn = QPushButton("Mở file ZIP sau 3 giây")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.start_countdown)

        self.delete_btn = QPushButton("🗑️ Xóa file đã tạo")
        self.delete_btn.clicked.connect(self.delete_files)

        self.help_btn = QPushButton("❓ Hướng dẫn sử dụng")
        self.help_btn.clicked.connect(self.show_full_help)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: lime")

        self.log = QTextBrowser()
        self.log.setOpenExternalLinks(False)
        self.log.setStyleSheet("background-color: black; color: lime; font-family: Consolas;")
        self.log.anchorClicked.connect(self.open_image)

        self.author_label = QLabel("App được tạo by <span style='color: lime;'>Du</span>")
        self.author_label.setStyleSheet("color: gray; font-size: 10px;")
        self.author_label.setTextFormat(Qt.RichText)

        self.version_label = QLabel("<a href='#' style='color: gray;'>Phiên bản: 1.0 beta</a>")
        self.version_label.setOpenExternalLinks(False)
        self.version_label.setTextFormat(Qt.RichText)
        self.version_label.linkActivated.connect(self.show_update_check)

        self.footer_layout = QHBoxLayout()
        self.footer_layout.addWidget(self.author_label, alignment=Qt.AlignLeft)
        self.footer_layout.addWidget(self.version_label, alignment=Qt.AlignRight)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.again_btn)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.help_btn)
        layout.addWidget(self.status)
        layout.addWidget(self.log)
        layout.addLayout(self.footer_layout)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)

    def setup_timers(self):
        self.du_timer = QTimer()
        self.du_timer.timeout.connect(self.toggle_du_visibility)
        self.du_timer.start(800)

    def toggle_du_visibility(self):
        color = "lime" if self.du_visible else "gray"
        self.author_label.setText(f"App được tạo by <span style='color: {color};'>Du</span>")
        self.du_visible = not self.du_visible

    CURRENT_VERSION = "1.0"

    def show_update_check(self):

        reply = QMessageBox.question(self, "Cập nhật", "Bạn có muốn kiểm tra cập nhật không?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
                    try:
            import urllib.request
            with urllib.request.urlopen("https://raw.githubusercontent.com/clonenvb/app/main/version.txt") as response:
                latest_version = response.read().decode().strip()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể kiểm tra cập nhật: {e}")
            return

        if latest_version > CURRENT_VERSION:
            reply = QMessageBox.question(
                self, "Có bản cập nhật mới!",
                f"Phiên bản mới {latest_version} đã có.\nBạn có muốn tải về không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                
import shutil
import tempfile
download_url = "https://raw.githubusercontent.com/clonenvb/app/main/split_and_zip_with_update.py"
try:
    temp_dir = tempfile.gettempdir()
    new_file = os.path.join(temp_dir, "split_and_zip_updated.py")
    urllib.request.urlretrieve(download_url, new_file)
    QMessageBox.information(self, "Đang khởi động lại...", "Ứng dụng sẽ khởi động lại bằng phiên bản mới.")
    subprocess.Popen(["python", new_file], shell=True)
    sys.exit()
except Exception as e:
    QMessageBox.warning(self, "Lỗi", f"Tải hoặc chạy phiên bản mới thất bại: {e}")

        else:
            QMessageBox.information(self, "Thông báo", "Bạn đang dùng phiên bản mới nhất.")

    def show_full_help(self):
        popup = GuidePopup(self)
        popup.exec_()

    def log_message(self, message):
        self.log.append(message)
        self.log.moveCursor(QTextCursor.End)

    def log_file_link(self, path):
        name = os.path.basename(path)
        self.log.append(f"<a href='{path}' style='color:cyan;' title='Xem trước'>{name}</a>")
        self.log.moveCursor(QTextCursor.End)

    def open_image(self, url):
        subprocess.Popen(['explorer', url.toLocalFile()], shell=True)

    def prepare_tool(self):
        self.status.setText("Đang xử lý...")
        self.log.clear()
        self.log_message("🔄 Bắt đầu xử lý ảnh...")

        if not os.path.isdir(IMG_DIR):
            QMessageBox.critical(self, "Lỗi", "Thư mục ảnh không tồn tại.")
            return

        img_files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not img_files:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy ảnh nào trong thư mục.")
            return

        img_path = os.path.join(IMG_DIR, img_files[0])
        self.original_img = Image.open(img_path)
        img_width, img_height = self.original_img.size
        self.cell_width = img_width // COLS
        self.cell_height = img_height // ROWS

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.image_paths = []
        self.current_row = 0

        self.log_message("✨ Đang cắt từng dòng ảnh...")
        QTimer.singleShot(300, self.process_next_row)

    def process_next_row(self):
        if self.current_row >= ROWS:
            self.finalize_zip()
            return

        for col in range(COLS):
            left = col * self.cell_width
            upper = self.current_row * self.cell_height
            right = left + self.cell_width
            lower = upper + self.cell_height
            cropped_img = self.original_img.crop((left, upper, right, lower))
            output_path = os.path.join(OUTPUT_DIR, f"sticker_{self.current_row}_{col}.png")
            cropped_img.save(output_path)
            self.image_paths.append(output_path)
            self.log_message("✅ Đã lưu: ")
            self.log_file_link(output_path)

        self.current_row += 1
        QTimer.singleShot(400, self.process_next_row)

    def finalize_zip(self):
        self.log_message("🗜️ Đang nén ảnh thành ZIP...")
        with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
            for image_path in self.image_paths:
                zipf.write(image_path, os.path.basename(image_path))
                self.log_message(f"➕ {os.path.basename(image_path)}")

        self.status.setText("✅ Hoàn tất! File ZIP đã được tạo.")
        self.again_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.run_btn.setEnabled(False)
        self.log_message("🎉 Tất cả đã xong!")

    def delete_files(self):
        deleted = 0
        for file in self.image_paths:
            if os.path.exists(file):
                os.remove(file)
                deleted += 1
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
            deleted += 1
        self.log_message(f"🗑️ Đã xóa {deleted} tệp đã tạo.")
        self.status.setText("Đã xóa tệp.")

    def reset_ui(self):
        self.status.setText("")
        self.countdown = 3
        self.run_btn.setEnabled(True)
        self.again_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.log.clear()

    def start_countdown(self):
        self.status.setText(f"Mở file trong {self.countdown} giây...")
        self.timer.start(1000)

    def update_countdown(self):
        self.countdown -= 1
        if self.countdown == 0:
            self.timer.stop()
            subprocess.Popen(['explorer', os.path.abspath(ZIP_PATH)], shell=True)
            self.status.setText("Hoàn tất!")
        else:
            self.status.setText(f"Mở file trong {self.countdown} giây...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageTool()
    window.show()
    sys.exit(app.exec_())
