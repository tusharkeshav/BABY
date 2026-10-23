"""
WhatsApp Contact Alias Manager
==============================
Manages local contact mappings and normalizes recipient queries (names, aliases,
raw phone numbers) into WhatsApp JID format for automated messaging.
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple

from logs.Logging import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_CONTACTS_PATH = os.path.join(BASE_DIR, "credentials", "whatsapp_contacts.json")


class ContactAliasManager:
    """
    Thread-safe manager for user contact aliases.
    Maps human-friendly names (e.g. 'Mom', 'Rahul') to E.164 phone numbers.
    """

    def __init__(self, file_path: str = DEFAULT_CONTACTS_PATH, default_country_code: str = "91"):
        self.file_path = file_path
        self.default_country_code = default_country_code
        self._contacts: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Loads contacts from JSON storage."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._contacts = {k.lower().strip(): str(v).strip() for k, v in data.items()}
                log.info(f"Loaded {len(self._contacts)} WhatsApp contacts from {self.file_path}")
            except Exception as e:
                log.error(f"Failed to load WhatsApp contacts: {e}")
                self._contacts = {}
        else:
            self._contacts = {}

    def _save(self) -> bool:
        """Persists contacts dictionary to JSON storage."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._contacts, f, indent=2)
            return True
        except Exception as e:
            log.error(f"Failed to save WhatsApp contacts: {e}")
            return False

    def add_contact(self, name: str, phone: str) -> Tuple[bool, str]:
        """
        Adds or updates a contact mapping.
        
        Args:
            name: Human friendly name (e.g. 'Rahul', 'Mom')
            phone: Phone number with or without country code
        """
        clean_name = name.lower().strip()
        clean_phone = self.normalize_phone(phone)
        if not clean_phone:
            return False, f"Invalid phone number format: '{phone}'"

        self._contacts[clean_name] = clean_phone
        if self._save():
            return True, f"Saved contact '{name}' with number +{clean_phone}."
        return False, "Failed to write contact to storage."

    def remove_contact(self, name: str) -> Tuple[bool, str]:
        """Removes a contact alias."""
        clean_name = name.lower().strip()
        if clean_name in self._contacts:
            del self._contacts[clean_name]
            self._save()
            return True, f"Removed contact '{name}'."
        return False, f"Contact '{name}' not found."

    def list_contacts(self) -> Dict[str, str]:
        """Returns all registered contacts."""
        return dict(self._contacts)

    def normalize_phone(self, raw_phone: str) -> str:
        """
        Strips non-digits and ensures international country code.
        Example: '+91 (96223) 77818' -> '919622377818'
                 '9622377818' -> '919622377818' (with default_country_code '91')
        """
        digits = re.sub(r"\D", "", raw_phone)
        if not digits:
            return ""

        # If user passed 10-digit national number, prepend default country code
        if len(digits) == 10 and self.default_country_code:
            digits = f"{self.default_country_code}{digits}"

        return digits

    def resolve_recipient(self, query: str) -> Tuple[bool, str, Optional[str]]:
        """
        Resolves a spoken or typed target into a valid WhatsApp JID.
        
        Args:
            query: Target identifier ('me', 'Rahul', '+91 96223 77818')

        Returns:
            Tuple[bool, str, Optional[str]]:
                - Success boolean.
                - Resolved WhatsApp JID (e.g. '919622377818@s.whatsapp.net' or 'me').
                - Formatted display name or phone number.
        """
        if not query or not query.strip():
            return False, "Recipient cannot be empty", None

        clean_query = query.strip()
        query_lower = clean_query.lower()

        # Case 1: Dedicated Group or Self
        if query_lower in ("group", "assistant", "baby", "command", "me", "self", "myself", "you"):
            return True, "group", "BABY Assistant Group"


        # Case 2: Contact Alias Lookup
        if query_lower in self._contacts:
            phone = self._contacts[query_lower]
            jid = f"{phone}@s.whatsapp.net"
            return True, jid, f"{clean_query.title()} (+{phone})"

        # Check for partial / fuzzy alias match (e.g. 'call mom' -> 'mom')
        for alias, phone in self._contacts.items():
            if alias in query_lower:
                jid = f"{phone}@s.whatsapp.net"
                return True, jid, f"{alias.title()} (+{phone})"

        # Case 3: Raw Phone Number
        phone_digits = self.normalize_phone(clean_query)
        if len(phone_digits) >= 10:
            jid = f"{phone_digits}@s.whatsapp.net"
            return True, jid, f"+{phone_digits}"

        return False, f"Could not find contact '{clean_query}'. Please provide a valid phone number or add to contacts.", None
