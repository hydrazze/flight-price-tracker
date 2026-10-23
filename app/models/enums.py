from enum import Enum


class StopPreference(str, Enum):
    ANY = "any"
    DIRECT = "direct"
    WITH_STOPS = "with_stops"

    @property
    def label(self) -> str:
        return {
            self.ANY: "Без предпочтений",
            self.DIRECT: "Без пересадок",
            self.WITH_STOPS: "С пересадками",
        }[self]


class TrackStatus(str, Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    NOT_FOUND = "not_found"
    ERROR = "error"
    ARCHIVED = "archived"
