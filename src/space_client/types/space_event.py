from enum import Enum


class SpaceEvent(str, Enum):
    SYNCHRONIZED = "synchronized"
    PRICING_CREATED = "pricing_created"
    PRICING_ARCHIVED = "pricing_archived"
    PRICING_ACTIVED = "pricing_actived"
    SERVICE_DISABLED = "service_disabled"
    ERROR = "error"

    @classmethod
    def from_string(cls, text: str) -> "SpaceEvent | None":
        lowered = text.lower()
        for event in cls:
            if event.value == lowered:
                return event
        return None
