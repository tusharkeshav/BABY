"""
Meeting Alert Toast Card (PyQt5)
================================
Kawaii dark-glass desktop notification card displaying upcoming calendar meetings
with an interactive one-click 'Join Google Meet' button.
"""

import os
import sys
import webbrowser
from typing import Optional

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QPixmap, QGuiApplication
from PyQt5.QtWidgets import QWidget, QApplication

from logs.Logging import log
from ..models import CalendarEvent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASCOT_PATH = os.path.join(BASE_DIR, "img", "mascot", "listening.png")

_active_meeting_cards = []


class MeetingToastWidget(QWidget):
    """
    Floating desktop meeting reminder card.
    Features:
    - Translucent dark glass backdrop with glowing border.
    - Mascot avatar thumbnail.
    - Meeting title, time range, and countdown badge.
    - Interactive 'Join Meet' and 'Dismiss' buttons.
    """

    def __init__(self, event: CalendarEvent):
        super().__init__()
        self.event = event

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(380, 150)

        # Position at top-right of primary screen
        screen = QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.right() - 400, geom.top() + 45)

        # Load avatar
        self.avatar_pix = None
        if os.path.exists(MASCOT_PATH):
            orig = QPixmap(MASCOT_PATH)
            self.avatar_pix = orig.scaled(70, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Auto-dismiss after 90 seconds if not interacted with
        self.auto_timer = QTimer(self)
        self.auto_timer.setSingleShot(True)
        self.auto_timer.timeout.connect(self.close)
        self.auto_timer.start(90000)

        # Button bounds
        has_meet = bool(self.event.meet_url)
        if has_meet:
            self.btn_join_rect = QRectF(105, 106, 135, 32)
            self.btn_dismiss_rect = QRectF(250, 106, 105, 32)
        else:
            self.btn_join_rect = None
            self.btn_dismiss_rect = QRectF(250, 106, 105, 32)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            pos = e.pos()
            if self.btn_join_rect and self.btn_join_rect.contains(pos):
                if self.event.meet_url:
                    log.info(f"Opening Google Meet URL: {self.event.meet_url}")
                    webbrowser.open(self.event.meet_url)
                self.close()
                e.accept()
                return
            elif self.btn_dismiss_rect and self.btn_dismiss_rect.contains(pos):
                self.close()
                e.accept()
                return
        super().mousePressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # 1. Dark Glass rounded background
        card_path = QPainterPath()
        card_path.addRoundedRect(QRectF(4, 4, w - 8, h - 8), 16, 16)
        p.setBrush(QBrush(QColor(22, 20, 32, 240)))
        p.setPen(QPen(QColor(168, 85, 247, 220), 1.8))
        p.drawPath(card_path)

        # 2. Avatar
        if self.avatar_pix:
            p.drawPixmap(16, 28, self.avatar_pix)

        # 3. Header badge
        mins = self.event.minutes_until_start
        if mins <= 0:
            badge_text = "🔴 HAPPENING NOW"
            badge_color = QColor(239, 68, 68)
        elif mins <= 10:
            badge_text = f"⏰ IN {mins} MINUTES"
            badge_color = QColor(245, 158, 11)
        else:
            badge_text = "📅 UPCOMING MEETING"
            badge_color = QColor(192, 132, 252)

        p.setPen(QPen(badge_color))
        p.setFont(QFont("SansSerif", 9, QFont.Bold))
        p.drawText(QRectF(105, 16, 250, 20), Qt.AlignLeft | Qt.AlignVCenter, badge_text)

        # 4. Title
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("SansSerif", 11, QFont.Bold))
        p.drawText(QRectF(105, 38, 255, 38), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.event.title)

        # 5. Time range
        p.setPen(QColor(209, 213, 219))
        p.setFont(QFont("SansSerif", 9))
        p.drawText(QRectF(105, 76, 255, 20), Qt.AlignLeft | Qt.AlignVCenter, self.event.format_time_range())

        # 6. Join Meet Button (Gradient Emerald Green)
        if self.btn_join_rect:
            btn_j_path = QPainterPath()
            btn_j_path.addRoundedRect(self.btn_join_rect, 8, 8)
            p.setBrush(QBrush(QColor(16, 185, 129, 220)))
            p.setPen(QPen(QColor(110, 231, 183), 1.0))
            p.drawPath(btn_j_path)
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("SansSerif", 9, QFont.Bold))
            p.drawText(self.btn_join_rect, Qt.AlignCenter, "🎥 Join Meet")

        # 7. Dismiss Button (Subtle Slate)
        if self.btn_dismiss_rect:
            btn_d_path = QPainterPath()
            btn_d_path.addRoundedRect(self.btn_dismiss_rect, 8, 8)
            p.setBrush(QBrush(QColor(75, 85, 99, 180)))
            p.setPen(QPen(QColor(156, 163, 175), 1.0))
            p.drawPath(btn_d_path)
            p.setPen(QColor(243, 244, 246))
            p.setFont(QFont("SansSerif", 9, QFont.Bold))
            p.drawText(self.btn_dismiss_rect, Qt.AlignCenter, "Dismiss")

        p.end()


def show_meeting_toast(event: CalendarEvent):
    """
    Safely shows the meeting card on the main Qt GUI thread.
    """
    app = QApplication.instance()
    if app is not None:
        def _render():
            try:
                card = MeetingToastWidget(event)
                _active_meeting_cards.append(card)
                card.show()
            except Exception as e:
                log.warning(f"Failed to display MeetingToastWidget: {e}")

        QTimer.singleShot(0, _render)
