class HealthReportError(Exception):
    """Base exception for user-facing HealthReport failures."""


class AuthError(HealthReportError):
    """Raised when Strava authentication cannot be completed."""


class ConfigError(HealthReportError):
    """Raised when required local configuration is missing or invalid."""


class StorageError(HealthReportError):
    """Raised when local application storage cannot be read or written."""


class StravaAPIError(HealthReportError):
    """Raised when Strava API requests fail."""
