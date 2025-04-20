import os
import sys
import subprocess
import zipfile
import tempfile
import urllib.request
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTextBrowser, QDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPalette, QColor, QTextCursor

IMG_DIR = r"E:\python\images"
OUTPUT_DIR = r"E:\python\NaXinh"
ZIP_PATH = "sticker_pack.zip"
ROWS, COLS = 3, 3

CURRENT_VERSION = "1.0"

class GuidePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hướng dẫn sử dụng")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #111; color: #0f0; font-size: 14px;")
        layout = QVBoxLayout()
        title = QLabel("📘 Cách sử dụng công cụ")
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
            layout.addWidget(QLabel(ins))
        close_btn = QPushButton("✖ Đóng")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        self.setLayout(layout)

class ImageTool(QWidget):
    def __init__(self):
        super().__init__()
        self.countdown = 3
        self.image_paths = []
        self.init_ui()
        self.setup_timers()

    def init_ui(self):
        self.setWindowTitle("Tách ảnh & ZIP (PyQt5)")
        self.setGeometry(100, 100, 540, 500)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("black"))
        self.setPalette(palette)

        self.label = QLabel("<b style='color: lime;'>Tách ảnh 3x3 và tạo file ZIP</b>")
        self.label.setAlignment(Qt.AlignCenter)

        self.run_btn = QPushButton("Chạy công cụ")
        self.run_btn.clicked.connect(self.prepare_tool)

        self.again_btn = QPushButton("Chạy lại")
        self.again_btn.setEnabled(False)
        self.again_btn.clicked.connect(self.reset_ui)

        self.open_btn = QPushButton("Mở file ZIP sau 3 giây")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.start_countdown)

        self.delete_btn = QPushButton("🗑️ Xóa file")
        self.delete_btn.clicked.connect(self.delete_files)

        self.help_btn = QPushButton("❓ Hướng dẫn")
        self.help_btn.clicked.connect(self.show_full_help)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: lime")

        self.log = QTextBrowser()
        self.log.setOpenExternalLinks(False)
        self.log.setStyleSheet("background-color: black; color: lime; font-family: Consolas;")
        self.log.anchorClicked.connect(self.open_image)

        self.version_label = QLabel("<a href='#' style='color: gray;'>Phiên bản: 1.0 beta</a>")
        self.version_label.setOpenExternalLinks(False)
        self.version_label.setTextFormat(Qt.RichText)
        self.version_label.linkActivated.connect(self.show_update_check)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("App by Du", self))
        footer.addStretch()
        footer.addWidget(self.version_label)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.again_btn)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.help_btn)
        layout.addWidget(self.status)
        layout.addWidget(self.log)
        layout.addLayout(footer)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)

    def setup_timers(self):
        pass

    def show_update_check(self):
        try:
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
                try:
                    download_url = "https://raw.githubusercontent.com/clonenvb/app/main/split_and_zip_with_update.py"
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
        original_img = Image.open(img_path)
        width, height = original_img.size
        cell_width = width // COLS
        cell_height = height // ROWS

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.image_paths = []
        for row in range(ROWS):
            for col in range(COLS):
                left = col * cell_width
                top = row * cell_height
                right = left + cell_width
                bottom = top + cell_height
                cropped_img = original_img.crop((left, top, right, bottom))
                out_path = os.path.join(OUTPUT_DIR, f"sticker_{row}_{col}.png")
                cropped_img.save(out_path)
                self.image_paths.append(out_path)
                self.log_message(f"✅ Đã lưu: {out_path}")

        with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
            for path in self.image_paths:
                zipf.write(path, os.path.basename(path))
                self.log_message(f"🗜️ Đã thêm: {os.path.basename(path)}")

        self.status.setText("✅ Hoàn tất!")
        self.again_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.run_btn.setEnabled(False)

    def delete_files(self):
        for f in self.image_paths:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
        self.log_message("🗑️ Đã xóa các tệp đã tạo.")
        self.status.setText("Đã xóa.")

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
