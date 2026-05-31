import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

class Player():
    """
    Player contains all the information unique to a player

    It is stored in the Gamestate
    """
    from game.agents import Agent
    ### Init ### 
    def __init__(
            self, 
            agent: tuple[str, Agent],
            faction: str, 
            victory_points: int = 0, 
            money: int = 0, 
            loans: int = 0
        ):
        self._agent = agent
        self._faction = faction
        self._victory_points = victory_points
        self._money = money
        self._loans = loans

    ### Attributes ###
    @property
    def agent(self) -> tuple:
        return self._agent
    @property
    def faction(self) -> str:
        return self._faction
    @property
    def victory_points(self) -> int:
        return self._victory_points
    @property
    def money(self) -> int:
        return self._money
    @property
    def loans(self) -> int:
        return self._loans

    ### Methods ###
    def to_dict(self) -> dict:
        return {k.lstrip('_'): v for k, v in vars(self).items()}

    def _add_victory_points(self, points):
        '''This will add or subtract points from the player.
        If subtracting more than they have, value is set to 0'''
        logger.debug(f"{self._faction} _add_victory_points({points})")
        if points < 0 and self._victory_points < -1 * points:
            self._victory_points = 0
        else:
            self._victory_points += points
        return

    def _add_money(self, amount):
        logger.debug(f"{self._faction} _add_money({amount})")
        self._money += amount
        logger.debug(f"{self._faction} money: {self._money}")
        
    def _take_loan(self):
        logger.debug(f"{self._faction} _take_loan()")
        self._loans += 1
        logger.debug(f"{self._faction} total loans: {self._loans}")

    def _remove_loan(self):
        logger.debug(f"{self._faction} _remove_loan()")
        self._loans -= 1
        logger.debug(f"{self._faction} total loans: {self._loans}")








