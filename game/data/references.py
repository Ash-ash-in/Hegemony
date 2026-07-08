import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field

# ----------- Functions ------------ #
# Core Assets
def build_company_decks():
    """
    reads in a csv to create Company objects.
    These are stored as:
    dict[str: list[object]]
    company_deck: 'working_class'[object]
    """
    import pandas as pd
    import os
    from game.data.classes import Company
    logger.debug("Reading in companies")
    root = os.getcwd()
    comp_df = pd.read_csv(os.path.join(root, "game", "data", "companies.csv"))

    working_class_company_pool = []
    middle_class_company_pool = []
    capitalists_company_pool = []
    state_company_pool = []
    for _, row in comp_df.iterrows():

        # Wages
        if pd.isnull(row['L1']):
            wages = None
        else: 
            wages = {'L1': row['L1'], 'L2': row['L2'], 'L3': row['L3']}
        
        # Worker slots
        slots = {}
        if not pd.isnull(row['Class1']):
            slots[1] = {"faction":row['Class1'], "skill": row['Skill1']}
        if not pd.isnull(row['Class2']):
            slots[2] = {"faction":row['Class2'], "skill": row['Skill2']}
        if not pd.isnull(row['Class3']):
            slots[3] = {"faction":row['Class3'], "skill": row['Skill3']}    
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
            {i+1: None for i in range(len(slots.keys()))}, # Empty workers dict
            False
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
        'Capitalists': capitalists_company_pool,
        'State': state_company_pool
    }
    logger.debug("Company pools set up")

def build_unions():
    logger.debug("Building unions")
    from game.data.classes import Union
    unions = {}
    for ind in industries:
        unions[ind] = Union(ind, None)
    return unions

def build_worker_pool():
    logger.debug("Building worker pool")
    from game.data.classes import Worker
    worker_pool = {'Working Class':[], 'Middle Class':[]}

    ## Working Class ##

    # Skilled
    for skill in industries:
        for i in range(5):
            worker_pool['Working Class'].append(Worker(
                'Working Class',
                skill,
            ))
                
    # Unskilled            
    for i in range(23):
        worker_pool['Working Class'].append(Worker(
            'Working Class',
            'Unskilled'
        ))   
            
    ## Middle Class ##

    # Skilled
    for skill in industries:
        for i in range(5): 
            worker_pool['Middle Class'].append(Worker(
                'Middle Class',
                skill
            ))
    # Unskilled            
    for i in range(17):
        worker_pool['Middle Class'].append(Worker(
            'Middle Class',
            'Unskilled'
        ))
     
    logging.debug(f"Worker setup complete. Worker count: {len(worker_pool['Working Class']) + len(worker_pool['Middle Class'])}")
    return worker_pool

def build_laws():
    logger.debug("Building law refs")
    from game.data.classes import Law
    laws = [
        Law(1, "Fiscal Policy", 3),
        Law(2, "Labour Market", 2),
        Law(3, "Taxation", 1),
        Law(4, "Healthcare and Benefits", 2),
        Law(5, "Education", 3),
        Law(6, "Foreign Trade", 2),
        Law(7, "Immigration", 2)
    ]
    return laws

# Card Decks
def build_immigration_cards():
    logger.debug("(Re)building immigration card deck")
    from game.data.classes import ImmigrationCard
    from random import shuffle
    immigration_cards = []
    for industry in industries:
        for i in range(3):
            if i < 2:
                immigration_cards.append(ImmigrationCard(
                    ('Working Class', industry),
                    ('Middle Class', 'Unskilled')
                ))
            immigration_cards.append(ImmigrationCard(
                ('Working Class', 'Unskilled'),
                ('Middle Class', industry)
            ))
    return immigration_cards




# ---------- References ----------- #
# Handy variables for building data in setup
faction_play_order = ["Working Class", "Middle Class", "Capitalists", "State"]
faction_instantiate_order = ["Working Class", "Capitalists", "Middle Class", "State"]
phases = ['Preparation','Action','Production','Elections','Scoring']
industries = ['Healthcare','Education','Luxury','Agriculture','Media']
company_decks = build_company_decks()
unions = build_unions()
worker_pool = build_worker_pool()
immigration_cards = build_immigration_cards()
laws = build_laws()