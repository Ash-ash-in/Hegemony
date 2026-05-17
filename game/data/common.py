import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass

# common variables used across files
@dataclass
class GameState:
    """
    GameState is the master storage location for all game information. 
    """
    player_count: int
    players: dict
    turn: int = 0
    round: int = 0
    active_player: int = 0

@dataclass(frozen = True)
class Worker:
    faction: str
    skill: str
    alive: bool
    employed: bool

@dataclass(frozen=True)
class Card:
    faction: str
    description: str

@dataclass(frozen=True)
class Company:
    faction: str
    cost: int
    production: tuple[str,int]
    wages: tuple[tuple[int,bool]]

@dataclass(frozen = True)
class Event:
    name: str
    description: str
    effect: dict[str, int]
    forfeit: str

# ---------- References ----------- #
# Handy variables for building data in setup
faction_list = ["Working Class", "Middle Class", "Capitalist Class", "State"]


# ----------- END ---------- #
logger.debug("Finished importing data.common")