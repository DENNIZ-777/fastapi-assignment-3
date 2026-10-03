from src.common import CustomException

class InvalidPasswordException(CustomException):
    def __init__(self):
        super().__init__(
            status_code=422,
            error_code="ERR_002",
            error_message="INVALID PASSWORD"
        )

class InvalidPhoneNumberException(CustomException):
    def __init__(self):
        super().__init__(422, "ERR_003", "INVALID PHONE NUMBER")

class BioTooLongException(CustomException):
    def __init__(self):
        super().__init__(422, "ERR_004", "BIO TOO LONG")

class EmailAlreadyExistsException(CustomException):
    def __init__(self):
        super().__init__(409, "ERR_005", "EMAIL ALREADY EXISTS")
