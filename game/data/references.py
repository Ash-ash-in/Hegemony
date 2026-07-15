import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field

# ----------- Functions ------------ #
# Core Mechanics (Mutable)
from game.data.classes import Union
def build_unions() -> dict[str,Union]:
    logger.debug("Building unions")
    from game.data.classes import Union
    unions = {}
    for ind in industries:
        unions[ind] = Union(ind, None)
    return unions

def build_laws() -> dict:
    logger.debug("Building law refs")
    from game.data.classes import Law
    laws = {
        1: Law(1, "Fiscal Policy", 3),
        2: Law(2, "Labour Market", 2),
        3: Law(3, "Taxation", 1),
        4: Law(4, "Healthcare and Benefits", 2),
        5: Law(5, "Education", 3),
        6: Law(6, "Foreign Trade", 2),
        7: Law(7, "Immigration", 2)
    }
    return laws

def build_voting_area():
    from game.data.classes import Election
    return Election({},{})

# Card Decks and Pools (Immutable)
def build_company_decks() -> dict[str,tuple]:
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
            wages,
            slots
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
        
    company_deck = {
        'Working Class': tuple(working_class_company_pool),
        'Middle Class': tuple(middle_class_company_pool),
        'Capitalists': tuple(capitalists_company_pool),
        'State': tuple(state_company_pool)
    }
    return company_deck

def build_worker_pool() -> dict[str,tuple]:
    logger.debug("Building worker pool")
    from game.data.classes import Worker
    WC = []
    MC = []

    ## Working Class ##

    # Skilled
    for skill in industries:
        for i in range(5):
            WC.append(Worker(
                'Working Class',
                skill,
            ))   
    # Unskilled            
    for i in range(23):
        WC.append(Worker(
            'Working Class',
            'Unskilled'
        ))   
    # Check
    if len(WC) != 48:
        raise Exception("Incorrect Number of Working Class Workers made")            
    
    ## Middle Class ##

    # Skilled
    for skill in industries:
        for i in range(5): 
            MC.append(Worker(
                'Middle Class',
                skill
            ))
    # Unskilled            
    for i in range(17):
        MC.append(Worker(
            'Middle Class',
            'Unskilled'
        ))
    # Check
    if len(MC) != 42:
        raise Exception("Incorrect Number of Middle Class Workers made")            

    return {"Working Class":tuple(WC), "Middle Class":tuple(MC)}

def build_immigration_cards() -> tuple:
    logger.debug("Building immigration card deck")
    from game.data.classes import ImmigrationCard
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

    if len(immigration_cards) != 25:
        raise Exception("Incorrect number of immigration cards created")
    return tuple(immigration_cards)

def build_export_cards() -> tuple:
    logger.debug("Building export card deck")
    from game.data.classes import ExportCard
    export_cards = []
    
    # Temporary function
    logger.warning("Temporary export cards in use")
    import random
    for i in range(16):
        export_cards.append(
            ExportCard(
                ((random.randint(1,4), random.randrange(10,51,5)),(random.randint(3,9), random.randrange(35,81,5))),
                ((random.randint(1,4), random.randrange(10,51,5)),(random.randint(3,9), random.randrange(35,81,5))),
                ((random.randint(1,4), random.randrange(10,51,5)),(random.randint(3,9), random.randrange(35,81,5))),
                ((random.randint(1,4), random.randrange(10,51,5)),(random.randint(3,9), random.randrange(35,81,5)))
            )
        )

    if len(export_cards) != 16:
        raise Exception("Incorrect number of export cards created")

    return tuple(export_cards)

def build_political_agenda_cards() -> tuple:
    logger.debug("Building political agenda card deck")
    from game.data.classes import PoliticalAgendaCard
    cards = []

    # Temporary Process
    logger.warning("Temporary political agenda cards used")
    import random
    for i in range(10):
        pols = {}
        for j in range(5):
            pols[j+1] = random.randint(1,4) 
        cards.append(PoliticalAgendaCard(pols))

    if len(cards) != 10:
        raise Exception("Incorrect number of poltical agenda cards created")

    return tuple(cards)

def build_business_deal_cards() -> tuple:
    logger.debug("Building business card deal cards")
    from game.data.classes import BusinessDealCard
    cards = []

    # Temporary function
    logger.warning("Temporary business deal cards used")
    import random
    for c in range(20):
        price = random.randrange(20,101,5)
        tariff = random.randrange(4,21,2)
        prod = random.randint(1,3)
        if prod == 1:
            goods = {"Food": random.randint(3,12)}
        elif prod == 2:
            goods = {"Luxuries": random.randint(3,12)}
        else:
            goods = {"Food": random.randint(3,12), "Luxuries": random.randint(3,12)}
        cards.append(BusinessDealCard(
            goods,
            price,
            {"A": tariff * 2, "B": tariff, "C": 0}
        ))

    return tuple(cards)

# ---------- References ----------- #
# Concepts
faction_play_order = ["Working Class", "Middle Class", "Capitalists", "State"]
faction_instantiate_order = ["Working Class", "Capitalists", "Middle Class", "State"]
phases = ['Preparation','Action','Production','Elections','Scoring']
industries = ['Healthcare','Education','Luxury','Agriculture','Media']

# Core Mechanics
unions = build_unions()
default_laws = build_laws()
voting_area = build_voting_area()

# Decks and Pools (Immutable)
company_decks = build_company_decks()
worker_pool = build_worker_pool()
immigration_cards = build_immigration_cards()
export_cards = build_export_cards()
political_agenda_cards = build_political_agenda_cards()
business_deal_cards = build_business_deal_cards()   

# Generic Resources 
default_resources = {
    "Food": 24,
    "Luxuries": 26,
    "Healthcare": 26,
    "Education": 26
}
default_election_cubes = {
    "Working Class": 25,
    "Middle Class": 25,
    "Capitalists": 25
}
default_influence = 35

# Faction Specific Resources
default_machinery_tokens = 6
default_strike_tokens = 7
default_storages = 6
default_legitimacy_tokens = {
    "Working Class": 6,
    "Middle Class": 6,
    "Capitalists": 6
}