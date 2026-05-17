# EXEPTIONS
class WorkerNotInPlayError(Exception):
    """Raised when a worker is not in play"""
    pass

class WorkerAlreadyEmployedError(Exception):
    """Raised when a worker is already employed"""
    pass

class WorkerNotEmployedError(Exception):
    """Raised when a worker is not employed"""
    pass

class WorkerNotInCompanyError(Exception):
    """Raised when a worker is not in the company"""
    pass

class WorkerSlotOccupiedError(Exception):
    """Raised when a worker slot is occupied"""
    pass

class WorkerSlotNotFoundError(Exception):
    """Raised when a worker slot is not found"""
    pass

class WorkerSlotNotAppropriateError(Exception):
    """Raised when a worker slot is not appropriate"""
    pass

class WorkerSlotAlreadyOccupiedError(Exception):
    """Raised when a worker slot is already occupied"""
    pass

class CompanyNotEstablishedError(Exception):
    """Raised when a company is not established"""
    pass

class CompanyAlreadyEstablishedError(Exception):
    """Raised when a company is already established"""
    pass

class CompanySlotOccupiedError(Exception):
    """Raised when a company slot is occupied"""
    pass

class CompanyNotFoundError(Exception):
    """Raised when a company is not found"""
    pass

class ClassMethodFailure(Exception):
    """Raised when a class method fails"""
    pass

class NotEnoughWorkersError(Exception):
    """Raised when there are not enough workers"""
    pass

class InputError(Exception):
    """Raised when there is an input error"""
    pass

class ValueError(Exception):
    """Raised when there is a value error"""
    pass