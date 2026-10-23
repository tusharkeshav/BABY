"""
Data Models for Connectors Framework
====================================
Standardized data structures shared across all connector providers.
Ensures provider interchangeability (e.g., Composio vs Google Native).
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional


@dataclass
class CalendarEvent:
    """
    Standardized calendar event representation across all providers.
    
    Attributes:
        id: Unique identifier of the event.
        title: Title / summary of the meeting.
        start_time: Starting datetime.
        end_time: Ending datetime.
        meet_url: Direct link to Google Meet, Zoom, or video conference.
        location: Physical location or room name.
        attendees: List of participant names or email addresses.
        description: Agenda or meeting notes.
    """
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    meet_url: Optional[str] = None
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    description: Optional[str] = None

    @property
    def is_today(self) -> bool:
        """Returns True if the event starts today."""
        return self.start_time.date() == date.today()

    @property
    def minutes_until_start(self) -> int:
        """Returns minutes remaining until the event starts (negative if past)."""
        delta = self.start_time - datetime.now(self.start_time.tzinfo)
        return int(delta.total_seconds() / 60)

    @property
    def duration_minutes(self) -> int:
        """Returns the event duration in minutes."""
        delta = self.end_time - self.start_time
        return max(0, int(delta.total_seconds() / 60))

    def format_time_range(self) -> str:
        """
        Formats human-friendly time range, e.g.:
        '02:30 PM – 03:00 PM'
        """
        fmt_start = self.start_time.strftime("%I:%M %p").lstrip("0")
        fmt_end = self.end_time.strftime("%I:%M %p").lstrip("0")
        return f"{fmt_start} – {fmt_end}"

    def format_speech_summary(self) -> str:
        """
        Formats a natural sentence suitable for text-to-speech output.
        E.g.: 'Design Review from 2:00 PM to 2:45 PM'
        """
        time_str = self.format_time_range()
        mins_left = self.minutes_until_start
        
        if 0 <= mins_left <= 60:
            return f"{self.title} in {mins_left} minutes, at {self.start_time.strftime('%I:%M %p').lstrip('0')}"
        return f"{self.title} at {self.start_time.strftime('%I:%M %p').lstrip('0')}"


@dataclass
class WhatsAppStatus:
    """
    Real-time telemetry and state of the WhatsApp Multi-Device session.
    """
    connected: bool
    state: str  # 'connected', 'qr_ready', 'disconnected', 'logged_out'
    phone: Optional[str] = None
    jid: Optional[str] = None
    qr: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_logged_out(self) -> bool:
        """True if the device was unlinked from the phone."""
        return self.state == "logged_out"

    @property
    def is_ready_for_scan(self) -> bool:
        """True if waiting for user to scan the QR code."""
        return self.state == "qr_ready" and self.qr is not None


@dataclass
class ContactEntry:
    """
    A recognized WhatsApp contact alias with normalized phone number.
    """
    name: str
    phone: str
    alias: Optional[str] = None

