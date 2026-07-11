import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass


## Economics
class Worker:
    """Immuatable information about a worker"""
    import itertools
    wc_gen = itertools.count()
    mc_gen = itertools.count()

    def __init__(self, faction: str, skill: str):
        self.faction = faction
        self.skill = skill
        # Retrieve next ID from the class generator
        if faction == 'Working Class':
            self.id = "WC"+str(next(self.wc_gen))
        elif faction == "Middle Class":
            self.id = "MC"+str(next(self.mc_gen))

    def check(self):
        return {
            'faction': self.faction,
            'skill': self.skill
        }

@dataclass
class Union:
    """
    Unions are basically independent worker slots
    
    They have basic internal checks for when workers are assigned, 
    but cannot see the wider gamestate. 

    Worker assignment/unassignment should always follow a worker count validity check
    """
    industry: str
    occupant: Worker | None

    def assign_worker(self, worker: Worker) -> None:

        # Validity Checks
        if self.occupant is not None:
            raise Exception("Cannot assign worker to occupied union")
        if worker.skill != self.industry:
            raise Exception(f"{worker.skill} worker assigned to {self.industry} union")
        if worker.faction != "Working Class":
            raise Exception("Middle Class worker assigned to union")
        
        # Execute
        self.occupant = worker
        return

    def unassign_worker(self):

        # Validity Checks
        # Checks cannot be completed within the class, 
        # but unassignment should only happen if the worker count condition is not longer met

        # Execute
        self.occupant = None
        return

class Company:
    """Immutable information about a company"""
    import itertools
    id_gen = itertools.count()

    ### Init ###
    def __init__(
            self,
            name: str,
            faction: str,
            industry: str,
            cost: int,
            production: int,
            production_bonus: int,
            wages: dict | None,
            worker_requirements: dict
        ):
        self._name = name
        self._faction = faction
        self._industry = industry
        self._cost = cost
        self._production = production
        self._production_bonus = production_bonus
        self._wages = wages
        self._worker_requirements = worker_requirements
        self._id = "company_"+str(next(self.id_gen))

    ### Attributes ###
    @property
    def name(self) -> str:
        return self._name
    @property
    def faction(self) -> str:
        return self._faction
    @property
    def industry(self) -> str:
        return self._industry
    @property
    def cost(self) -> int:
        return self._cost
    @property
    def production(self) -> int:
        return self._production
    @property
    def production_bonus(self) -> int:
        return self._production_bonus
    @property
    def wages(self) -> dict | None:
        return self._wages
    @property
    def worker_requirements(self) -> dict:
        return self._worker_requirements
    @property
    def id(self) -> str:
        return self._id

class CompanySlot:
    """
    The main element to interact with companies and workers.
    References to companies and workers are held as attributes while they are placed here,
    and are simply removed when they are not.

    The validation checks only maintain internal consistency and are a last resort, 
    real validity should take place at the rules layer
    """
    def __init__(
            self,
            faction: str,
            company: Company | None,
            workers: list[Worker | None],
            wage: int,
            bonus_active: bool,
            committed: bool,
            strike: bool
        ):
        # Initialisation Validity
        if company is not None:
            # Wages
            if company.wages is None:
                if wage != 0:
                    raise Exception("Company does not have wages, value should be set to 0")
            else:
                if wage < 1 or wage > 3:
                    raise Exception("Companies with wages should be between 1 and 3")
            # Bonus Production
            if company.production_bonus == 0 and bonus_active:
                raise Exception("Company has no production bonus, yet was passed as true")
            # Workers
            if len(company.worker_requirements.keys()) != len(workers):
                raise Exception(f"Number of workers positions passed ({len(workers)}) does not match number of slots in company ({len(company.worker_requirements.keys())})")


        self.faction = faction
        self.company = company
        self.workers = workers
        self.wage = wage
        self.bonus_active = bonus_active
        self.committed = committed
        self.strike = strike


    # def _remove_worker(self, index: int):
    #     self.workers[index] = None
    #     logger.debug(f"Worker removed from {self._name}")

    # def _add_worker(self, index:int, worker: object):
    #     self.workers[index] = worker
    #     logger.debug(f"Worker added to {self._name}")

    # def _toggle_production_bonus(self):
    #     if self._production_bonus == 0:
    #         raise Exception(f"Instructed to toggle production bonus on company without one ({self._name})")
    #     self._production_bonus_active = not self._production_bonus_active
    #     logger.debug(f"{self._name} production bonus {'activated' if self._production_bonus_active else 'deactivated'}")

    # def _set_wages(self, L_value: str):
    #     if L_value[0:] != 'L' or len(L_value) != 2:
    #         raise Exception(f"Wage instruction must be in format 'L2'. Received: {L_value}") 
    #     if self._wages is None:
    #         raise Exception(f"Instructed to change wages on company without wages ({self._name})")
    #     self._current_wage = L_value
    #     logger.debug(f"{self._name} wages set to {L_value}")

    # def _transfer_ownership(self, target_faction):
    #     """This needs to happen alongside moving the company to the relevant area on the board"""
    #     if target_faction == self._faction:
    #         raise Exception("Cannot transfer company to self ({target_faction} selected as target)")
    #     self._faction = target_faction


## Cards / Decks
@dataclass
class ImmigrationCard:
    WorkingClass: tuple[str,str]
    MiddleClass: tuple[str,str] 

@dataclass
class ExportCard:
    food: tuple[tuple[int, int], tuple[int, int]]
    healthcare: tuple[tuple[int, int], tuple[int, int]]
    luxuries: tuple[tuple[int, int], tuple[int, int]]
    education: tuple[tuple[int, int], tuple[int, int]]

@dataclass
class PoliticalAgendaCard:
    policies: dict[int,int]

@dataclass
class BusinessDealCard:
    goods: dict[str, int]
    # Example {"Luxuries": 8, "Food": 10}
    cost: int
    tariffs: dict[str, int] # Dependant on the position of law 6
    # Example: {"A":18,"B":10,"C":0}

## Legal / Voting
@dataclass
class Law:
    id: int
    name: str
    position: int

@dataclass
class Election:
    """Shows the position of the current voting area"""
    proponents: dict[str,tuple[int, int]] # {"Faction":(cubes, influence)}
    opponents: dict[str,tuple[int, int]] # {"Faction":(cubes, influence)}




## Utils
class Config:
    def __init__(self, config: dict):
        self.player_count = config["player_count"]
        self.agents = config["agents"]

        # Validation
        if type(self.player_count) != int:
            raise Exception("Invalid datatype passed as player_count (should be int)")
        if type(self.agents) != dict:
            raise Exception("Invalid datatype passed as agents (should be dict)")
