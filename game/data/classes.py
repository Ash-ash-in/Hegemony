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

    def __repr__(self) -> str:
        return f"{self.faction} {self.skill} worker"

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
            wages: dict[str, int] | None, # eg. 'L1': 5
            worker_requirements: dict[int,dict[str,str]] # eg. 1: {'faction': 'Working Class', 'skill': 'Luxury'}
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

    def __repr__(self) -> str:
        from game.data.references import industries
        return f"{self.name}: {self.faction} company with {len(self.worker_requirements)} worker slots. Produces {self.production} {industries[self.industry]}"

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

class Storage:
    def __init__(self, resource: str):
        self.resource = resource
        if resource == 'Food':
            self.size = 8
        elif resource in ("Luxuries", "Education", "Healthcare"):
            self.size = 12

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
@dataclass
class CheckResponse:
    """
    Contains all the information that would allow an agent to successfully complete this action
    
    # Attributes:
    validity: bool
    tooltip: str
    actiontype: str
    params: list    
    """
    validity: bool
    tooltip: str
    actiontype: str
    params: list

class Config:
    def __init__(self, config: dict):

        # Validation
        if type(config["player_count"]) != int:
            raise Exception("Invalid datatype passed as player_count (should be int)")
        if type(config["agents"]) != dict:
            raise Exception("Invalid datatype passed as agents (should be dict)")
        if type(config["expansions"]) != dict:
            raise Exception("Invalid datatype passed as expansions (should be dict)")

        self.player_count = config["player_count"]
        self.agents = config["agents"]
        self.expansions = config["expansions"]

        # Build Game ID
        # Read in previously used IDs
        import os
        import pandas as pd
        if os.path.exists(os.path.join("training", "game_ids.csv")):
            ids = pd.read_csv(os.path.join("training", "game_ids.csv"))
        else:
            ids = pd.DataFrame(columns=["ID", "expansion", "player_count", "count"])

        # Prepare new instance
        # Player Count
        id_append = {"player_count": [config["player_count"]]}
        # Expansions
        exp_count = 0
        for exp_bool in config["expansions"].values():
            exp_count += exp_bool
        if exp_count == 0:
            id_append["expansion"] = ["G"]
        elif exp_count == 2:
            id_append["expansion"] = ["B"]
        else:
            if config["expansions"]["historical_events"] == 1:
                id_append["expansion"] = ["H"]
            else:
                id_append["expansion"] = ["C"]
        # Iterator
        id_append["count"] = [len(ids[(ids["expansion"] == id_append["expansion"]) & (ids["player_count"] == id_append["player_count"])])]
        # Full ID
        id_append["ID"] = [f"{id_append['expansion']}_{id_append['player_count']}_{id_append['count']}"]
        self.game_id = id_append["ID"]

        # Append new ID
        ids = pd.concat([ids, pd.DataFrame.from_dict(id_append)], axis=0, ignore_index=True)
        ids.to_csv(os.path.join("training", "game_ids.csv"))
