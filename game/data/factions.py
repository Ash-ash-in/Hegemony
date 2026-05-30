import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class Player:
    """
    Player contains all the information unique to a player

    It is stored in the Gamestate
    """
    ### Attributes ### 
    faction: str
    victory_points: int = 0
    money: int = 0
    loans: int = 0

    ### Methods ###
    def _add_victory_points(self, points):
        '''This will add or subtract points from the player.
        If subtracting more than they have, value is set to 0'''
        logger.debug(f"{self.faction} _add_victory_points({points})")
        if points < 0 and self.victory_points < -1 * points:
            self.victory_points = 0
        else:
            self.victory_points += points
        return

    def _add_money(self, amount):
        logger.debug(f"{self.faction} _add_money({amount})")
        self.money += amount
        logger.debug(f"{self.faction} money: {self.money}")
        
    def _take_loan(self):
        logger.debug(f"{self.faction} _take_loan()")
        self._add_money(50)
        self.loans += 1
        logger.debug(f"{self.faction} total loans: {self.loans}")







