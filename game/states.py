import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field

@dataclass
class CompanySlot:
    """
    The main element to interact with companies and workers.
    References to companies and workers are held as attributes while they are placed here,
    and are simply removed when they are not.

    These are instantiated when the gamestate is first created, and are only modified from then on.

    The validation checks only maintain internal consistency and are a last resort, 
    real validity should take place at the rules layer
    """
    from game.data.classes import Company, Worker
    faction: str
    company: Company | None
    workers: list[Worker | None]
    wage: int
    bonus_active: bool
    committed: bool
    strike: bool
    
    def __init__(
                self,
                faction: str
            ):
        self.faction = faction # Name of faction owning the slot
        self.company = None
        self.workers = []
        self.wage = 0
        self.bonus_active = False
        self.committed = False
        self.strike = False

    def __repr__(self) -> str:
        return f"Company: ({self.company}). Workers: {self.workers}"

    def validate(self):
    # Quicky Validity Checks to check internal rules. 
    # Cannot prove all rules are met.
    # Could benefit from extra check.
        if self.company is not None:
            # Wages
            if self.company.wages is None:
                if self.wage != 0:
                    raise Exception("Company does not have wages, value should be set to 0")
            else:
                if self.wage < 1 or self.wage > 3:
                    raise Exception("Companies with wages should be between 1 and 3")
            # Bonus Production
            if self.company.production_bonus == 0 and self.bonus_active:
                raise Exception("Company has no production bonus, yet was passed as true")
            # Workers
            if self.workers is not None:
                if len(self.company.worker_requirements.keys()) != len(self.workers):
                    raise Exception(f"Number of workers positions passed ({len(self.workers)}) does not match number of slots in company ({len(self.company.worker_requirements.keys())})")
                if self.company.faction == "Middle Class" and self.bonus_active and self.workers[-1] is None:
                    raise Exception("Middle Class company production bonus is active without worker")                                                              
            # Strikes
            if self.strike and not self.committed:
                raise Exception("Striking workers but be committed")

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
        self._market = []
        self._deck = [] # Setup later
        self._hand = []

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
    def market(self) -> list:
        return self._market
    @property
    def deck(self) -> list:
        return self._deck
    @property
    def hand(self) -> list:
        return self._hand
    

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
        self._money += 50
        logger.debug(f"{self._faction} money: {self.money}")
        logger.debug(f"{self._faction} total loans: {self._loans}")

    def _repay_loan(self):
        logger.debug(f"{self._faction} _remove_loan()")
        self._loans -= 1
        self._money -= 50
        logger.debug(f"{self._faction} money: {self._money}")
        logger.debug(f"{self._faction} remaining loans: {self._loans}")

    def _add_company_to_market(self, card: Company):
        logger.debug(f"{self._faction} drawing company cards")
        self._market.append(card)
        logger.debug(f"{self._faction} companies: {len(self._market)}")

    def _remove_company_from_market(self, card: Company):
        logger.debug(f"{self.faction} removing a company card")
        self._market.remove(card)
        logger.debug(f"{self._faction} companies in market: {len(self._market)}")

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
        self._strike_tokens = 7
        
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
    def strike_tokens(self) -> int:
        return self._strike_tokens  

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
    def prosperity_track(self) -> int:
        return self._prosperity_track   
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
    @property
    def storages(self) -> int:
        return self._storages
    
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
                "Food": 8,
                "Healthcare": 12,
                "Education": 12,
                "Luxuries": 12
                }
        self._free_trade_zone = {
            "Food": 8,
            "Luxuries": 12
        }
        self._storages = 0
        self._machinery_tokens = 6

    ### Attributes ###

    @property
    def revenue(self) -> int:
        return self._revenue
    @property
    def capital(self) -> int:
        return self._capital
    @property # Overwrites parent property
    def money(self) -> int:
        return self._revenue + self._capital
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
    @property
    def free_trade_zone(self) -> dict:
        return self._free_trade_zone
    @property
    def storages(self) -> int:
        return self._storages
    @property
    def machinery_tokens(self) -> int:
        return self._machinery_tokens

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

    def _add_money(self, amount):
        logger.debug(f"{self._faction} _add_money({amount})")
        self._revenue += amount
        logger.debug(f"{self._faction} money: {self.money} (revenue: {self._revenue}, capital: {self._capital})")

    def _take_loan(self):
        logger.debug(f"{self._faction} _take_loan()")
        self._loans += 1
        self._capital += 50
        logger.debug(f"{self._faction} money: {self.money} (revenue: {self._revenue}, capital: {self._capital})")
        logger.debug(f"{self._faction} total loans: {self._loans}")

    def _repay_loan(self):
        logger.debug(f"{self._faction} _remove_loan()")
        self._loans -= 1
        if self._capital < 50:
            remainder = 50 - self._capital
            self._capital = 0
            self._revenue -= remainder
        else:
            self._capital -= 50
        logger.debug(f"{self._faction} money: {self.money} (revenue: {self._revenue}, capital: {self._capital})")
        logger.debug(f"{self._faction} remaining loans: {self._loans}")


class NPCState(Player): 
    def __init__(
            self,
            faction: str = "State",
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
        self._legitimacy_tokens = {
            "Working Class": 6,
            "Middle Class": 6,
            "Capitalists": 6
            }

    @property
    def food_storage(self) -> int:
        return self._storage["Food"]
    @property
    def luxuries_storage(self) -> int:
        return self._storage["Luxuries"]
    @property
    def influence(self) -> int:
        return self._influence
    @property
    def legitmacy_tokens(self) -> dict:
        return self._legitimacy_tokens


class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    Masking needs to take place before this can be passed to an agent
    """

    def __init__(self, players: dict, player_count: int, game_id: str):
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
        self.game_id: str = game_id
        self.round: int = 0
        self.phase: str = "Preparation"
        self.turn: int = 1
        self.active_player: str = "Working Class"

        ## Assets ##
        # Worker Pool
        self.worker_pool: dict[str,list] = {faction:list(workers) for faction, workers in refs.worker_pool.items()}
        self.storages: int = copy(refs.default_storages)
        self.election_cubes: dict[str,int] = copy(refs.default_election_cubes)

        ## Board Areas ##
        # Unemployment Area
        self.unemployed_workers: dict[str,list] = {"Working Class": [], "Middle Class": []}
        self.demonstration: bool = False
        # Company Slots
        def setup_companies():
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
        self.companies: dict[str,tuple[CompanySlot]] = setup_companies()
        self.unions = deepcopy(refs.unions)
        # Laws / Elections
        self.laws: dict = deepcopy(refs.default_laws)
        self.tariff_level: int = self.laws["Foreign Trade"].position
        self.voting_area = deepcopy(refs.voting_area)
        self.voting_bag: dict = {player.faction: 0 for player in self.players.values()}

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
        self.update_export_card()
        # Political Agenda Cards
        self.political_agenda_cards: list = list(refs.political_agenda_cards)
        rand.shuffle(self.political_agenda_cards)
        # Political Agenda Cards
        self.business_deal_cards: list = list(refs.business_deal_cards)
        rand.shuffle(self.business_deal_cards)
        self.update_business_deals()

    ### Methods ###

    # Game Flow
    def update_export_card(self) -> None:
        """Updates active export card with the first in the deck 
        and moves that card to the back"""
        logger.debug("updating active export card")
        card = self.export_cards[0]
        self.export_cards.remove(card)
        self.export_cards.append(card)
        logger.debug("card moved to back of deck")
        self.active_export_card = card
        logger.debug("active export card updated")

    def update_business_deals(self) -> None:
        """Updates active business deals accoring to law 6. 
        Uses the first cards in the deck 
        and moves them to the back"""
        logger.debug("updating active business deals")
        self.active_business_deals = []
        position = self.laws["Foreign Trade"].position
        if position == 0:
            logger.debug("no business deal cards required")
        else:
            for i in range(position - 1):          
                card = self.business_deal_cards[0]
                self.business_deal_cards.remove(card)
                self.business_deal_cards.append(card)
                logger.debug("card moved to back of deck")
                self.active_business_deals.append(card)
                logger.debug("active business deal card updated")
        logger.debug("business deal cards updated")

    def update_immigration_card(self) -> None:
        """Simply moves the front card to the back. 
        Should only be called through the rule layer"""
        logger.debug("updating immigration card")
        card = self.immigration_cards[0]
        self.immigration_cards.remove(card)
        self.immigration_cards.append(card)
        logger.debug("card moved to back of deck")

    def check_founded_companies(self, faction: str) -> int:
        """Returns the number of founded companies owned by the given faction"""
        compcount = 0
        for compslot in self.companies[faction]:
            if compslot.company is not None:
                compcount += 1
        return compcount

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
            for slot in factioncomps:
                if slot.company is None: # Ignore unfilled company slots
                    continue
                for worker in slot.workers:
                    if worker is None: # If there is no worker in the first slot, there are no workers
                        continue
                    elif worker.faction == 'Working Class':
                        WC_track += 1
                    elif worker.faction == 'Middle Class':
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
        if self.player_count > 2:
            if MC_track != MC_num:
                acc = False

        # Display Error Messages
        if not acc:
            logger.error(f"Worker counts cannot be reconciled.")
            logger.error(f"Working Class Player tracker believes there are {WC_num}. Checker found {WC_track}.")
            if self.player_count > 2:
                logger.error(f"Middle Class Player tracker believes there are {MC_num}. Checker found {MC_track}")
                     
        return acc
