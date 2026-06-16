import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass, field

# common variables used across files
@dataclass
class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    """
    ### Attributes ###
    player_count: int
    round: int = 1
    phase: str = 'Preparation'
    turn: int = 1
    active_player: str = "Working Class"
    company_deck: dict = {'Capitalists': [], 'State': [], 'Working Class': [], 'Middle Class': []}
    companies: dict = { # Company slots on board
        'Capitalists': {'C'+str(i+1): None for i in range(12)}, 
        'Working Class': {'C1': None, 'C2':None},
        'Middle Class': {'C'+str(i+1): None for i in range(8)},
        'State': {'C'+str(i+1): None for i in range(9)}
        }
    worker_pool: dict = field(default_factory=dict)
    unemployed_workers: dict = {'Working Class': [], 'Middle Class': []}
    players: dict = field(default_factory=dict) # players must be the last arg, since it is appended to the dict in load_save

    ### Methods ###
    def to_dict(self) -> dict: # For saving
        return {k.lstrip('_'): v for k, v in vars(self).items()}
    
    # Reference building functions
    def build_company_decks(self):
        """
        reads in a csv to create Company objects.
        These are stored as:
        dict[str: list[object]]
        company_deck: 'working_class'[object]
        """
        import pandas as pd
        import os
        logger.debug("Reading in companies")
        root = os.getcwd()
        comp_df = pd.read_csv(os.path.join(root, "game", "data", "companies.csv"))

        working_class_company_pool = []
        middle_class_company_pool = []
        capitalists_company_pool = []
        state_company_pool = []
        for index, row in comp_df.iterrows():
            if not type(index) == int:
                raise Exception("Index of company dataframe must be an integer")

            # Wages
            if pd.isnull(row['L1']):
                wages = None
            else: 
                wages = {'L1': row['L1'], 'L2': row['L2'], 'L3': row['L3']}
            
            # Worker slots
            slots = {}
            if not pd.isnull(row['Class1']):
                slots[1] = Worker(row['Class1'],row['Skill1'])
            if not pd.isnull(row['Class2']):
                slots[2] = Worker(row['Class2'],row['Skill2'])
            if not pd.isnull(row['Class3']):
                slots[3] = Worker(row['Class3'],row['Skill3'])     
            comp = Company(
                row['Name'], 
                row['Owner'], 
                row['Industry'], 
                row['Cost'], 
                row['Base Production'],
                0 if pd.isnull(row['Upgrade Value']) else row['Upgrade Value'],
                False,
                'L2',
                wages,
                slots,
                {i: None for i in range(len(slots.keys()))}, # Empty workers dict
                index
                )
            if comp.faction == 'Working Class':
                working_class_company_pool.append(comp)
            elif comp.faction == 'Middle Class':
                middle_class_company_pool.append(comp)
            elif comp.faction == 'Capitalists':
                capitalists_company_pool.append(comp)
            elif comp.faction == 'State':
                state_company_pool.append(comp)
            else:
                raise Exception('Faction not found')
            
        self.company_deck = {
            'Working Class': working_class_company_pool,
            'Middle Class': middle_class_company_pool,
            'Capialists': capitalists_company_pool,
            'State': state_company_pool
        }
        logger.debug("Company pools set up")

    def build_worker_pool(self):
        from game.data.common import industries
        worker_pool = {'working_class_worker_pool':[], 'middle_class_worker_pool':[]}

        # skilled workers
        for skill in industries:
            for i in range(5):
                worker_pool['working_class_worker_pool'].append(Worker(
                    'Working Class',
                    skill
                ))
                    
        # unskilled workers            
        for i in range(23): # double check unskilled worker count
            worker_pool['working_class_worker_pool'].append(Worker(
                'Working Class',
                'Unskilled'
            ))   
                
        # middle class workers

        # skilled workers
        for skill in industries:
            for i in range(5): 
                worker_pool['middle_class_worker_pool'].append(Worker(
                    'Middle Class',
                    skill
                ))
        # unskilled workers            
        for i in range(17): # double check unskilled worker count
            worker_pool['middle_class_worker_pool'].append(Worker(
                'Middle Class',
                'Unskilled'
            ))

        self.worker_pool = worker_pool        
        logging.debug(f"Worker setup complete. Worker count: {len(worker_pool['working_class_worker_pool']) + len(worker_pool['middle_class_worker_pool'])}")
        
    
@dataclass
class PlayerReference:
    active_factions: list
    existing_factions: list
    working_class: object
    middle_class: object | None
    capitalists: object
    state: object

@dataclass
class Worker:
    faction: str
    skill: str

    def check(self):
        return {
            'faction': self.faction,
            'skill': self.skill
        }
    

class Company:
    from game.data.common import Worker 

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
            worker_slots: dict,
            workers: dict,
            id: int
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
        self._id = id

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
    def id(self) -> int:
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
class Card:
    faction: str
    description: str

@dataclass(frozen = True)
class Event:
    name: str
    description: str
    effect: dict[str, int]
    forfeit: str

# ---------- References ----------- #
# Handy variables for building data in setup
faction_play_order = ["Working Class", "Middle Class", "Capitalists", "State"]
faction_instantiate_order = ["Working Class", "Capitalists", "Middle Class", "State"]
phases = ['Preparation','Action','Production','Elections','Scoring']
industries = ['Healthcare','Education','Luxury','Agriculture','Media']


# ----------- END ---------- #
logger.debug("Finished importing data.common")

print("common.py fully loaded")

