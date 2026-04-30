"""Custom exceptions for the application domain."""


class ExpiredTenderError(ValueError):
    """Raised when a Tender has an expired or invalid publication date."""
