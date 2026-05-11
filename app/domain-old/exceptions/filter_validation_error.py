"""Custom exceptions for the application domain."""


class FilterValidationError(ValueError):
    """Raised when a FilterConfig is created with invalid parameter values."""
