
from dataclasses import dataclass

@dataclass(frozen = True)
class Event:
    name: str
    description: str
    effect: dict[str, int]
    forfeit: str


@dataclass(frozen = True)
class Worker:
    faction: str
    skill: str
    alive: bool
    employed: bool