"""
Connector Manager
=================
Central registry and factory for all external connectors.
Implements the Provider Pattern to allow swapping between Composio and Native Google OAuth
via a single config setting.
"""

import os
import sys
import time
import threading
from datetime import datetime, date, timedelta
from typing import Tuple, Dict, Any, Optional

from logs.Logging import log
from config.get_config import get_config
from .base import BaseCalendarConnector
from .models import CalendarEvent

_manager_instance: Optional["ConnectorManager"] = None
_lock = threading.Lock()


class ConnectorManager:
    """
    Manages active service connectors, intent dispatch, and background proactive alerts.
    """

    def __init__(self):
        self._calendar_connector: Optional[BaseCalendarConnector] = None
        self._whatsapp_connector = None
        self._alerted_event_ids = set()
        self._running = True

        # Initialize providers
        self._load_provider()
        self._load_whatsapp()

        # Start proactive background meeting watcher
        self._watcher_thread = threading.Thread(target=self._proactive_watcher_loop, daemon=True)
        self._watcher_thread.start()
        log.info("ConnectorManager: Initialized and background meeting watcher started.")

    def _load_whatsapp(self):
        """Initializes the WhatsApp Multi-Device connector."""
        try:
            from .providers.whatsapp import WhatsAppConnector
            self._whatsapp_connector = WhatsAppConnector()
            log.info("ConnectorManager: Loaded WhatsAppConnector.")
        except Exception as e:
            log.error(f"ConnectorManager: Failed to load WhatsAppConnector: {e}")


    def _load_provider(self):
        """
        Dynamically loads the configured calendar provider based on config.ini.
        Defaults to 'composio'.
        """
        raw_provider = get_config("connectors", "calendar_provider", fallback="composio")
        provider_name = (raw_provider or "composio").strip().lower()

        log.info(f"ConnectorManager: Loading calendar provider '{provider_name}'...")

        if provider_name == "google_native":
            try:
                from .providers.google_native.calendar import GoogleNativeCalendarConnector
                self._calendar_connector = GoogleNativeCalendarConnector()
                log.info("ConnectorManager: Loaded GoogleNativeCalendarConnector.")
            except Exception as e:
                log.error(f"ConnectorManager: Failed to load GoogleNativeCalendarConnector: {e}")
        else:
            # Default to Composio
            try:
                from .providers.composio.calendar import ComposioCalendarConnector
                self._calendar_connector = ComposioCalendarConnector()
                log.info("ConnectorManager: Loaded ComposioCalendarConnector.")
            except Exception as e:
                log.error(f"ConnectorManager: Failed to load ComposioCalendarConnector: {e}")

    @property
    def calendar(self) -> Optional[BaseCalendarConnector]:
        """Returns the currently active calendar connector."""
        return self._calendar_connector

    @property
    def whatsapp(self):
        """Returns the WhatsApp Multi-Device connector."""
        if not self._whatsapp_connector:
            self._load_whatsapp()
        return self._whatsapp_connector

    def handle_connect(self, service_name: str = "google_calendar") -> Tuple[bool, str]:
        """
        Top-level handler for voice commands like 'connect google calendar' or 'connect whatsapp'.
        """
        clean_name = service_name.lower().strip()
        if "whatsapp" in clean_name:
            if not self._whatsapp_connector:
                self._load_whatsapp()
            if not self._whatsapp_connector:
                return False, "WhatsApp connector is not available."
            return self._whatsapp_connector.initiate_auth()

        if "calendar" in clean_name or "google" in clean_name:
            if not self._calendar_connector:
                return False, "Calendar provider is not configured properly."
            return self._calendar_connector.initiate_auth()

        return False, f"Unknown service '{service_name}'. Currently supported: Google Calendar, WhatsApp."


    def handle_agenda(self, query_text: str = "") -> Tuple[bool, str]:
        """
        Top-level handler for queries like 'what is my schedule today'.
        """
        if not self._calendar_connector:
            return False, "Calendar connector is not initialized."

        target_date = date.today()
        if "tomorrow" in query_text.lower():
            target_date = date.today() + timedelta(days=1)

        ok, speech, events = self._calendar_connector.get_agenda(target_date)

        # If events found, display the first one on a desktop card
        if ok and events:
            try:
                from .ui.meeting_toast import show_meeting_toast
                show_meeting_toast(events[0])
            except Exception as e:
                log.debug(f"ConnectorManager: Could not show meeting toast: {e}")

        return ok, speech

    def handle_next_meeting(self) -> Tuple[bool, str]:
        """
        Top-level handler for queries like 'when is my next meeting'.
        """
        if not self._calendar_connector:
            return False, "Calendar connector is not initialized."

        ok, speech, next_ev = self._calendar_connector.get_next_meeting()

        if ok and next_ev:
            try:
                from .ui.meeting_toast import show_meeting_toast
                show_meeting_toast(next_ev)
            except Exception as e:
                log.debug(f"ConnectorManager: Could not show meeting toast: {e}")

        return ok, speech

    def _proactive_watcher_loop(self):
        """
        Background daemon that alerts the user 5 minutes before scheduled meetings.
        """
        while self._running:
            # Poll every 2 minutes
            time.sleep(120)

            if not self._calendar_connector or not self._calendar_connector.is_connected():
                continue

            try:
                ok, _, next_ev = self._calendar_connector.get_next_meeting()
                if ok and next_ev:
                    mins = next_ev.minutes_until_start
                    # Alert if meeting starts in 2 to 6 minutes and hasn't been alerted yet
                    if 1 <= mins <= 6 and next_ev.id not in self._alerted_event_ids:
                        self._alerted_event_ids.add(next_ev.id)
                        log.info(f"ConnectorManager: Proactively alerting user for meeting: '{next_ev.title}' in {mins}m")

                        # 1. Play chime
                        try:
                            from skills.reminder import play_chime
                            play_chime()
                        except Exception:
                            pass

                        # 2. Show desktop card with Join Meet button
                        try:
                            from .ui.meeting_toast import show_meeting_toast
                            show_meeting_toast(next_ev)
                        except Exception:
                            pass

                        # 3. Spoken alert
                        try:
                            from speech.speech_engine import speak
                            speak(f"Heads up! Your meeting, '{next_ev.title}', starts in {mins} minutes.")
                        except Exception:
                            pass

                        # 4. Proactive WhatsApp alert to phone
                        try:
                            if self._whatsapp_connector and self._whatsapp_connector.is_connected():
                                meet_info = f"\n🎥 *Meet:* {next_ev.meet_url}" if next_ev.meet_url else ""
                                alert_text = (
                                    f"⏰ *Meeting in {mins} minutes!*\n"
                                    f"📌 *{next_ev.title}*{meet_info}\n"
                                    f"🕒 {next_ev.format_time_range()}"
                                )
                                self._whatsapp_connector.send_message("me", alert_text)
                        except Exception as wa_err:
                            log.debug(f"Proactive WhatsApp alert failed: {wa_err}")

            except Exception as loop_err:
                log.debug(f"ConnectorManager watcher loop error: {loop_err}")


def get_connector_manager() -> ConnectorManager:
    """Returns the global thread-safe ConnectorManager singleton."""
    global _manager_instance
    with _lock:
        if _manager_instance is None:
            _manager_instance = ConnectorManager()
        return _manager_instance
