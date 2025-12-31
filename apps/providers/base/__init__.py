# Base provider interfaces
from .consultation import ConsultationProvider
from .diagnostics import DiagnosticsProvider
from .pharmacy import PharmacyProvider
from .exceptions import (
    ProviderException,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderNotFoundError,
    SlotNotAvailableError,
    BookingFailedError,
)

__all__ = [
    'ConsultationProvider',
    'DiagnosticsProvider',
    'PharmacyProvider',
    'ProviderException',
    'ProviderAuthenticationError',
    'ProviderAPIError',
    'ProviderNotFoundError',
    'SlotNotAvailableError',
    'BookingFailedError',
]
