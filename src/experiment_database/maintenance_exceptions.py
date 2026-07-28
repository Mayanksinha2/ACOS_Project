class DatabaseMaintenanceError(RuntimeError):
    pass

class DatabaseIntegrityError(DatabaseMaintenanceError):
    pass

class MaintenanceValidationError(DatabaseMaintenanceError):
    pass
