from enum import Enum

class NotificationStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    FAILED = "FAILED"