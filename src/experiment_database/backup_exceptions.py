class BackupError(RuntimeError):
    """Base exception for database backup operations."""


class BackupIntegrityError(BackupError):
    """Raised when a database fails an integrity check."""


class BackupNotFoundError(BackupError):
    """Raised when the requested backup does not exist."""


class RestoreError(BackupError):
    """Raised when a database restore operation fails."""
