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
    round: int = 0
    phase: str = 'Preparation'
    turn: int = 0
    active_player: str = 'Working Class'
    free_action_taken: bool = False
    players: dict = field(default_factory=dict) # players must be the last arg, since it is appended to the dict in load_save

    ### Methods ###
    def to_dict(self) -> dict: # For saving
        return {k.lstrip('_'): v for k, v in vars(self).items()}

    
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
    alive: bool
    employed: bool

    def check(self):
        return {
            'faction': self.faction,
            'skill': self.skill,
            'alive': self.alive,
            'employed': self.employed
        }

@dataclass(frozen=True)
class Card:
    faction: str
    description: str

@dataclass
class Company:
    name: str
    faction: str
    industry: str
    cost: int
    production: int
    production_bonus: int
    production_bonus_active: bool
    wages: dict
    worker_slots: list
    workers: list
    id: int

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


# Reference building functions
def build_company_pools():
    """
    reads in a csv to create Company objects.
    These are stored as:
    dict[str: list[object]]
    company_pool: 'working_class'[object]
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
        slots = []
        if not pd.isnull(row['Class1']):
            slots.append(Worker(row['Class1'],row['Skill1'],True,True))
        if not pd.isnull(row['Class2']):
            slots.append(Worker(row['Class2'],row['Skill2'],True,True))
        if not pd.isnull(row['Class3']):
            slots.append(Worker(row['Class3'],row['Skill3'],True,True))        
        comp = Company(
            row['Name'], 
            row['Owner'], 
            row['Industry'], 
            row['Cost'], 
            row['Base Production'],
            row['Upgrade Value'],
            False,
            {'L1': row['L1'], 'L2': row['L2'], 'L3': row['L3']},
            slots,
            [],
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
    return {
        'working_class': working_class_company_pool,
        'middle_class': middle_class_company_pool,
        'capitalists': capitalists_company_pool,
        'state': state_company_pool
    } 


# ----------- END ---------- #
logger.debug("Finished importing data.common")

print("common.py fully loaded")