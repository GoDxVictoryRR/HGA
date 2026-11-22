"""
hostelguard/exceptions.py
Project-specific exception classes.

All modules raise these instead of bare Exception so callers can catch
specific error kinds without catching everything.
"""


class HostelGuardError(Exception):
    """Base class for all HostelGuard exceptions."""


class AuthenticationError(HostelGuardError):
    """Raised when login or token verification fails."""


class AuthorizationError(HostelGuardError):
    """Raised when a principal attempts an action it is not permitted to do."""


class ReplayError(HostelGuardError):
    """Raised when a replayed or out-of-window message is detected."""


class TamperError(HostelGuardError):
    """Raised when a message MAC or signature does not verify."""


class RateLimitError(HostelGuardError):
    """Raised when a device or user exceeds its allowed message rate."""


class EncryptionError(HostelGuardError):
    """Raised when encryption or decryption fails."""


class RegistrationError(HostelGuardError):
    """Raised when a device or user registration fails."""


class NotImplementedYet(HostelGuardError):
    """Raised by stub implementations that have not been built yet."""
