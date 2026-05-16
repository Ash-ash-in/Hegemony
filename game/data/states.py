import logging
logger = logging.getLogger(__name__)

class PlayerState:
    """
    PlayerState contains all the information unique to a player

    It is stored in the Gamestate
    """
    ### Setup ### 
    def __init__(self, faction, victory_points):
        self.faction = faction
        self.victory_points = victory_points

    ### Methods ###
    def add_victory_points(self, points):
        if points < 0 and self.victory_points < -1 * points:
            self.victory_points = 0
        else:
            self.victory_points += points
        return

class GameState:
    """
    GameState is the master storage location for all game information. 
    """
    player_count: int
    players: dict
    turn: int = 0
    round: int = 0
    active_player: int = 0



