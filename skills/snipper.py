import os
import sys
import base64
import subprocess
from typing import Optional
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QGuiApplication
from PyQt5.QtCore import Qt, QRect, QBuffer, QIODevice

SHUTTER_SOUND = "/usr/share/sounds/freedesktop/stereo/camera-shutter.oga"


def play_shutter():
    """Plays an instant camera snapshot audio effect."""
    try:
        if os.path.exists(SHUTTER_SOUND):
            subprocess.Popen(['paplay', SHUTTER_SOUND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class SnipperOverlay(QWidget):
    """
    Transparent full-screen interactive overlay for selecting screen sub-regions.
    Features dark glass dimming, kawaii sakura-pink border, size badge, and top HUD pill.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setCursor(Qt.CrossCursor)

        screen = QGuiApplication.primaryScreen()
        if not screen:
            sys.exit(2)
        self.setGeometry(screen.geometry())
        self.pixmap = screen.grabWindow(0)

        self.origin = None
        self.current = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Base desktop screenshot
        painter.drawPixmap(0, 0, self.pixmap)

        # 2. Dim entire screen
        dim_color = QColor(12, 10, 18, 140)
        painter.fillRect(self.rect(), dim_color)

        # 3. Top instruction pill
        pill_w = 460
        pill_h = 36
        pill_x = (self.width() - pill_w) // 2
        pill_y = 24
        pill_rect = QRect(pill_x, pill_y, pill_w, pill_h)

        painter.setBrush(QBrush(QColor(28, 20, 32, 225)))
        painter.setPen(QPen(QColor("#ff8da1"), 1.5))
        painter.drawRoundedRect(pill_rect, 18, 18)

        painter.setFont(QFont("DejaVu Sans", 10, QFont.Bold))
        painter.setPen(QColor("#fff0f5"))
        painter.drawText(pill_rect, Qt.AlignCenter, "🍓 Drag area to inspect  •  Space for Full  •  Esc to cancel")

        # 4. Selection box & size tag
        if self.origin and self.current:
            r = QRect(self.origin, self.current).normalized()
            if r.width() > 1 and r.height() > 1:
                # Restore original un-dimmed pixels in the selected region
                painter.drawPixmap(r, self.pixmap, r)

                # Sakura-pink selection border
                pen = QPen(QColor("#ff69b4"), 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(r)

                # Size indicator badge
                size_str = f" {r.width()} × {r.height()} px "
                badge_w = 100
                badge_h = 22
                badge_x = min(r.right() - badge_w, self.width() - badge_w - 10)
                badge_y = r.bottom() + 6 if r.bottom() + 30 < self.height() else max(10, r.top() - 28)
                badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

                painter.setBrush(QBrush(QColor(20, 14, 24, 210)))
                painter.setPen(QPen(QColor("#ff69b4"), 1))
                painter.drawRoundedRect(badge_rect, 6, 6)

                painter.setFont(QFont("DejaVu Sans", 8, QFont.Bold))
                painter.setPen(QColor("#ffccd8"))
                painter.drawText(badge_rect, Qt.AlignCenter, size_str)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.current = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.origin:
            self.current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.origin:
            self.current = event.pos()
            r = QRect(self.origin, self.current).normalized()
            if r.width() >= 16 and r.height() >= 16:
                cropped = self.pixmap.copy(r)
                self.finish_with_pixmap(cropped)
            else:
                self.origin = None
                self.current = None
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            sys.exit(1)
        elif event.key() == Qt.Key_Space:
            self.finish_with_pixmap(self.pixmap)

    def finish_with_pixmap(self, pixmap):
        play_shutter()
        # Scale down if width exceeds 1280px to save transmission & memory
        if pixmap.width() > 1280:
            pixmap = pixmap.scaledToWidth(1280, Qt.SmoothTransformation)

        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "JPEG", 85)
        raw = buf.data().data()
        b64 = base64.b64encode(raw).decode("utf-8")
        print(f"B64_START:{b64}:B64_END", flush=True)
        QApplication.quit()


def snip_screen_base64(timeout: float = 30.0) -> Optional[str]:
    """
    Launches SnipperOverlay in an isolated subprocess to guarantee 100% thread safety
    across X11/Qt threads. Returns the base64 JPEG string or None if cancelled.
    """
    env = os.environ.copy()
    if "DISPLAY" not in env:
        env["DISPLAY"] = ":1"

    script_path = os.path.abspath(__file__)
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if proc.returncode == 0 and "B64_START:" in proc.stdout:
            b64 = proc.stdout.split("B64_START:")[1].split(":B64_END")[0].strip()
            return b64
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    snipper = SnipperOverlay()
    snipper.show()
    sys.exit(app.exec_())
