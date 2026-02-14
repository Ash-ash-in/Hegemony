import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass  

@dataclass(frozen = True)
class PlayerState:
    """
    PlayerState contains all the information unique to a player

    It is stored in the Gamestate
    """
    faction: str
    victory_points: int = 0

@dataclass(frozen = True)
class GameState:
    """
    GameState is the master storage location for all game information. 
    """
    player_count: int
    players: dict
    turn: int = 0
    round: int = 0
    active_player: int = 0



