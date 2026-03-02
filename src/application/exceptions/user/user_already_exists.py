from src.application.exceptions.domain_ex import DomainException

class UserAlreadyExistsException(DomainException):
    def __init__(self, message):
        super().__init__(message)