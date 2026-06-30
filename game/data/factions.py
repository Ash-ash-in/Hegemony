import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

class Player():
    """
    Player contains all the information unique to a player

    It is stored in the Gamestate
    """
    from game.data.common import Company
    ### Init ### 
    def __init__(
            self,
            faction: str, 
            victory_points: int = 0, 
            money: int = 0, 
            loans: int = 0,
            company_hand: list = []
        ):
        self._faction = faction
        self._victory_points = victory_points
        self._money = money
        self._loans = loans
        self._company_hand = company_hand

    ### Attributes ###
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
    @property
    def company_hand(self) -> list:
        return self._company_hand

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

    def _add_company_card_to_hand(self, card: Company):
        logger.debug(f"{self._faction} drawing company cards")
        self._company_hand.append(card)
        logger.debug(f"{self._faction} companies: {len(self._company_hand)}")

    def _remove_company_card_from_hand(self, card: Company):
        logger.debug(f"{self.faction} removing a company card")
        self._company_hand.remove(card)
        logger.debug(f"{self._faction} companies in market: {len(self._company_hand)}")

class WorkingClass(Player):
    def __init__(
            self,
            faction: str, 
            victory_points: int = 0, 
            money: int = 0, 
            loans: int = 0,
            prosperity: int = 0,
            population_track: int = 0
        ):
        super().__init__(            
                faction, 
                victory_points, 
                money, 
                loans
            )
        self._population_track = population_track
        self._prosperity = prosperity
        self._population = self._update_population()
        
    ### Attributes ###

    @property
    def population(self) -> int:
        return self._population
    @property
    def population_track(self) -> int:
        return self._population_track
    @property
    def prosperity(self) -> int:
        return self._prosperity    


    ### Methods ###
        
    def _update_population(self):
        logger.debug("Called WorkingClass _update_population")
        if self._population_track < 30 and self._population_track > 9:
            population = self._population_track // 3
        elif self._population_track >= 30:
            population = 10
        else:
            population = 3
        return population
        
    def _add_prosperity(self):
        logger.debug("Called WorkingClass _add_prosperity")
        if self._prosperity == 10:
            return
        self._prosperity += 1
        return
        
    def _remove_prosperity(self):
        logger.debug("Called WorkingClass _remove_prosperity")
        if self._prosperity == 0:
            return
        self._prosperity -= 1
        return
    
    def _add_population(self):
        logger.debug("Called WorkingClass _add_population")
        self._population_track += 1
        self._update_population()
        return
    
    def _remove_population(self):
        logger.debug("Called WorkingClass _remove_population")
        if self._population_track == 0:
            raise Exception('Population already at 0')
        self._population_track -= 1
        self._update_population()
        return


class MiddleClass(Player):
    def __init__(
            self,
            faction: str, 
            victory_points: int = 0, 
            money: int = 0, 
            loans: int = 0,
            prosperity_track: int = 0, # The index of the tracker, rather than the actual value
            population_track: int = 0 # Number of workers
        ):
        super().__init__(            
                faction,
                victory_points, 
                money, 
                loans
            )
        self._population_track = population_track
        self._population = self._update_population()
        self._prosperity_track = prosperity_track
        self._prosperity = self._update_prosperity()

    ### Attributes ###

    @property
    def population(self) -> int:
        return self._population
    @property
    def population_track(self) -> int:
        return self._population_track
    @property
    def prosperity(self) -> int:
        return self._prosperity    

    ### Methods ###

    def _update_population(self):
        logger.debug("Called MiddleClass _update_population")
        if self._population_track < 30 and self._population_track > 9:
            population = self._population_track // 3
        elif self._population_track >= 30:
            population = 10
        else:
            population = 3
        return population
    
    def _add_population(self):
        logger.debug("Called MiddleClass _add_population")
        self._population_track += 1
        self._update_population()
        return
    
    def _remove_population(self):
        logger.debug("Called MiddleClass _remove_population")
        if self._population_track == 0:
            raise Exception('Population already at 0')
        self._population_track -= 1
        self._update_population()
        return
    
    def _update_prosperity(self):
        """Changes prosperity based on the tracker and returns the prosperity"""
        logger.debug("Called MiddleClass _update_prosperity")
        prosperity_tracker = [0,1,2,3,4,5,5,6,6,7,7]
        self._prosperity = prosperity_tracker[self._prosperity_track]
        return self._prosperity

    def _add_prosperity(self):
        logger.debug("Called MiddleClass _add_prosperity")
        if self._prosperity_track == 10:
            return
        self._prosperity_track += 1
        self._update_prosperity()
        return
        
    def _remove_prosperity(self):
        logger.debug("Called MiddleClass _remove_prosperity")
        if self._prosperity_track == 0:
            return
        self._prosperity_track -= 1
        self._update_prosperity()
        return
    

