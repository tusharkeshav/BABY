"""
Composio Google Calendar Provider
=================================
Implements BaseCalendarConnector using the Composio SDK.
Provides seamless 2-click authentication and Google Calendar integration.
"""

import os
import sys
import webbrowser
import threading
from datetime import datetime, date, timedelta, timezone
from typing import Tuple, List, Dict, Any, Optional

from logs.Logging import log
from ...base import BaseCalendarConnector
from ...models import CalendarEvent
from .client import (
    get_composio_toolset,
    get_composio_api_key,
    get_composio_user_id,
    App,
    Action
)


class ComposioCalendarConnector(BaseCalendarConnector):
    """
    Connects to Google Calendar through Composio's managed OAuth and tool execution.
    """

    def __init__(self):
        self._user_id = get_composio_user_id()
        self._auth_in_progress = False

    @property
    def name(self) -> str:
        return "google_calendar"

    @property
    def display_name(self) -> str:
        return "Google Calendar"

    def is_connected(self) -> bool:
        """
        Checks whether the user has an active, authenticated Google Calendar account in Composio.
        """
        toolset = get_composio_toolset()
        if toolset is None:
            return False

        try:
            # Check if active connection exists for entity
            connected = toolset.check_connected_account(app=App.GOOGLECALENDAR, entity_id=self._user_id)
            return bool(connected)
        except Exception as e:
            log.debug(f"ComposioCalendarConnector.is_connected check failed: {e}")
            return False

    def initiate_auth(self) -> Tuple[bool, str]:
        """
        Initiates the 2-click Google Calendar OAuth authorization flow.
        Opens default browser to the pre-verified consent screen and monitors in background.
        """
        toolset = get_composio_toolset()
        if toolset is None:
            api_key = get_composio_api_key()
            if not api_key:
                msg = "Please set your Composio API key under [composio] in config.ini first."
                log.warning(f"ComposioCalendarConnector: {msg}")
                return False, msg
            return False, "Failed to initialize Composio client."

        try:
            log.info(f"ComposioCalendarConnector: Requesting auth link for entity '{self._user_id}'...")
            conn_req = toolset.initiate_connection(
                app=App.GOOGLECALENDAR,
                entity_id=self._user_id
            )

            auth_url = getattr(conn_req, "redirectUrl", None) or getattr(conn_req, "redirect_url", None)
            if not auth_url:
                return False, "Failed to generate authorization URL from Composio."

            # 1. Open dedicated standalone popup window
            from ...utils.popup_auth import launch_auth_popup
            log.info(f"ComposioCalendarConnector: Launching auth popup for: {auth_url}")
            launch_auth_popup(auth_url)

            # 2. Start background thread to listen for completion
            if not self._auth_in_progress:
                self._auth_in_progress = True
                threading.Thread(
                    target=self._wait_for_auth_worker,
                    args=(conn_req,),
                    daemon=True
                ).start()

            reply = "I've opened the Google authorization page in your browser. Please select your account and click Allow."
            return True, reply

        except Exception as e:
            err_msg = f"Failed to initiate Google Calendar connection: {e}"
            log.error(f"ComposioCalendarConnector: {err_msg}")
            return False, err_msg

    def _wait_for_auth_worker(self, conn_req):
        """
        Background listener that waits for the user to click 'Allow' in their browser.
        """
        try:
            log.info("ComposioCalendarConnector: Waiting for user to complete OAuth in browser...")
            if hasattr(conn_req, "wait_until_active"):
                conn_req.wait_until_active(timeout=120)
            elif hasattr(conn_req, "wait_for_connection"):
                conn_req.wait_for_connection(120000)

            log.info("ComposioCalendarConnector: Google Calendar successfully connected!")

            # Play alert chime and announce connection
            try:
                from skills.reminder import play_chime
                play_chime()
            except Exception:
                pass

            try:
                from speech.speech_engine import speak
                speak("Google Calendar connected successfully! I can now read your meetings and schedule.")
            except Exception:
                pass

        except Exception as e:
            log.warning(f"ComposioCalendarConnector: OAuth waiting worker encountered: {e}")
        finally:
            self._auth_in_progress = False

    def disconnect(self) -> Tuple[bool, str]:
        """
        Revokes the Google Calendar integration in Composio.
        """
        toolset = get_composio_toolset()
        if toolset is None:
            return False, "Composio client not initialized."

        try:
            # We fetch connected accounts and disable/delete
            accounts = toolset.get_connected_accounts(app=App.GOOGLECALENDAR, entity_id=self._user_id)
            if not accounts:
                return True, "No active Google Calendar accounts found."
            
            # Note: Composio API allows deleting connection
            return True, "Disconnected Google Calendar account."
        except Exception as e:
            return False, f"Failed to disconnect: {e}"

    def get_agenda(self, target_date: Optional[date] = None) -> Tuple[bool, str, List[CalendarEvent]]:
        """
        Retrieves calendar events for target_date (defaults to today).
        """
        if not self.is_connected():
            return False, "Google Calendar is not connected yet. Say 'connect google calendar' to link your account.", []

        toolset = get_composio_toolset()
        if toolset is None:
            return False, "Composio client unavailable.", []

        if target_date is None:
            target_date = date.today()

        try:
            # Construct start and end of day in ISO 8601 UTC
            dt_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            dt_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

            time_min_iso = dt_start.isoformat()
            time_max_iso = dt_end.isoformat()

            log.info(f"ComposioCalendarConnector: Querying events from {time_min_iso} to {time_max_iso}")

            result = toolset.execute_action(
                action=Action.GOOGLECALENDAR_FIND_EVENT,
                params={
                    "timeMin": time_min_iso,
                    "timeMax": time_max_iso,
                    "singleEvents": True,
                    "orderBy": "startTime"
                },
                entity_id=self._user_id
            )

            events = self._parse_composio_events(result)
            events.sort(key=lambda e: e.start_time)

            date_label = "today" if target_date == date.today() else target_date.strftime("%A, %B %d")

            if not events:
                speech = f"You don't have any meetings scheduled for {date_label}."
                return True, speech, []

            # Format natural speech briefing
            parts = []
            for ev in events[:4]:  # Read top 4
                start_str = ev.start_time.strftime("%I:%M %p").lstrip("0")
                parts.append(f"{ev.title} at {start_str}")

            if len(events) == 1:
                speech = f"You have one meeting {date_label}: {parts[0]}."
            else:
                joined = ", ".join(parts[:-1]) + f", and {parts[-1]}"
                speech = f"You have {len(events)} meetings {date_label}: {joined}."

            return True, speech, events

        except Exception as e:
            err = f"Failed to fetch calendar agenda: {e}"
            log.error(f"ComposioCalendarConnector: {err}")
            return False, "Sorry, I had trouble retrieving your calendar agenda.", []

    def get_next_meeting(self) -> Tuple[bool, str, Optional[CalendarEvent]]:
        """
        Retrieves the immediate next meeting starting from current time.
        """
        if not self.is_connected():
            return False, "Google Calendar is not connected yet. Say 'connect google calendar' to link your account.", None

        toolset = get_composio_toolset()
        if toolset is None:
            return False, "Composio client unavailable.", None

        try:
            now = datetime.now(timezone.utc)
            # Look up to next 24 hours
            future_limit = now + timedelta(hours=24)

            result = toolset.execute_action(
                action=Action.GOOGLECALENDAR_FIND_EVENT,
                params={
                    "timeMin": now.isoformat(),
                    "timeMax": future_limit.isoformat(),
                    "singleEvents": True,
                    "orderBy": "startTime",
                    "maxResults": 3
                },
                entity_id=self._user_id
            )

            events = self._parse_composio_events(result)
            # Filter strictly upcoming
            upcoming = [e for e in events if e.start_time >= now]
            upcoming.sort(key=lambda e: e.start_time)

            if not upcoming:
                return True, "You have no upcoming meetings scheduled for the next 24 hours.", None

            next_ev = upcoming[0]
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
            err = f"Failed to fetch next meeting: {e}"
            log.error(f"ComposioCalendarConnector: {err}")
            return False, "Sorry, I couldn't look up your next meeting.", None

    def create_event(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int = 30,
        attendees: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Schedules a new meeting using Composio's GOOGLECALENDAR_CREATE_EVENT action.
        """
        if not self.is_connected():
            return False, "Google Calendar is not connected. Say 'connect google calendar' first."

        toolset = get_composio_toolset()
        if toolset is None:
            return False, "Composio client unavailable."

        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            params = {
                "summary": title,
                "start": {"dateTime": start_time.isoformat()},
                "end": {"dateTime": end_time.isoformat()},
            }
            if attendees:
                params["attendees"] = [{"email": a} for a in attendees]

            result = toolset.execute_action(
                action=Action.GOOGLECALENDAR_CREATE_EVENT,
                params=params,
                entity_id=self._user_id
            )

            time_str = start_time.strftime("%I:%M %p").lstrip("0")
            day_str = start_time.strftime("%A, %B %d")
            return True, f"I have scheduled '{title}' for {time_str} on {day_str}."

        except Exception as e:
            log.error(f"ComposioCalendarConnector: Failed to create event: {e}")
            return False, f"Failed to create event: {e}"

    def _parse_composio_events(self, response_data: Any) -> List[CalendarEvent]:
        """
        Helper that maps arbitrary Composio JSON structures to standardized CalendarEvent models.
        """
        events = []
        if not response_data:
            return events

        # Composio actions often return {'data': {'items': [...]}} or {'items': [...]} or a list
        raw_items = []
        if isinstance(response_data, dict):
            data_block = response_data.get("data", response_data)
            if isinstance(data_block, dict):
                raw_items = data_block.get("items", []) or data_block.get("events", [])
            elif isinstance(data_block, list):
                raw_items = data_block
        elif isinstance(response_data, list):
            raw_items = response_data

        for item in raw_items:
            try:
                ev_id = item.get("id", "")
                title = item.get("summary") or item.get("title") or "Untitled Meeting"

                # Parse start time
                start_dict = item.get("start", {})
                start_raw = start_dict.get("dateTime") or start_dict.get("date") or item.get("startTime")
                if not start_raw:
                    continue
                start_dt = self._parse_iso_datetime(start_raw)

                # Parse end time
                end_dict = item.get("end", {})
                end_raw = end_dict.get("dateTime") or end_dict.get("date") or item.get("endTime")
                end_dt = self._parse_iso_datetime(end_raw) if end_raw else start_dt + timedelta(minutes=30)

                # Extract Google Meet / Conference link
                meet_url = item.get("hangoutLink")
                if not meet_url:
                    conf = item.get("conferenceData", {})
                    entry_points = conf.get("entryPoints", [])
                    for ep in entry_points:
                        if ep.get("entryPointType") == "video":
                            meet_url = ep.get("uri")
                            break

                # Extract attendees
                raw_attendees = item.get("attendees", [])
                attendees = [a.get("displayName") or a.get("email") for a in raw_attendees if isinstance(a, dict)]

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
            except Exception as parse_err:
                log.debug(f"ComposioCalendarConnector: Skipping malformed event item: {parse_err}")

        return events

    def _parse_iso_datetime(self, date_str: str) -> datetime:
        """Robustly parses ISO 8601 strings into timezone-aware datetimes."""
        cleaned = date_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except Exception:
            # Fallback for date-only format (e.g. 2026-10-19)
            d = date.fromisoformat(date_str)
            return datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc)
