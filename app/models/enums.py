from enum import Enum


class TrackStatus(str, Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    ERROR = "error"
