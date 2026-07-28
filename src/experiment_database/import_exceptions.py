class ExperimentImportError(RuntimeError):
    """Base exception for experiment import failures."""


class ImportPackageValidationError(ExperimentImportError):
    """Raised when an import package is invalid."""


class DuplicateExperimentError(ExperimentImportError):
    """Raised when duplicate handling rejects an import."""


class SchemaCompatibilityError(ExperimentImportError):
    """Raised when package data does not match the database schema."""
