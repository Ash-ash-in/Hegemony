# import modules
import logging

### Main Functions ###
def instantiate_game(Game):
    """
    Sets up the game by instantiating allgame elements.
    It must be run before all other functions.

    returns: None
    """
    # Run instantiate functions to set up the game elements
    instantiate_trade_unions(Game)
    instantiate_workers(Game)
    instantiate_companies(Game)
    instantiate_company_slots(Game)
    instantiate_immigration_cards(Game)
    instantiate_players(Game)

    logging.info('Game instantiated')
    return

def setup_game(Game):
    """
    Sets up the game for the specified player count.
    This function must be run after instantiate_game().
    It sets up the game elements based on the player count, according to the default start position.

    Game: the game object containing the player count and other game elements.

    returns: None
    """
    # Run setup functions to set up the game elements
    setup_companies(Game)
    setup_workers(Game)

    logging.info('Game setup complete')
    return

### Instantiate Functions ###

def instantiate_trade_unions(Game):
    """
    Sets up trade unions for the game.
    It creates a list of trade unions, each represented by an object of the trade_union class.
    Each trade union has a name and an industry.

    returns: a list of trade union objects.
    """
    #import classes
    from classes import Trade_Union

    #setup objects
    healthcare_trade_union = Trade_Union('Healthcare Trade Union', 'Healthcare')
    education_trade_union = Trade_Union('Education Trade Union','Education')
    luxury_trade_union = Trade_Union('Luxury Trade Union','Luxury')
    agriculture_trade_union = Trade_Union('Agriculture Trade Union','Agriculture')
    media_trade_union = Trade_Union('Media Trade Union','Media')

    # create list
    trade_unions = [
        healthcare_trade_union, 
        education_trade_union, 
        luxury_trade_union, 
        agriculture_trade_union, 
        media_trade_union
    ]

    logging.debug('trade unions set up')
    Game.trade_unions = trade_unions
    return

def instantiate_workers(Game):
    """
    Sets up workers for the game. 
    It creates a pool of workers for both the working class and middle class,
    with a mix of skilled and unskilled workers.

    returns: a dictionary of worker pools.
    The keys are the worker pool names, and the values are dictionaries of Worker objects.
    """

    #import classes
    from classes import Worker    

    # working class workers
    worker_int = 1

    # skilled workers
    for union in Game.trade_unions:
        for i in range(5):
            
            workerID = 'WC_worker' + str(worker_int)
            
            if workerID in Game.worker_pool['WC_workers'].keys():
                logging.error('duplicate worker created:', workerID)
                print('Failed to complete worker setup: duplicate worker')
                break
                
            else:
                Game.worker_pool['WC_workers'][workerID] = Worker(
                    workerID, 
                    union.skill,
                    'WC'
                )
                
                worker_int += 1
                
    # unskilled workers            
    for i in range(23): # double check unskilled worker count
        
        workerID = 'WC_worker' + str(worker_int)
        
        if workerID in Game.worker_pool['WC_workers'].keys():
            logging.error('duplicate worker created:', workerID)
            print('Failed to complete worker setup: duplicate worker')
            break
            
        else:
            Game.worker_pool['WC_workers'][workerID] = Worker(
                workerID, 
                'Unskilled',
                'WC'
            )   
            worker_int += 1
            
    # middle class workers
    worker_int = 1

    # skilled workers
    for union in Game.trade_unions:
        for i in range(5):
            
            workerID = 'MC_worker' + str(worker_int)
            
            if workerID in Game.worker_pool['MC_workers'].keys():
                logging.error('duplicate worker created:', workerID)
                print('Failed to complete worker setup: duplicate worker')
                break
                
            else:
                Game.worker_pool['MC_workers'][workerID] = Worker(
                    workerID, 
                    union.skill,
                    'MC'
                )
                worker_int += 1
                
    # unskilled workers            
    for i in range(17): # double check unskilled worker count
        
        workerID = 'MC_worker' + str(worker_int)
        
        if workerID in Game.worker_pool['MC_workers'].keys():
            logging.error('duplicate worker created:', workerID)
            print('Failed to complete worker setup: duplicate worker')
            break
            
        else:
            Game.worker_pool['MC_workers'][workerID] = Worker(
                workerID, 
                'Unskilled',
                'MC'
            )
            worker_int += 1
            
    logging.debug(f"Worker initialization complete. Worker count: {len(Game.worker_pool['WC_workers']) + len(Game.worker_pool['MC_workers'])}")
    return

def instantiate_companies(Game):
    """
    Creates a pool of companies for the game.
    The pool is a dictionary with four keys: 'WC_companies', 'MC_companies', 'CC_companies', and 'State_companies',
    each containing a dictionary of companies.
    Each company is represented by an object of the Company class.
    The companies are read from a CSV file, and the setup is done based on the faction of the company.
    
    returns: a dictionary of company pools.
    The keys are the company pool names, and the values are dictionaries of Company objects.
    """

    # Imports
    from classes import Company
    import pandas as pd
    import os
    cwd = os.getcwd()

    companies_df = pd.read_csv(cwd+"\Hegemony Companies.csv")


    def company_setup(faction):
        """
        Sets up companies for the game.
        It creates a dictionary of companies for each of the working class, middle class, capitalists, and state.
        These make up the company pool dictionary.

        Arguments:
        faction: the faction of the company (string) - 'WC', 'MC', 'CC', or 'State'

        Returns: None
        It modifies the company pool in place.
        """
        if faction == 'WC':
            csv_faction = 'Working Class'
        elif faction == 'MC':
            csv_faction = 'Middle Class'
        elif faction == 'CC':
            csv_faction = 'Capitalists'
        elif faction == 'State':
            csv_faction = 'State'
        
        company_dict = {}
        company_int = 1
        for index, row in companies_df[companies_df['Owner'] == csv_faction].iterrows():
            companyID = faction +'_company' + str(company_int)

            if companyID in company_dict.keys():

                # duplicate error handling
                logging.error('Error in company setup, duplicate company created: ' + companyID)

            else: 
                # extract complex parts
                # wages
                if not pd.isna(row['L1']):
                    wages = (int(row['L1']), int(row['L2']), int(row['L3']))
                else:
                    wages = None
                    
                # worker slots
                if pd.isna(row['Class1']):
                    worker_slots = None
                else:
                    worker_slots = {}
                if not pd.isna(row['Class3']):
                    worker_slots['S3'] = [(row['Class1'], row['Skill1']), None]
                if not pd.isna(row['Class2']):
                    worker_slots['S2'] = [(row['Class2'], row['Skill2']), None]
                if not pd.isna(row['Class1']):
                    worker_slots['S1'] = [(row['Class1'], row['Skill1']), None]

                # set up object    
                company_dict[companyID] = Company(
                    companyID,
                    row['Owner'],
                    row['Name'],
                    row['Cost'],
                    row['Product'],
                    row['Base Production'],
                    wages,
                    worker_slots,
                    row['Upgrade Value']
                )
                company_int += 1
                
        return company_dict
            

    Game.company_pool = {
        'WC_companies':company_setup('WC'), 
        'MC_companies':company_setup('MC'), 
        'CC_companies':company_setup('CC'), 
        'State_companies':company_setup('State')
    }

    logging.debug('company_pool created')
    return

#set up company slot dict
def instantiate_company_slots(Game):
    """
    Creates the company slots for the game.

    Arguments:
    Game: the game object containing the company slots.

    Retruns: None
    """

    for i in range(12):
        Game.company_slots['CC_company_slot' + str(i + 1)] = None
        Game.company_slots['State_company_slot' + str(i + 1)] = None
        if i < 2:
            Game.company_slots['WC_company_slot' + str(i + 1)] = None
        if i < 8:
            Game.company_slots['MC_company_slot' + str(i + 1)] = None    
    return


def instantiate_immigration_cards(Game):
    """
    Creates and shuffles the immigration cards for the game.
    The cards read the industries from the trade unions and create a list of cards.
    Each card has a 'WC' and 'MC' key, and a skill value.
    The cards are shuffled to randomize the order.

    Arguments:
    Game: the game object containing the trade unions.
    
    Returns: None
    """
    # Imports
    import random

    # setup immigration cards

    for union_name in Game.trade_unions:
        for i in range(3):
            if i < 2:
                Game.immigration_cards.append({'WC':union_name.industry, 'MC':'Unskilled'})
            Game.immigration_cards.append({'MC':union_name.industry, 'WC':'Unskilled'})
            
    random.shuffle(Game.immigration_cards)
    return 

def instantiate_players(Game):
    """
    Creates the players for the game.
    The players are represented by a list of player objects.

    Arguments:
    Game: the game object containing the player count.

    Returns: None
    It modifies the players in place.
    """
    # Imports
    from classes import WorkingClass, MiddleClass, CapitalistClass, StateClass

    # Setup players
    player_dict = {'WC':WorkingClass(), 'CC':CapitalistClass()}
    if Game.player_count > 2:
        player_dict['MC'] = MiddleClass()
    if Game.player_count > 3:
        player_dict['State'] = StateClass()
    Game.players = player_dict
    logging.info('Players instantiated')
    return
    
def instantiate_laws(Game):
    """
    Creates the laws for the game.
    The laws are represented by a dict of {ID: Law objects}.

    Arguments:
    Game: the game object

    Returns: None
    It modifies the laws in place.
    """
    # Imports
    from classes import Law

    # Setup laws
    Game.laws = {
        1: Law(1, 'Fiscal Policy', 'C'),
        2: Law(2, 'Labour Market', 'B'),
        3: Law(3, 'Taxation', 'A'),
        4: Law(4, 'Welfare State: Healthcare & Benefits', 'B'),
        5: Law(5, 'Welfare State: Education', 'C'),
        6: Law(6, 'Foreign Trade', 'B'),
        7: Law(7, 'Immigration', 'B')
    }
    
    logging.info('Laws instantiated with default positions')
    return




### Setup Functions ###
## For the default start position ##


def setup_workers(Game):
    """
    Sets up workers for the game start position.
    It assigns workers to companies based on the player count and the type of companies.
    
    Arguments:
    Game: the game object containing the player count and company slots.
    
    Returns: None
    It modifies the workers and companies in place.
    """

    from utilities import staff_from_abroad, find_worker, draw_immigration_card

    ### Working Class
    
    # define companies to assign workers to (dependant on player count) and draw immigration cards
    if Game.player_count == 2:
        WC_setup = ['Supermarket', 'Shopping Mall' ,'Public Hospital', 'Public University']
        draw_immigration_card('WC')
        
    elif Game.player_count > 2:
        WC_setup = ['Supermarket', 'College', 'University Hospital']
        draw_immigration_card(Game, 'WC')
        draw_immigration_card(Game, 'WC')
    else:
        raise ValueError('Invalid player count. Must be 2 or more.')

    # assign workers to companies
    for company in Game.company_slots.values():
        if not company:
            continue
        if company.name in WC_setup:
            logging.debug(f"Executing worker setup for {company.name}")
            staff_from_abroad(Game, company, 'WC')
            WC_setup.remove(company.name)
            
    # spawn one worker in unemployment area        
    find_worker(Game, 'WC', 'Any', 'No').birth_worker(Game)   


    ### Middle Class
    if Game.player_count > 2:
        MC_setup = ['Technical University', 'Shopping Mall'] 
        MC_setup2 = ['Convenience Store', "Doctor's Office"]
        for company in Game.company_slots.values():
            if not company:
                continue
            if company.name in MC_setup:
                logging.debug(f"Executing worker setup for {company.name}")
                staff_from_abroad(Game, company, 'MC')
                MC_setup.remove(company.name)
            elif company.name in MC_setup2:
                logging.debug(f"Executing worker setup for {company.name}")
                worker = find_worker(Game, 'MC', company.worker_slots['S1'][0][1], 'No')
                worker.birth_worker(Game)
                worker.assign_to_company(company, 'S1')
                MC_setup2.remove(company.name)
                
        skill = 'Luxury'
        print('MC picked Luxury as their setup worker skill. This needs to be changed to a player input.')
        # skill = str(input('Middle Class Player: pick a skilled worker to add to the unemployment area')).strip().capitalize()
        # while skill not in ['Agriculture', 'Luxury', 'Healthcare', 'Education', 'Media']:
        #     skill = str(input('Input not understood, try again')).strip().capitalize()
        find_worker(Game, 'MC', skill, 'No').birth_worker(Game)
        
        draw_immigration_card(Game, 'MC')
        draw_immigration_card(Game, 'MC')

    logging.info("Worker setup complete")
                   
    return


def setup_companies(Game):
    """
    Sets up companies for the game start position.
    It assigns companies to slots in the company_slots dictionary.
    The setup is based on the player count and the type of companies.

    Game: the game object containing the company pool and company slots.

    returns: None
    It modifies the company slots in place.
    """
    logging.info('Starting company setup')
    from utilities import assign_company_to_slot
    
    # set up capitalist companies
    CC_setup = ['Supermarket', 'Shopping Mall', 'College', 'Clinic']
    for company in Game.company_pool['CC_companies'].values():
        if company.name in CC_setup:
            logging.debug(f"Setting up {company.name}")
            slotname = 'CC_company_slot' + str(5 - len(CC_setup))
            assign_company_to_slot(Game, company, slotname)
            CC_setup.remove(company.name)

    # set up state companies
    if Game.player_count == 2:
        State_setup = ['Regional TV Station', 'Public Hospital', 'Public University']
    elif Game.player_count > 2:
        State_setup = ['Technical University', 'University Hospital', 'National Public Broadcasting']
    for company in Game.company_pool['State_companies'].values():
        if company.name in State_setup:
            logging.debug(f"Setting up {company.name}")
            slotname = 'State_company_slot' + str(4 - len(State_setup))
            assign_company_to_slot(Game, company, slotname)
            State_setup.remove(company.name)    

    # setup middle class companies
    if Game.player_count > 2:
        MC_setup = ['Convenience Store', "Doctor's Office"]
        for company in Game.company_pool['MC_companies'].values():
            if company.name in MC_setup:
                logging.debug(f"Setting up {company.name}")
                slotname = 'MC_company_slot' + str(3 - len(MC_setup))
                assign_company_to_slot(Game, company, slotname)
                MC_setup.remove(company.name)    

    logging.info('Company Setup Complete')
    return

def setup_players(Game):
    """
    Sets up players for the game start position.
    It assigns players to the game based on the player count.

    Game: the game object containing the player count and players.

    returns: None
    It modifies the players in place.
    """
    logging.info('Starting player setup')


    