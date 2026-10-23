"""
Base Connector Interfaces
=========================
Abstract interfaces defining standard contracts for all external service providers.
Enforces decoupling: business logic and UI code interact solely with these interfaces.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Tuple, List, Dict, Any, Optional

from .models import CalendarEvent, WhatsAppStatus


class BaseConnector(ABC):
    """
    Abstract base class for any external service connector.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Internal machine name of the connector (e.g. 'google_calendar')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """User-friendly name of the service (e.g. 'Google Calendar')."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Checks whether the connector currently has an active, valid authentication session.
        """
        pass

    @abstractmethod
    def initiate_auth(self) -> Tuple[bool, str]:
        """
        Starts the authentication flow for the user.
        
        Returns:
            Tuple[bool, str]: (Success boolean, Auth URL or status message).
        """
        pass

    @abstractmethod
    def disconnect(self) -> Tuple[bool, str]:
        """
        Revokes the current authentication session and clears stored tokens.
        """
        pass

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Optional: Returns function calling / tool definitions for LLM agents.
        """
        return []


class BaseCalendarConnector(BaseConnector):
    """
    Standard interface for all calendar providers (Composio, Google Native, CalDAV).
    """

    @abstractmethod
    def get_agenda(self, target_date: Optional[date] = None) -> Tuple[bool, str, List[CalendarEvent]]:
        """
        Retrieves scheduled events for a specific day (defaults to today).

        Args:
            target_date: The date to fetch events for (defaults to today).

        Returns:
            Tuple[bool, str, List[CalendarEvent]]:
                - Success flag.
                - Natural spoken summary for TTS.
                - List of CalendarEvent objects.
        """
        pass

    @abstractmethod
    def get_next_meeting(self) -> Tuple[bool, str, Optional[CalendarEvent]]:
        """
        Finds the immediate next upcoming meeting.

        Returns:
            Tuple[bool, str, Optional[CalendarEvent]]:
                - Success flag.
                - Natural spoken summary for TTS.
                - Next CalendarEvent (or None if no meetings left).
        """
        pass

    @abstractmethod
    def create_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = 30,
        attendees: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Schedules a new meeting or event on the user's primary calendar.

        Args:
            title: Title or subject of the meeting.
            start_time: When the event starts.
            duration_minutes: Duration in minutes.
            attendees: Optional list of email addresses.

        Returns:
            Tuple[bool, str]: (Success flag, Spoken confirmation message).
        """
        pass


class BaseMessagingConnector(BaseConnector):
    """
    Abstract interface for messaging platforms (WhatsApp, Telegram, SMS).
    """

    @abstractmethod
    def get_status(self) -> WhatsAppStatus:
        """Returns real-time connection telemetry and authentication state."""
        pass

    @abstractmethod
    def send_message(self, recipient: str, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Sends an outbound text message to a phone number, contact name, or self.

        Args:
            recipient: Phone number (E.164), JID, contact name, or 'me'.
            text: Message body to send.

        Returns:
            Tuple[bool, str, Optional[str]]:
                - Success flag.
                - Human-readable status/error description.
                - Message ID if successfully dispatched.
        """
        pass

