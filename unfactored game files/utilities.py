import logging
import exceptions
import math


def round_up(n, decimals=0):
    """
    Round a number up to a given precision in decimal digits (default 0 digits).

    Arguments:
    n: the number to be rounded (float)
    decimals: the number of decimal digits to round to (int, default 0)

    Returns:
    The rounded number (float).
    """
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier



def find_worker(Game, faction, skill, in_play = 'Yes', exceptions = [], company = None):
    """
    faction: which class' workers are you looking for?
    skill: required skill, 'Any' if it doesn't matter
    in_play: 'No' for finding off-board workers, 'Any' is for setup only    
    company: enter a company object to restrict search to those employed at a specific place. None will search those without a company
    exceptions: list of workers to ignore in the search
    """

    logging.debug(f"Searching for worker with criteria: faction = {faction}, skill = {skill}, in_play = {in_play}, company = {company if company else 'None'}")
    
    if faction == 'WC':
        search_dict = 'WC_workers'
    elif faction == 'MC':
        search_dict = 'MC_workers'
    else:
        search_dict = 'Both'
    
    def search_loop(Game, active_dict) -> list:
        
        eligible_workers = []
        for ID, worker in Game.worker_pool[active_dict].items():
            
            # check exceptions
            if worker in exceptions:
                #logging.debug(f"Worker {worker} rejected due to exception rule")
                continue
            
            # check skill requirement
            if skill != 'Any' and worker.skill != skill:
                #logging.debug(f"Worker {worker} rejected due to skill requirement")
                continue
            
            # check in play requirement
            if in_play == 'Yes' and not worker.in_play:
                #logging.debug(f"Worker {worker} rejected due to in play requirement")
                continue
            elif in_play == 'No' and worker.in_play:
                #logging.debug(f"Worker {worker} rejected due to in play requirement")
                continue
            
            # check company requirement
            if company and worker.employer != company:
                #logging.debug(f"Worker {worker} rejected due to company requirement")
                continue
            elif not company and worker.employer:
                #logging.debug(f"Worker {worker} rejected due to company requirement")
                continue
            
            # add anyone left
            #logging.debug(f"Worker {worker} accepted")
            eligible_workers.append(worker)
            
        return eligible_workers
                
    # execute loop based on worker faction requirement
    if search_dict != 'Both':
        eligible_workers = search_loop(Game, search_dict)   
    else:
        eligible_workers = search_loop(Game, 'WC_workers') + search_loop(Game, 'MC_workers')
        
    logging.debug(f"Found {len(eligible_workers)} eligible workers")
    
    # handling if there are no eligible candidates
    if len(eligible_workers) == 0:
        logging.info('Failed to find any suitable candidates')
        return
    
    # dealing with 'any' skill - prioritise unskilled
    elif skill == 'Any':
        for candidate in eligible_workers:
            if candidate.skill == 'Unskilled':
                logging.debug(f"Worker search returning {candidate}")
                return candidate
            
    # return first worker in list
    logging.debug(f"Worker search returning {eligible_workers[0]}")
    return eligible_workers[0] 



def staff_from_abroad(Game, company, faction):
    logging.debug(f"Staffing {company} from abroad")
    """
    Finds the best workers to fill the slots of a company from those that are not currently in play.

    Arguments:
    Game: the game state (object)
    Company: the company to be staffed (object)
    Faction: the faction of the company (string) - 'WC' or 'MC'

    Returns: None if successful, or raises an exception if not.
    """


    # check all slots have available workers
    Failure = False
    candidates = {}
    for key, value in company.worker_slots.items():
        logging.debug(f"Finding slot {key}")
        try:
            worker = find_worker(Game, faction, value[0][1], 'No', list(candidates.values()))
        except:
            Failure = True
        else:
            candidates[key] = worker
                      
    if not Failure:
        logging.debug('All worker slots found, staffing company')
        for slot, worker in candidates.items():
            worker.birth_worker(Game)
            worker.assign_to_company(company, slot)
        return
                      
    else:
        logging.info('Unable to fill all slots of the company. Terminating staffing attempt')
        raise exceptions.NotEnoughWorkersError('Not enough workers available to fill all slots of the company')
    


def draw_immigration_card(Game, faction):
    """
    Draws an immigration card for the specified faction and moves the worker to in-play.
    
    faction: the faction to draw the card for (string) - 'WC' or 'MC'
    
    retuns: the updated immigration cards list.
    """
    logging.debug(f"Drawing immigration card for {faction}")
    
    # select first card, and put it to the back of the deck
    card = Game.immigration_cards[0]
    Game.immigration_cards.remove(card)
    Game.immigration_cards.append(card)
    
    # move worker to in-play
    worker = find_worker(Game, faction, card[faction], 'No')
    worker.birth_worker(Game)
    
    logging.debug("Immigration card drawn")
    return


# set up assignment function
def assign_company_to_slot(Game, company, slotname):
    """
    Assigns a company to a slot in the company_slots dictionary.
    This is used in setup, and when building a company.

    company: the company to be assigned (object)
    slotname: the name of the slot to be assigned to (string, found in company_slots dictionary)

    returns: None if successful, or raises an exception if not.
    """

    logging.debug(f"Assigning company {company.ID} to {slotname}")
    try:
        company.establish_company(Game, slotname)
        Game.company_slots[slotname] = company
        logging.info('Assignment successful')
        return
    except:
        logging.error('Failed to assign in company method. Failing function.')
        raise exceptions.CompanyAssignmentError('Failed to assign company to slot')
        