class CsvExportError(RuntimeError):
    """Base exception for CSV export failures."""

class CsvExportValidationError(CsvExportError):
    """Raised when a CSV export package is invalid."""
