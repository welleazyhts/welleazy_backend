"""
Custom exceptions for healthcare service providers.
"""


class ProviderException(Exception):
    """Base exception for all provider-related errors."""

    def __init__(self, message: str, provider: str = None, details: dict = None):
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        return {
            'error': self.message,
            'provider': self.provider,
            'details': self.details,
        }


class ProviderAuthenticationError(ProviderException):
    """Raised when authentication with provider fails."""
    pass


class ProviderAPIError(ProviderException):
    """Raised when provider API returns an error."""

    def __init__(self, message: str, provider: str = None,
                 status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message, provider, {'status_code': status_code})


class ProviderNotFoundError(ProviderException):
    """Raised when requested provider is not found or not configured."""
    pass


class ProviderNotConfiguredError(ProviderException):
    """Raised when provider credentials are not configured."""
    pass


class SlotNotAvailableError(ProviderException):
    """Raised when requested slot is not available."""
    pass


class BookingFailedError(ProviderException):
    """Raised when booking operation fails."""

    def __init__(self, message: str, provider: str = None,
                 booking_id: str = None, reason: str = None):
        self.booking_id = booking_id
        self.reason = reason
        super().__init__(message, provider, {'booking_id': booking_id, 'reason': reason})


class CancellationFailedError(ProviderException):
    """Raised when cancellation operation fails."""
    pass


class RescheduleFailedError(ProviderException):
    """Raised when reschedule operation fails."""
    pass
