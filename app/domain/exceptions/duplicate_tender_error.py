"""Custom exceptions for the application domain."""


class DuplicateTenderError(ValueError):
    """Raised when a Tender with the same expedient_id already exists."""
