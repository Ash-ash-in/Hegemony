import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass, field


class Worker:
    
    import itertools
    wc_gen = itertools.count()
    mc_gen = itertools.count()

    def __init__(self, faction: str, skill: str, committed: bool):
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
            'skill': self.skill,
            'committed': self.committed
        }

@dataclass
class ImmigrationCard:
    WorkingClass: str
    MiddleClass: str  


class Company:

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
            production_bonus_active: bool,
            current_wage: str,
            wages: dict | None,
            worker_requirements: dict,
            workers_slots: dict,
            committed: bool
        ):
        self._name = name
        self._faction = faction
        self._industry = industry
        self._cost = cost
        self._production = production
        self._production_bonus = production_bonus
        self._production_bonus_active = production_bonus_active
        self._current_wage = current_wage
        self._wages = wages
        self._worker_slots = worker_slots
        self._workers = workers
        self._committed = committed
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
    def production_bonus_active(self) -> bool:
        return self._production_bonus_active
    @property
    def current_wage(self) -> str:
        return self._current_wage
    @property
    def wages(self) -> dict | None:
        return self._wages
    @property
    def worker_slots(self) -> dict:
        return self._worker_slots
    @property
    def workers(self) -> dict:
        return self._workers
    @property
    def committed(self) -> bool:
        return self._committed
    @property
    def id(self) -> str:
        return self._id

    ### Methods ###
    def to_dict(self) -> dict:
        return {k.lstrip('_'): v for k, v in vars(self).items()}
    
    def _remove_worker(self, index: int):
        self.workers[index] = None
        logger.debug(f"Worker removed from {self._name}")

    def _add_worker(self, index:int, worker: object):
        self.workers[index] = worker
        logger.debug(f"Worker added to {self._name}")

    def _toggle_production_bonus(self):
        if self._production_bonus == 0:
            raise Exception(f"Instructed to toggle production bonus on company without one ({self._name})")
        self._production_bonus_active = not self._production_bonus_active
        logger.debug(f"{self._name} production bonus {'activated' if self._production_bonus_active else 'deactivated'}")

    def _set_wages(self, L_value: str):
        if L_value[0:] != 'L' or len(L_value) != 2:
            raise Exception(f"Wage instruction must be in format 'L2'. Received: {L_value}") 
        if self._wages is None:
            raise Exception(f"Instructed to change wages on company without wages ({self._name})")
        self._current_wage = L_value
        logger.debug(f"{self._name} wages set to {L_value}")

    def _transfer_ownership(self, target_faction):
        """This needs to happen alongside moving the company to the relevant area on the board"""
        if target_faction == self._faction:
            raise Exception("Cannot transfer company to self ({target_faction} selected as target)")
        self._faction = target_faction

@dataclass(frozen=True)
class ActionCard:
    faction: str
    description: str

@dataclass(frozen = True)
class Event:
    name: str
    description: str
    effect: dict[str, int]
    forfeit: str

@dataclass
class Law:
    name: str
    position: int

# ---------- References ----------- #
# Handy variables for building data in setup
faction_play_order = ["Working Class", "Middle Class", "Capitalists", "State"]
faction_instantiate_order = ["Working Class", "Capitalists", "Middle Class", "State"]
phases = ['Preparation','Action','Production','Elections','Scoring']
industries = ['Healthcare','Education','Luxury','Agriculture','Media']




