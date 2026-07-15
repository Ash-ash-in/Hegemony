import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field

class Player():
    """
    Player contains all the information unique to a player

    It is stored in the Gamestate
    """
    from game.data.classes import Company
    ### Init ### 
    def __init__(
            self,
            faction: str
        ):
        self._faction = faction
        self._victory_points = 0
        self._money = 0
        self._loans = 0
        self._resources = {
                "Food":0,
                "Healthcare":0,
                "Education":0,
                "Luxuries":0
                }
        self._influence = 0
        self._company_hand = []

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
    def food(self) -> int:
        return self._resources["Food"]
    @property
    def luxuries(self) -> int:
        return self._resources["Luxuries"]
    @property
    def healthcare(self) -> int:
        return self._resources["Healthcare"]
    @property
    def education(self) -> int:
        return self._resources["Education"]
    @property
    def resources(self) -> dict:
        return self._resources
    @property
    def influence(self) -> int:
        return self._influence
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
            faction: str = "Working Class"
        ):
        logger.debug("Creating Working Class")
        super().__init__(            
                faction
            )
        self._population_track = 0
        self._prosperity = 0
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


    ### Modification Methods ###
        
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
            faction: str = "Middle Class"
        ):
        logger.debug("Creating Middle Class")
        super().__init__(            
                faction
            )
        self._population_track = 0
        self._population = self._update_population()
        self._prosperity_track = 0
        self._prosperity = self._update_prosperity()
        self._storage = {
            "Food":8,
            "Healthcare":12,
            "Education":12,
            "Luxuries":12
            }
        self._storages = 0 # Extra Storages

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
    @property
    def food_storage(self) -> int:
        return self._storage["Food"]
    @property
    def luxuries_storage(self) -> int:
        return self._storage["Luxuries"]
    @property
    def education_storage(self) -> int:
        return self._storage["Education"]
    @property
    def healthcare_storage(self) -> int:
        return self._storage["Healthcare"]
    @property
    def storage(self) -> dict:
        return self._storage

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
    
    def _add_storage(self, type):
        logger.debug("Called MiddleClass _add_storage")
        from game.data.classes import Storage
        storage = Storage(type)
        self._storage[type] += storage.size
        self._storages += 1
        return
    
    def _remove_storage(self, type):
        logger.debug("Called MiddleClass _remove_storage")
        if self._storages <= 0:
            raise Exception("Attempted to remove storage, but none were found")
        from game.data.classes import Storage
        storage = Storage(type)
        self._storage[type] -= storage.size
        self._storages -= 1
        return

class Capitalists(Player):
    def __init__(
            self,
            faction: str = "Capitalists"
        ):
        logger.debug("Creating Capitalists")
        super().__init__(        
                faction
            )
        self._revenue = 0
        self._capital = 0
        self._storage = {
                "Food":8,
                "Healthcare":12,
                "Education":12,
                "Luxuries":12
                }
        self._free_trade_zone = {
            "Food": 8,
            "Luxuries": 12
        }
        self._storages = 0

    ### Attributes ###

    @property
    def food_storage(self) -> int:
        return self._storage["Food"]
    @property
    def luxuries_storage(self) -> int:
        return self._storage["Luxuries"]
    @property
    def education_storage(self) -> int:
        return self._storage["Education"]
    @property
    def healthcare_storage(self) -> int:
        return self._storage["Healthcare"]
    @property
    def storage(self) -> dict:
        return self._storage
    
    ### Methods ###

    def _add_storage(self, type):
        logger.debug("Called Capitalists _add_storage")
        from game.data.classes import Storage
        storage = Storage(type)
        self._storage[type] += storage.size
        self._storages += 1
        return
    
    def _remove_storage(self, type):
        logger.debug("Called Capitalists _remove_storage")
        if self._storages <= 0:
            raise Exception("Attempted to remove storage, but none were found")
        from game.data.classes import Storage
        storage = Storage(type)
        self._storage[type] -= storage.size
        self._storages -= 1
        return

class NPCState(Player): 
    def __init__(
            self,
            faction: str = "NPC State",
            storage: dict = {
                "Food":0,
                "Healthcare":0,
                "Education":0,
                "Luxuries":0
                }
        ):
        logger.debug("Creating NPC State")
        super().__init__(            
                faction
            )
        self._storage = storage # MAKE THIS A METHOD CALL INSTEAD

    ### Attributes ###

    @property
    def food_storage(self) -> int:
        logger.error("NPC State cannot have food")
        return self._storage["Food"]
    @property
    def luxuries_storage(self) -> int:
        logger.error("NPC State cannot have luxuries")
        return self._storage["Luxuries"]
    @property
    def education_storage(self) -> int:
        return self._storage["Education"]
    @property
    def healthcare_storage(self) -> int:
        return self._storage["Healthcare"]
    @property
    def storage(self) -> dict:
        return self._storage
    @property
    def influence(self) -> int:
        logger.error("NPC State cannot have its own influence")
        return self._influence

class PlayerState(NPCState):
    def __init__(
            self,
            faction: str = "State",
            storage: dict = {
                "Food":0,
                "Healthcare":0,
                "Education":0,
                "Luxuries":0
                },
            legitimacy: dict[str,int] = {"Working Class": 1, "Middle Class": 1, "Capitalists": 1}
        ):
        logger.debug("Creating Player State")
        super().__init__(            
                faction,
                storage
            )
        self._legitimacy = legitimacy

    @property
    def food_storage(self) -> int:
        return self._storage["Food"]
    @property
    def luxuries_storage(self) -> int:
        return self._storage["Luxuries"]
    @property
    def influence(self) -> int:
        return self._influence


class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    Masking needs to take place before this can be passed to an agent
    """

    def __init__(self, players: dict, player_count: int):
        """
        Gamestate initiailisation creates the frameworks for all concepts in the game
        These frameworks may be empty and should be set up later, to aid implementation of expansion packs
        """
        logger.debug("Instantiating gamestate")
        import game.data.references as refs
        import random as rand
        from copy import copy, deepcopy
        self.player_count = player_count
        self.players = players

        ### Attributes ###

        ## Substates ##
        # players: dict - from init

        ## Game Metadata ##
        # player_count: int - from init
        self.round: int = 0
        self.phase: str = "Preparation"
        self.turn: int = 1
        self.active_player: str = "Working Class"

        ## Card Decks ##
        # Company Decks
        self.company_deck: dict[str,list] = {faction: list(companies) for faction, companies in refs.company_decks.items()}
        for comps in self.company_deck.values():
            rand.shuffle(comps)
        # Immigration Cards
        self.immigration_cards: list = list(refs.immigration_cards)
        rand.shuffle(self.immigration_cards)
        # Export Cards
        self.export_cards: list = list(refs.export_cards)
        rand.shuffle(self.export_cards)
        # Political Agenda Cards
        self.political_agenda_cards: list = list(refs.political_agenda_cards)
        rand.shuffle(self.political_agenda_cards)
        # Political Agenda Cards
        self.business_deal_cards: list = list(refs.business_deal_cards)
        rand.shuffle(self.business_deal_cards)

        ## Assets ##
        # Worker Pool
        self.worker_pool: dict[str,list] = {faction:list(workers) for faction, workers in refs.worker_pool.items()}
        self.storages: int = copy(refs.default_storages)
        self.election_cubes: dict[str,int] = copy(refs.default_election_cubes)
        self.default_machinery_tokens = copy(refs.default_machinery_tokens)
        self.default_strike_tokens = copy(refs.default_strike_tokens)
        self.default_legitimacy_tokens = copy(refs.default_legitimacy_tokens)

        ## Board Areas ##
        # Unemployment Area
        self.unemployed_workers: dict[str,list] = {"Working Class": [], "Middle Class": []}
        # Company Slots
        def setup_companies():
            from game.data.classes import CompanySlot
            company_slots = {"Working Class": [], "Middle Class": [], "Capitalists": [], "State": []}
            for _ in range(2):
                company_slots["Working Class"].append(CompanySlot("Working Class"))
            for _ in range(8):
                company_slots["Middle Class"].append(CompanySlot("Middle Class"))
            for _ in range(12):
                company_slots["Capitalists"].append(CompanySlot("Capitalists"))
            for _ in range(9):
                company_slots["State"].append(CompanySlot("State"))
            return {key: tuple(value) for key, value in company_slots.items()}
        self.companies: dict[str,tuple] = setup_companies()
        self.unions = deepcopy(refs.unions)
        # Laws / Elections
        self.laws: dict = deepcopy(refs.default_laws)
        self.tariff_level: int = self.laws[6 - 1].position
        self.voting_area = deepcopy(refs.voting_area)
        self.voting_bag: dict = {player.faction: 0 for player in self.players.values()}



    # Safety Checks
    def corroborate_worker_count(self):
        """Checks if the population trackers of WC (and MC) are true to the workers on the board"""
        WC_track = 0
        MC_track = 0

        # Record Players' Understanding
        WC_num = self.players['Working Class'].population_track
        if self.player_count > 2:
            MC_num = self.players['Middle Class'].population_track
            
        # Count Workers in Companies
        for factioncomps in self.companies.values():
            for comp in factioncomps.values():
                if comp is None: # Ignore unfilled company slots
                    continue
                for worker in comp.workers.values():
                    if worker is None: # If there is no worker in the first slot, there are no workers
                        continue
                    if worker.faction == 'Working Class':
                        WC_track += 1
                    if worker.faction == 'Middle Class':
                        MC_track += 1

        # Count Unemployed Workers
        for worker in self.unemployed_workers['Working Class']:
            WC_track += 1
        for worker in self.unemployed_workers['Middle Class']:
            MC_track += 1                
        
        # Compare Values
        acc = True
        if WC_track != WC_num:
            acc = False
        if self.player_count > 2 and MC_track != MC_num:
            acc = False

        # Display Error Messages
        if not acc:
            logger.error(f"Worker counts cannot be reconciled.")
            logger.error(f"Working Class Player tracker believes there are {WC_num}. Checker found {WC_track}.")
            if self.player_count > 2:
                logger.error(f"Middle Class Player tracker believes there are {MC_num}. Checker found {MC_track}")
                     
        return acc
