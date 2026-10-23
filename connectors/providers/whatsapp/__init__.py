"""
WhatsApp Provider Package
=========================
Multi-Device WhatsApp companion integration for BABY Assistant.
"""

from .connector import (
    WhatsAppConnector,
    WhatsAppError,
    WhatsAppNotConnectedError,
    WhatsAppLoggedOutError,
    WhatsAppUnregisteredRecipientError,
    WhatsAppConnectionTimeoutError
)
from .contacts import ContactAliasManager

__all__ = [
    "WhatsAppConnector",
    "ContactAliasManager",
    "WhatsAppError",
    "WhatsAppNotConnectedError",
    "WhatsAppLoggedOutError",
    "WhatsAppUnregisteredRecipientError",
    "WhatsAppConnectionTimeoutError"
]
