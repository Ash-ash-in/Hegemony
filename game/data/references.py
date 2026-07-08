import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass, field


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

def build_worker_pool(self):
    logger.debug("Building worker pool")
    from game.data.classes import industries
    worker_pool = {'Working Class':[], 'Middle Class':[]}

    # skilled workers
    for skill in industries:
        for i in range(5):
            worker_pool['Working Class'].append(Worker(
                'Working Class',
                skill,
                False # Committed
            ))
                
    # unskilled workers            
    for i in range(23): # double check unskilled worker count
        worker_pool['Working Class'].append(Worker(
            'Working Class',
            'Unskilled',
            False # Committed
        ))   
            
    # middle class workers

    # skilled workers
    for skill in industries:
        for i in range(5): 
            worker_pool['Middle Class'].append(Worker(
                'Middle Class',
                skill,
                False # Committed
            ))
    # unskilled workers            
    for i in range(17): # double check unskilled worker count
        worker_pool['Middle Class'].append(Worker(
            'Middle Class',
            'Unskilled',
            False # Committed
        ))

    self.worker_pool = worker_pool        
    logging.debug(f"Worker setup complete. Worker count: {len(worker_pool['Working Class']) + len(worker_pool['Middle Class'])}")
    
def build_immigration_cards(self):
    logger.debug("(Re)building immigration card deck")
    from game.data.classes import industries, ImmigrationCard
    from random import shuffle
    immigration_cards = []
    for industry in industries:
        for i in range(3):
            if i < 2:
                immigration_cards.append(ImmigrationCard(
                    Worker('Working Class', industry, False),
                    Worker('Middle Class', 'Unskilled', False)
                ))
            immigration_cards.append(ImmigrationCard(
                Worker('Working Class', 'Unskilled', False),
                Worker('Middle Class', industry, False)
            ))
    shuffle(immigration_cards)
    self.immigration_card_deck = immigration_cards
    return immigration_cards
