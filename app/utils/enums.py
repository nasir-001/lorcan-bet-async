from enum import Enum

class ActionStatus(str, Enum):
    success = "success"
    failed = "failed"