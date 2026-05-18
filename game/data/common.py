import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass

# common variables used across files
@dataclass
class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    """
    player_count: int
    players: dict
    round: int = 0
    turn: int = 0
    active_player: int = 0

    def __hash__(self): # Used for converting into a dict when saving
        return hash((
            self.player_count, 
            self.players, 
            self.round, 
            self.turn, 
            self.active_player))

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
faction_play_order = ["Working Class", "Middle Class", "Capitalist Class", "State"]
faction_instantiate_order = ["Working Class", "Capitalist Class", "Middle Class", "State"]

# ----------- END ---------- #
logger.debug("Finished importing data.common")