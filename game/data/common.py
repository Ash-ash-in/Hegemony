import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass, field

# common variables used across files
@dataclass
class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    """
    ### Attributes ###
    player_count: int
    round: int = 0
    phase: str = 'Preparation'
    turn: int = 0
    active_player: int = 0
    players: dict = field(default_factory=dict) # players must be the last arg, since it is appended to the dict in load_save

    ### Methods ###
    def to_dict(self) -> dict: # For saving
        return {k.lstrip('_'): v for k, v in vars(self).items()}

    
@dataclass
class PlayerReference:
    active_factions: list
    existing_factions: list
    working_class: object
    middle_class: object | None
    capitalists: object
    state: object

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
faction_play_order = ["Working Class", "Middle Class", "Capitalists", "State"]
faction_instantiate_order = ["Working Class", "Capitalists", "Middle Class", "State"]
phases = ['Preparation','Action','Production','Elections','Scoring']
# ----------- END ---------- #
logger.debug("Finished importing data.common")