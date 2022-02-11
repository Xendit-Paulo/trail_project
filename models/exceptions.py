class InvalidField(Exception):
    def __init__(self, field, code, message):
        self.field = field
        self.code = code
        self.message = message
