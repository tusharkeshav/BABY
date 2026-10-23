"""
Native Google Calendar Provider (Direct Google Cloud OAuth)
============================================================
Implements BaseCalendarConnector using Google's official API client libraries
(google-api-python-client, google-auth-oauthlib).

Ready for Stage 2 migration: allows running with your own Google Cloud OAuth app
without any third-party intermediaries.
"""

import os
import sys
import threading
from datetime import datetime, date, timedelta, timezone
from typing import Tuple, List, Dict, Any, Optional

from logs.Logging import log
from ...base import BaseCalendarConnector
from ...models import CalendarEvent

# Directory locations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
TOKEN_FILE = os.path.join(CREDENTIALS_DIR, "google_token.json")
CLIENT_SECRET_FILE = os.path.join(CREDENTIALS_DIR, "google_client_secret.json")

# Google Calendar Read/Write Scope
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class GoogleNativeCalendarConnector(BaseCalendarConnector):
    """
    Direct Google Calendar connector using Google's official OAuth 2.0 PKCE flow.
    Enables seamless transition to your own Google Cloud Project.
    """

    def __init__(self):
        self._service = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar (Native)"

    def is_connected(self) -> bool:
        """
        Checks if a valid, refreshed google_token.json exists locally.
        """
        if not os.path.exists(TOKEN_FILE):
            return False

        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            return creds and (creds.valid or creds.refresh_token is not None)
        except Exception as e:
            log.debug(f"GoogleNativeCalendarConnector.is_connected error: {e}")
            return False

    def _get_service(self):
        """
        Loads Google Calendar service with automatic token refresh.
        """
        with self._lock:
            if self._service is not None:
                return self._service

            if not os.path.exists(TOKEN_FILE):
                return None

            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                from googleapiclient.discovery import build

                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                if not creds.valid:
                    if creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
                            token_out.write(creds.to_json())

                self._service = build("calendar", "v3", credentials=creds)
                return self._service
            except Exception as e:
                log.error(f"GoogleNativeCalendarConnector: Failed to build calendar service: {e}")
                return None

    def initiate_auth(self) -> Tuple[bool, str]:
        """
        Launches Google's native OAuth 2.0 PKCE loopback server in a dedicated popup window.
        Supports both credentials file and config.ini direct credentials.
        """
        from config.get_config import get_config
        cfg_client_id = get_config("google_native", "client_id", fallback="")
        cfg_client_secret = get_config("google_native", "client_secret", fallback="")

        has_file = os.path.exists(CLIENT_SECRET_FILE)
        has_config = bool(cfg_client_id and cfg_client_secret)

        if not has_file and not has_config:
            msg = (
                f"Missing Google credentials. Place 'google_client_secret.json' in '{CREDENTIALS_DIR}' "
                "or configure client_id and client_secret under [google_native] in config.ini."
            )
            log.warning(f"GoogleNativeCalendarConnector: {msg}")
            return False, msg

        def _auth_thread():
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                from ...utils.popup_auth import launch_auth_popup, run_oauth_callback_server, find_free_port

                port = find_free_port()
                redirect_uri = f"http://127.0.0.1:{port}/"

                if has_file:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CLIENT_SECRET_FILE,
                        SCOPES,
                        redirect_uri=redirect_uri
                    )
                else:
                    client_config = {
                        "installed": {
                            "client_id": cfg_client_id,
                            "client_secret": cfg_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [redirect_uri]
                        }
                    }
                    flow = InstalledAppFlow.from_client_config(
                        client_config,
                        SCOPES,
                        redirect_uri=redirect_uri
                    )

                auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")

                log.info(f"GoogleNativeCalendarConnector: Launching standalone popup to: {auth_url[:60]}...")
                launch_auth_popup(auth_url)

                code, error = run_oauth_callback_server(port=port, timeout_seconds=120)
                if not code:
                    log.warning(f"GoogleNativeCalendarConnector: Auth failed or timed out: {error}")
                    return

                flow.fetch_token(code=code)
                creds = flow.credentials

                os.makedirs(CREDENTIALS_DIR, exist_ok=True)
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())

                log.info("GoogleNativeCalendarConnector: Saved credentials to token.json")
                self._service = None

                # Speech & Chime feedback
                try:
                    from skills.reminder import play_chime
                    play_chime()
                except Exception:
                    pass

                try:
                    from speech.speech_engine import speak
                    speak("Google Calendar connected successfully through your native Google app!")
                except Exception:
                    pass

            except Exception as e:
                log.error(f"GoogleNativeCalendarConnector: Authorization failed: {e}")

        threading.Thread(target=_auth_thread, daemon=True).start()
        return True, "I have opened Google login in a popup window. Please approve access to connect."

    def disconnect(self) -> Tuple[bool, str]:
        """Removes local token file."""
        if os.path.exists(TOKEN_FILE):
            try:
                os.remove(TOKEN_FILE)
                self._service = None
                return True, "Disconnected Google Calendar account."
            except Exception as e:
                return False, f"Failed to remove token: {e}"
        return True, "No active connection found."

    def get_agenda(self, target_date: Optional[date] = None) -> Tuple[bool, str, List[CalendarEvent]]:
        """Queries Google Calendar API for events on target_date."""
        service = self._get_service()
        if not service:
            return False, "Google Calendar is not connected yet. Say 'connect google calendar' first.", []

        if target_date is None:
            target_date = date.today()

        try:
            dt_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            dt_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

            events_result = service.events().list(
                calendarId="primary",
                timeMin=dt_start.isoformat(),
                timeMax=dt_end.isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            items = events_result.get("items", [])
            events = self._parse_api_items(items)

            date_label = "today" if target_date == date.today() else target_date.strftime("%A, %B %d")

            if not events:
                return True, f"You don't have any meetings scheduled for {date_label}.", []

            parts = [f"{ev.title} at {ev.start_time.strftime('%I:%M %p').lstrip('0')}" for ev in events[:4]]
            if len(events) == 1:
                speech = f"You have one meeting {date_label}: {parts[0]}."
            else:
                joined = ", ".join(parts[:-1]) + f", and {parts[-1]}"
                speech = f"You have {len(events)} meetings {date_label}: {joined}."

            return True, speech, events

        except Exception as e:
            log.error(f"GoogleNativeCalendarConnector: Failed to get agenda: {e}")
            return False, "Could not fetch your Google Calendar agenda.", []

    def get_next_meeting(self) -> Tuple[bool, str, Optional[CalendarEvent]]:
        """Queries Google Calendar API for the next upcoming event."""
        service = self._get_service()
        if not service:
            return False, "Google Calendar is not connected yet.", None

        try:
            now = datetime.now(timezone.utc)
            future_limit = now + timedelta(hours=24)

            events_result = service.events().list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=future_limit.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=3
            ).execute()

            items = events_result.get("items", [])
            events = self._parse_api_items(items)

            if not events:
                return True, "You have no upcoming meetings in the next 24 hours.", None

            next_ev = events[0]
            mins = next_ev.minutes_until_start
            time_human = next_ev.start_time.strftime("%I:%M %p").lstrip("0")

            if mins <= 1:
                speech = f"Your next meeting, '{next_ev.title}', is starting right now at {time_human}."
            elif mins < 60:
                speech = f"Your next meeting is '{next_ev.title}' in {mins} minutes, at {time_human}."
            else:
                speech = f"Your next meeting is '{next_ev.title}' at {time_human}."

            return True, speech, next_ev

        except Exception as e:
            log.error(f"GoogleNativeCalendarConnector: Failed to get next meeting: {e}")
            return False, "Could not look up your next meeting.", None

    def create_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = 30,
        attendees: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Creates an event using Google Calendar API."""
        service = self._get_service()
        if not service:
            return False, "Google Calendar is not connected."

        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            body = {
                "summary": title,
                "start": {"dateTime": start_time.isoformat()},
                "end": {"dateTime": end_time.isoformat()},
            }
            if attendees:
                body["attendees"] = [{"email": a} for a in attendees]

            service.events().insert(calendarId="primary", body=body).execute()
            time_str = start_time.strftime("%I:%M %p").lstrip("0")
            day_str = start_time.strftime("%A, %B %d")
            return True, f"I have scheduled '{title}' for {time_str} on {day_str}."

        except Exception as e:
            return False, f"Failed to create event: {e}"

    def _parse_api_items(self, items: List[Dict[str, Any]]) -> List[CalendarEvent]:
        events = []
        for item in items:
            try:
                ev_id = item.get("id", "")
                title = item.get("summary", "Untitled Meeting")

                start_dict = item.get("start", {})
                start_raw = start_dict.get("dateTime") or start_dict.get("date")
                if not start_raw:
                    continue
                start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))

                end_dict = item.get("end", {})
                end_raw = end_dict.get("dateTime") or end_dict.get("date")
                end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else start_dt + timedelta(minutes=30)

                meet_url = item.get("hangoutLink")
                attendees = [a.get("displayName") or a.get("email") for a in item.get("attendees", []) if isinstance(a, dict)]

                events.append(CalendarEvent(
                    id=ev_id,
                    title=title,
                    start_time=start_dt,
                    end_time=end_dt,
                    meet_url=meet_url,
                    location=item.get("location"),
                    attendees=attendees,
                    description=item.get("description")
                ))
            except Exception as e:
                log.debug(f"GoogleNativeCalendarConnector: Parse error on event: {e}")

        return events
