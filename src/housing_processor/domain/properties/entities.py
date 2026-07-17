from dataclasses import dataclass

from housing_processor.domain.shared.identifiers import PropertyId


@dataclass(slots=True)
class Property:
    id: PropertyId
    name: str
    normalized_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HousePreference:
    raw_property: str
    property_id: PropertyId | None
    rank: int | None
    confidence: float
