class ExperimentExportError(RuntimeError):
    """Base exception for experiment export failures."""


class ExperimentNotFoundError(ExperimentExportError):
    """Raised when an experiment ID does not exist."""


class ExportValidationError(ExperimentExportError):
    """Raised when an export package is invalid."""
