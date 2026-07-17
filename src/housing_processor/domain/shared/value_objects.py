from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmailAddress:
    original: str
    normalized: str


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    original: str
    e164: str


@dataclass(frozen=True, slots=True)
class PersonName:
    first: str
    last: str
    normalized: str


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
