# import modules
import logging
import exceptions

# Games State
class GameState:
    def __init__(self):
        self.player_count = None # int: How many players are in the game?
        self.players = {} # dict: All player objects
        self.current_player = 0 # int: Which player is currently active?
        self.game_over = False # bool: Is the game over?
        self.round_number = 1 # int: Which round is it?
        self.turn_number = 1 # int: Which turn is it (for the action phase)?
        self.worker_pool = {'WC_workers':{}, 'MC_workers':{}} # dict: The reference for all workers in the game
        self.trade_unions = [] # list: The trade union objects
        self.company_dict = {} # dict: The reference for all companies in the game
        self.company_pool = {} # dict: The reference for all companies in the game
        self.company_slots = {} # dict: The reference for all company slots on the board
        self.immigration_cards = [] # list: The immigration cards
        self.CC_market = [] # list: The market for the capitalist class
        self.state_legitimacy = {} # dict: The state legitimacy for each class
        self.state_trade_goods = {} # dict: The state resources for each class
        self.laws = {} # dict: The laws in the game, with their respective positions


# LAWS
class Law:
    def __init__(self, ID, name, position, proposition = None):
        self.__ID = ID # str: Unique ID
        self.__name = name # str: Name of the law
        self.__position = position # int: Position of the law in the game
        self.__proposition = proposition # str: The current proposition to change the law, if any

    def __repr__(self):
        return f"Law({self.__ID}, Name: {self.__name}, Position: {self.__position}, Proposition: {self.__proposition if self.__proposition else 'None'})"
    
    def propose_law(self, Game, proposition):
        """
        Proposes a law change.
        This is used to propose a law change, and sets the proposition to the given value.
        
        Game: the game object (GameState) to propose the law in.
        proposition: the new proposition for the law (str)
        
        return value: None if successful, raises an error if it fails.
        """
        logging.debug(f"Proposing law {self.__ID} with proposition '{proposition}'")
        if self.__proposition:
            logging.error('Law already has a proposition, cannot propose again')
            raise exceptions.ClassMethodFailure('Law already has a proposition, cannot propose again')
        elif self.__position == proposition:
            logging.error('Law is already in the proposed position, cannot propose again')
            raise exceptions.ClassMethodFailure('Law is already in the proposed position, cannot propose again')
        else:
            self.__proposition = proposition
            Game.laws[self.__ID] = self
            logging.debug('Law proposed successfully')
            return
        
    def change_law(self, Game, proposition):
        """
        Changes the position of the law.
        This is used to change the position of the law to the proposed position.
        It unsets the proposition afterwards.

        Game: the game object (GameState) to change the law in.
        propositio: the new position for the law (int)
        
        return value: None if successful, raises an error if it fails.
        """
        logging.debug(f"Changing law {self.__ID} position to {proposition}")
        if not self.__proposition:
            logging.error('Law has no proposition, cannot change position')
            raise exceptions.ClassMethodFailure('Law has no proposition, cannot change position')
        elif self.__position == proposition:
            logging.error('Law is already in the proposed position, cannot change position')
            raise exceptions.ClassMethodFailure('Law is already in the proposed position, cannot change position')
        else:
            self.__position = proposition # Set the new position
            self.__proposition = None # Unset the proposition
            Game.laws[self.__ID] = self
            logging.debug('Law position changed successfully')
            return
        
    def remove_proposition(self, Game):
        """
        Removes the proposition from the law.
        This is used to remove the proposition from the law, and does not change the position of the law.

        Game: the game object (GameState) to remove the proposition from.

        return value: None if successful, raises an error if it fails.
        """
        logging.debug(f"Removing proposition from law {self.__ID}")
        if not self.__proposition:
            logging.error('Law has no proposition, cannot remove')
            raise exceptions.ClassMethodFailure('Law has no proposition, cannot remove')
        else:
            self.__proposition = None
            Game.laws[self.__ID] = self
            logging.debug('Proposition removed successfully')
            return


# WORKER

class Worker:
    def __init__(self, ID, skill, faction, employer = None, in_play = False):
        self.__ID = ID # str: Unique ID
        self.__skill = skill # str: What profession is it?
        self._faction = faction # str: What player owns this worker?
        self._employer = employer # classObj: What company is it assigned to?
        self._in_play = in_play # bool: True - on the board, False - off the board
        
    @property
    def ID(self):
        return self.__ID
    
    @property
    def skill(self):
        return self.__skill
    
    @property
    def faction(self):
        return self._faction
    
    @property
    def employer(self):
        return self._employer
    
    @property
    def company(self):
        return self._employer
    
    @property
    def in_play(self):
        return self._in_play
    
    def assign_to_company(self, company, slotname):
        """
        Assigns a worker to a company.
        This is the main function for assigning a worker to a company.
        It does not check costs or trade union validation, as it is assumed that this is done before calling this function.
        
        company: the company to be assigned to (object)
        slotname: the name of the slot to be assigned to (string, found in company_slots dictionary)
        """
        logging.info(f"Assigning {self.__ID} to {company.ID}")
        if not self._in_play:
            logging.error(f"Worker {self.__ID} not in play, cannot assign to {company.ID}")
            raise exceptions.WorkerNotInPlayError(f"Worker {self.__ID} not in play, cannot assign to {company.ID}")
        if self._employer:
            logging.error(f"Error assigning {self.__ID} to {company.ID}: worker already employed")
            raise exceptions.WorkerAlreadyEmployedError(f"Error assigning {self.__ID} to {company.ID}: worker already employed")
        try: 
            company.add_worker(self, slotname)
            self._employer = company
            logging.debug("Worker successfully assigned")
            return
        except:
            logging.error("Failed to add worker to company, worker-side assignment also failed")
            raise exceptions.ClassMethodFailure("Failed to add worker to company, company-side assignment also failed")
        
        
    def unassign_from_company(self, company):
        """
        Unassigns a worker from a company.
        This is the main function for unassigning a worker from a company.
        It does not check costs or trade union validation, as it is assumed that this is done before calling this function.
        
        company: the company to be unassigned from (object)
        """
        logging.debug(f"Unassigning {self.__ID} from {company.ID}")
        if self.employer != company:
            logging.error(f"Unable to unassign {self.__ID} from {company.ID}: worker is not employed here (missing in worker object)")
            raise exceptions.WorkerNotEmployedError(f"Unable to unassign {self.__ID} from {company.ID}: worker is not employed here (missing in worker object)")
        
        if self not in company.workers:
            logging.error(f"Unable to unassign {self.__ID} from {company.ID}: worker is not employed here (missing in company object)")
            raise exceptions.WorkerNotInCompanyError(f"Unable to unassign {self.__ID} from {company.ID}: worker is not employed here (missing in company object)")
        
        try:
            company.remove_worker(self)
            self._employer = None
            logging.debug('Worker successfully unassigned')
            return
        except:
            logging.error("Failed to remove worker from company, worker-side unassignment also failed")
            raise exceptions.ClassMethodFailure("Failed to remove worker from company, worker-side unassignment also failed")
        
        
    def birth_worker(self, Game):
        logging.debug(f"Birthing worker {self.__ID}")
        if self._in_play:
            logging.error(f"Worker already in play, cannot birth")
            raise exceptions.WorkerAlreadyInPlayError(f"Worker already in play, cannot birth")
        else:
            self._in_play = True
            Game.players[self._faction].add_worker()
            logging.debug(f"Worker birthed")
            

    def kill_worker(self, Game):
        logging.debug(f"Killing {self.__ID}")
        if self._employer:
            logging.error('Worker is currently employed, cannot kill')
            raise exceptions.WorkerAlreadyEmployedError('Worker is currently employed, cannot kill')
        if not self._in_play:
            logging.error(f"Worker not in play, cannot kill")
            raise exceptions.WorkerNotInPlayError(f"Worker not in play, cannot kill")
        else:
            self._in_play = False
            Game.players[self._faction].remove_worker()
            logging.debug(f"Worker {self.__ID} killed")
            
        
    def __repr__(self):
        return f"Worker({self.__ID}, Skill: {self.__skill}, Class: {self._faction}, Employer: {self._employer if self._employer else 'None'})"
    



# TRADE UNIONS

class Trade_Union:
    def __init__(self, name, skill, worker = None):
        self.__name = name # str
        self.__skill = skill # str
        self._worker = worker # classObj
        
    @property
    def skill(self):
        return self.__skill
    
    @property
    def industry(self):
        return self.__skill
    
    @property
    def worker(self):
        return self._worker
    
    def add_worker(self, workerobj):
        """
        Adds a worker to the trade union.
        Does not check legitimacy of the addition, as it is assumed that this is done before calling this function.
        """
        logging.debug(f"Adding {workerobj.name} to {self.__name}")
        if self._worker:
            logging.error("Cannot add worker, slot already occupied")
            raise exceptions.WorkerSlotOccupiedError('Cannot add worker, slot already occupied')
        if workerobj.skill != self.__skill:
            logging.error("Cannot add worker, incorrect skill")
            raise exceptions.WorkerSlotNotAppropriateError('Cannot add worker, incorrect skill')
        if workerobj.faction != 'WC':
            logging.error('Cannot add worker, incorrect faction')
            raise exceptions.WorkerSlotNotAppropriateError('Cannot add worker, incorrect faction')
        
        logging.debug(f"Worker {workerobj.name} added to {self.__name}")
        self._worker = workerobj
            



# COMPANIES

class Company:
    def __init__(self, ID, owner, name, cost, product, base_production, wages = None, worker_slots = None, upgrade_value = None, upgraded = False, workers = None, company_slot = None):
        self.__ID = ID
        self._owner = owner
        self.__name = name
        self.__cost = cost
        self.__product = product
        self.__base_production = base_production
        self.__wages = wages
        self._worker_slots = worker_slots # for real use
        self.__upgrade_value = upgrade_value
        self._upgraded = upgraded
        self._workers = workers # for ease of access
        self._company_slot = company_slot
        if self._upgraded:
            self._production_amount = self.__base_production + self._upgrade_value
        else:
            self._production_amount = self.__base_production
        self._location = None
    
    @property
    def ID(self):
        return self.__ID
    
    @property
    def owner(self):
        return self._owner
        
    @property
    def name(self):
        return self.__name
        
    @property
    def cost(self):
        return self.__cost
        
    @property
    def product(self):
        return self.__product
        
    @property
    def base_production(self):
        return self.__base_production
        
    @property
    def wages(self):
        return self.__wages
        
    @property
    def worker_slots(self):
        return self._worker_slots
        
    @property
    def upgrade_value(self):
        return self.__upgrade_value
        
    @property
    def upgraded(self):
        return self._upgraded
        
    @property
    def production(self):
        return self._production_amount
        
    @property
    def production_amount(self):
        return self._production_amount
    
    @property
    def workers(self):
        return self._workers
    
    @property
    def location(self):
        return self._location
    
    def __repr__(self):
        return f"Company({self.__ID}, Name: {self.__name}, Product: {self.__product}, Location: {self._location if self._location else 'None'})"
    
    def remove_worker(self, worker):
        """
        Removes a worker from the company.
        It does not check if the worker is in play, or any other worker attributed, as it is assumed that this is done before calling this function.
        
        worker: the worker to be removed (object)

        return value: None if successful, raises an error if it fails.
        """
        logging.debug(f"Removing {worker.ID} from {self.__ID} (company method)")
        # checks
        try: # throw error if we can't find that worker at this company
            self._workers.index(worker)
        except (ValueError, AttributeError):
            logging.error(f"Worker {worker.ID} not assigned to {self.__ID}, cannot remove")
            raise exceptions.WorkerNotInCompanyError(f"Worker {worker.ID} not assigned to {self.__ID}, cannot remove")

        # remove from worker list
        if len(self._workers) == 1:
            self._workers = None
        else:
            self._workers.remove(worker)   
        
        # remove worker from slots
        found = False
        for slot in self._worker_slots.values():
            if slot[1] == worker:
                slot[1] = None
                found = True
                break
        if not found:
            logging.error(f"Could not find worker {worker.ID} in company's worker slots. Something is broken.")
            raise exceptions.ClassMethodFailure(f"Could not find worker {worker.ID} in company's worker slots. Something is broken.")
        logging.debug(f"Worker removal successful (company method complete)")
        return
        
    def add_worker(self, worker, slotname):
        """
        Adds a worker to the company.
        It does not check if the worker is in play, as it is assumed that this is done before calling this function.
        
        worker: the worker to be added (object)
        slotname: the name of the slot to be added to (string, found in company_slots dictionary)

        return value: None if successful, raises an error if it fails.
        """
        
        logging.debug(f"Adding {worker.ID} to {self.__ID} (company method)")
        
        #checks
        if worker.employer:
            logging.error("Error adding worker, already employed")
            raise exceptions.WorkerAlreadyEmployedError("Error adding worker, already employed")
        try:
            self._worker_slots[slotname]
        except:
            logging.error(f"Error adding worker, slot '{slotname}' does not exist")
            raise exceptions.WorkerSlotNotFoundError(f"Error adding worker, slot '{slotname}' does not exist")
        try:
            if worker in self._workers:
                logging.error(f"Error adding worker, worker already employed here")
                raise exceptions.WorkerAlreadyEmployedError(f"Error adding worker, worker already employed here")
        except:
            pass
        if self._worker_slots[slotname][1]:
            logging.error(f"Error adding worker, slot '{slotname}' already occupied")
            raise exceptions.WorkerSlotOccupiedError(f"Error adding worker, slot '{slotname}' already occupied")
        if worker.faction != self.worker_slots[slotname][0][0] and self.worker_slots[slotname][0][0] != 'Any':
            logging.error(f"Error adding worker, '{worker.faction}' is not an appropriate faction")
            raise exceptions.WorkerSlotNotAppropriateError(f"Error adding worker, '{worker.faction}' is not an appropriate faction")
        if worker.skill != self.worker_slots[slotname][0][1] and self.worker_slots[slotname][0][1] != 'Any':
            logging.error(f"Error adding worker, '{worker.skill}' is not an appropriate skill")
            raise exceptions.WorkerSlotNotAppropriateError(f"Error adding worker, '{worker.skill}' is not an appropriate skill")
        if not self._location:
            logging.error(f"Error adding worker, company not established")
            raise exceptions.CompanyNotEstablishedError(f"Error adding worker, company not established")
    
        # adding worker to list
        if not self._workers:
            self._workers = []
        self._workers.append(worker)
        logging.debug("Worker added to worker list")
        
        # adding worker to slot
        self._worker_slots[slotname][1] = worker        
        logging.debug("Worker added to slot")
            
        logging.debug("Worker successfully added (company method complete)")
        return True
    
    def establish_company(self, Game, company_slot):
        """
        Establishes a company in the specified slot. This is used in setup, and when building a company.
        This does not consider the cost of establishing a company.

        company_slot: the name of the slot to be established in (string, found in company_slots dictionary)

        return value: None if successful, raises an error if it fails.
        It does not affect the company_slots dictionary.
        """

        logging.debug(f"Establishing company {self.__ID} in {company_slot} (company method)")

        if Game.company_slots[company_slot]:
            logging.error('Error establishing company, slot already occupied')
            raise exceptions.CompanySlotOccupiedError('Error establishing company, slot already occupied')
        elif self._location:
            logging.error('Error establishing company, company already established')
            raise exceptions.CompanyAlreadyEstablishedError('Error establishing company, company already established')
        else:
            self._location = company_slot
            logging.debug('Company established')
            return
            


class Player():
    
    def __init__(self):
        self._money = 0
        self._victory_points = 0
        self._loans = 0
        self._faction = 'None'

    @property
    def faction(self):
        return self._faction
    
    @property
    def money(self):
        return self._money
    
    @property
    def victory_points(self):
        return self._victory_points
    
    @property
    def loans(self):
        return self._loans
        
    def add_victory_points(self, amount):
        logging.debug(f"Adding {amount} victory points to {self._faction}")
        self._victory_points += amount
        
    def receive_money(self, amount):
        logging.debug(f"Adding ${amount} to {self._faction}")
        if amount <= 0:
            logging.error('Failed to add money - amount cannot be less than 0')
            raise exceptions.ValueError('Failed to add money - amount cannot be less than 0')
        else:
            self._money += amount
            
    def pay_money(self, amount, mandatory = False):
        logging.debug(f"Removing ${amount} from {self._faction}")
        if amount <= self._money:
            self._money -= amount
        elif not mandatory:
            logging.debug('Not enough money to make payment')
            raise exceptions.ValueError('Not enough money to make payment')
        elif mandatory:
            logging.debug('Not enough money for mandatory payment, loan required')
            self._money -= amount
            while self._money < 0:
                self.take_loan()
            
    def take_loan(self):
        logging.debug(f"{self._faction} taking a loan")
        self._loans += 1
        self.receive_money(50)
        return
    
    def repay_loan(self):
        logging.debug(f"{self._faction} repaying a loan")
        if self._loans == 0:
            logging.error('No loans to repay')
            raise exceptions.ClassMethodFailure('No loans to repay')
        elif self._money < 50:
            logging.error('Not enough money to repay loan')
            raise exceptions.ClassMethodFailure('Not enough money to repay loan')
        else:
            self._money -= 50
            if self._loans == 1:
                self._loans = 0
                logging.debug(f"Loan repaid, no loans remaining")
            else:
                self._loans -= 1
                logging.debug(f"Loan repaid, {self._loans} remaining")
        return
    
    def pay_loan_interest(self):
        logging.debug(f"{self._faction} paying loan interest")
        if self._loans == 0:
            logging.error('No loans to repay')
            raise exceptions.ClassMethodFailure('No loans to repay')
        elif self._money < 5 * self._loans:
            logging.error('Not enough money to pay loan interest')
            self._money -= 5 * self._loans
            while self._money < 0:
                self.take_loan()
            logging.debug('Loan taken to pay interest')
            return
        else:
            self._money -= 5 * self._loans
            return

        
class WorkingClass(Player):
    
    ### Setup the class variables for the working class
    def __init__(self):
        super().__init__()
        self._faction = 'WC'
        self._prosperity = 0
        self._worker_count = 0
        self._resources = {}
        self._population = self.population_calc()

    @property
    def worker_count(self):
        return self._worker_count
    
    @property
    def population(self):
        return self._population
    
    @property
    def prosperity(self):
        return self._prosperity
    
    @property
    def resources(self):
        return self._resources
    
    def add_worker(self):
        """
        Adds a worker to the working class.
        This is used when a new worker is created, and adds it to the working class.

        Arguments:
        None

        Returns:
        None if successful, raises an error if it fails.
        """
        logging.debug(f"Adding worker to {self._faction}")
        self._worker_count += 1
        self._population = self.population_calc()
        return
        
    ### Worker-related methods
    def population_calc(self):
        logging.debug(f"Recalculating population for {self._faction}")
        if self._worker_count < 30 and self._worker_count > 9:
            population = self._worker_count // 3
        elif self._worker_count >= 30:
            population = 10
        else:
            population = 3
        return population

    def record_workers(self, Game):
        """
        Records the number of workers in the game.
        This is used whenever the worker count changes, and keeps the population tracker up to date.

        Arguments:
        Game: the game object (GameState) to record the workers in.

        Returns:
        None if successful, raises an error if it fails.
        """
        # Scan all workers and count them if in play
        logging.debug(f"Recording workers for {self._faction}")
        self._worker_count = 0
        for worker in Game.worker_pool[self._faction]:
            if worker.in_play:
                self._worker_count += 1

        # Check if there are any workers in play
        if self._worker_count <= 0:
            logging.error('No workers found while recording.')
            raise exceptions.WorkerNotInPlayError('No workers in play, cannot record')
        
        self._population = self.population_calc(self._worker_count)
        return

    ### Scoring methods              
    def add_prosperity(self):
        """
        Adds prosperity to the working class.
        It adds one point of prosperity, and then adds the prosperity to the victory points."""
        logging.debug('Adding WC prosperity')      
        if self._prosperity < 10:
            self._prosperity += 1
        elif self._prosperity > 10:
            raise exceptions.ProsperityTooHighError('Prosperity cannot be greater than 10')
        self.add_victory_points(self._prosperity)
                      
    def drop_prosperity(self):
        logging.debug('Dropping WC prosperity')     
        if self._prosperity < 0:
            self._prosperity -= 1


    ### Resource methods
    def receive_resource(self, resource, amount):
        if resource not in self._resources.keys():
            logging.error(f"Resource {resource} not found")
            raise exceptions.ResourceNotFoundError(f"Resource {resource} not found")
        if amount <= 0:
            logging.error('Failed to add resource - amount cannot be less than 0')
            raise exceptions.ValueError('Failed to add resource - amount cannot be less than 0')
        else:
            self._resources[resource] += amount
            logging.debug(f"Added {amount} {resource} to {self._faction}")
            return
        
    def spend_resource(self, resource, amount):
        if resource not in self._resources.keys():
            logging.error(f"Resource {resource} not found")
            raise exceptions.ResourceNotFoundError(f"Resource {resource} not found")
        if amount <= 0:
            logging.error('Failed to remove resource - amount cannot be less than 0')
            raise exceptions.ValueError('Failed to remove resource - amount cannot be less than 0')
        elif amount > self._resources[resource]:
            logging.error('Failed to remove resource - not enough resources')
            raise exceptions.ValueError('Failed to remove resource - not enough resources')
        else:
            self._resources[resource] -= amount
            logging.debug(f"Removed {amount} {resource} from {self._faction}")
            return

    
class MiddleClass(WorkingClass):
    
    def __init__(self):
        super().__init__()
        self._faction = 'MC'
        self._population = self.population_calc()
        self._trade_goods = {}
        self._prices = {}
        self._storage = {}

    @property
    def trade_goods(self):
        return self._trade_goods
    
    @property
    def prices(self):
        return self._prices
    
    @property
    def storage(self):
        return self._storage
        
    prosperity_tracker = [0,1,2,3,4,5,5,6,6,7,7]
        
    def add_prosperity(self):
        logging.debug('Adding MC prosperity')
        if self._prosperity_position + 1 > 10:
            self._prosperity_position = 10
        else:
            self._prosperity_position += 1
        self._prosperity = self.prosperity_tracker[self._prosperity_position]
        self.add_victory_points(self._prosperity)
        
    def drop_prosperity(self):
        logging.debug('Dropping MC prosperity')
        if self._prosperity_position > 0:
            self._prosperity_position -= 1
        self._prosperity = self.prosperity_tracker[self._prosperity_position]
        
class CapitalistClass(Player):
                      
    def __init__(self):
        super().__init__()
        self._faction = 'CC'
        self._trade_goods = {}
        self._prices = {}              
        self._storage = {}
        self._revenue = 0
        self._capital = 0
        self._income_tracker = 0
        self._company_count = 0
        self._market = [] # list: The market is a list of company objects

    @property
    def trade_goods(self):
        return self._trade_goods
    
    @property
    def prices(self):
        return self._prices
    
    @property
    def storage(self):
        return self._storage
    
    @property
    def revenue(self):
        return self._revenue
    
    @property
    def capital(self):
        return self._capital
    
    @property
    def company_count(self):
        return self._company_count
    
    @property
    def market(self):
        return self._market

    def refresh_money(self):
        """
        Refreshes the money for the capitalist class.
        This is used after each transation, and adds the income to the money.
        """
        logging.debug(f"Refreshing money for {self._faction}")
        self._money = self._revenue + self._capital

    def receive_money(self, amount, location):
        """
        Adds money to the capitalist class.
        Unlike the other classes, the capiatlist class has two locations for money: revenue and capital.
        It will place them accordingly, and then refresh the money.

        Arguments:
        amount: the amount of money to be added (int)
        location: the location to add the money to (str) - either 'Revenue' or 'Capital'
        """
        logging.debug(f"Adding ${amount} to {self._faction} ({location})")
        if amount <= 0:
            logging.error('Failed to add money - amount cannot be less than 0')
            raise exceptions.ValueError('Failed to add money - amount cannot be less than 0')
        elif location.capitalize() == 'Revenue':
            self._revenue += amount
        elif location.capitalize() == 'Capital':
            self._capital += amount
        self.refresh_money()
        return

    def pay_money(self, amount, source = 'Both', mandatory = False):
        """
        Capitalist class payment method.
        This method is used to pay money from the capitalist class.
        Unlike the other classes, the capitalist class has two locations for money: revenue and capital.
        It will remove the money from the appropriate location, and then refresh the money.
        It will also check if the payment is mandatory or not, and if it is, it will not allow the payment to be made if there is not enough money.

        Mandatory payments from both sources are allowed, and payments will take from revenue first, then capital.
        If there is not enough money in either source, mandatory payments will take a loan to cover the difference.

        Arguments:
        amount: the amount of money to be paid (int)
        mandatory: whether the payment is mandatory or not (bool)
        source: the source of the money to be paid from (str) - either 'Revenue', 'Capital', or 'Both'
        """
        logging.debug(f"Removing ${amount} from {self._faction} ({source.lower()}) ({'True' if mandatory else 'False'}).")

        # Determine the source of the money
        if source.capitalize() == 'Revenue':
            if amount <= self._revenue:
                self._revenue -= amount
            elif not mandatory:
                logging.debug('Not enough money to make payment')
                raise exceptions.ValueError('Not enough money to make payment')
            elif mandatory:
                logging.debug('Not enough money for mandatory payment, taking as much as possible from revenue')
                logging.debug('This message should only trigger during income taxes')
                self._revenue == 0
        elif source.capitalize() == 'Capital':
            if amount <= self._capital:
                self._capital -= amount
            elif not mandatory:
                logging.debug('Not enough money to make payment')
                raise exceptions.ValueError('Not enough money to make payment')
            elif mandatory:
                logging.debug('Not enough money for mandatory payment, loan required')
                self._capital -= amount
                while self._capital < 0:
                    self.take_loan()
        elif source.capitalize() in ('Both', 'Any'):
            if amount >= self._revenue + self._capital:
                if self._revenue >= amount:
                    self._revenue -= amount
                else:
                    self._capital -= (amount - self._revenue)
                    self._revenue = 0

        else:
            logging.error('Failed to remove money - source must be either revenue, capital, or both')
            raise exceptions.InputError('Failed to remove money - source must be either revenue or capital, or both')
        self.refresh_money()
        return        
    
    def take_loan(self):
        logging.debug(f"{self._faction} taking a loan")
        self._loans += 1
        self.receive_money(50, 'Capital')
        return
    
    def repay_loan(self):
        logging.debug(f"{self._faction} repaying a loan")
        if self._loans == 0:
            logging.error('No loans to repay')
            raise exceptions.ClassMethodFailure('No loans to repay')
        elif self._capital < 50:
            logging.error('Not enough money to repay loan')
            raise exceptions.ClassMethodFailure('Not enough money to repay loan')
        else:
            self._capital -= 50
            if self._loans == 1:
                self._loans = 0
                logging.debug(f"Loan repaid, no loans remaining")
            else:
                self._loans -= 1
                logging.debug(f"Loan repaid, {self._loans} remaining")
        return

    def pay_loan_interest(self):
        logging.debug(f"{self._faction} paying loan interest")
        if self._loans == 0:
            logging.error('No loans to repay')
            raise exceptions.ClassMethodFailure('No loans to repay')
        elif self._capital < 5 * self._loans:
            logging.error('Not enough money to pay loan interest')
            self._capital -= 5 * self._loans
            while self._capital < 0:
                self.take_loan()
            logging.debug('Loan taken to pay interest')
            return
        else:
            self._capital -= 5 * self._loans
            return
    
class StateClass(Player):
        
    def __init__(self):

        super().__init__()
        self._faction = 'State'
        self._legitimacy = {'WC': 1, 'MC': 1, 'CC': 1}
        self._trade_goods = {'Healthcare':0, 'Education':0, 'Food':0, 'Luxury':0, 'Influence':0}
        self._prices = {}
        self._storage = {}
        self._resources = {'Influence':0}
        self._legitimacy_tokens = {'WC': 0, 'MC': 0, 'CC': 0}



    def add_legitimacy(self, faction):
        """
        Adds legitimacy to a class.
        """
        logging.debug(f"Adding legitimacy to {faction}")
        if faction not in self._legitimacy.keys():
            logging.error(f"Faction {faction} not found")
            raise exceptions.FactionNotFoundError(f"Faction {faction} not found")
        elif self._legitimacy[faction] >= 10:
            logging.debug(f"Legitimacy for {faction} is already at maximum")
            return
        else:
            self._legitimacy[faction] += 1
            logging.debug(f"Legitimacy added to {faction}")
            return

    def drop_legitimacy(self, faction):
        """
        Drops legitimacy to a class.
        """
        logging.debug(f"Dropping legitimacy for {faction}")
        if faction not in self._legitimacy.keys():
            logging.error(f"Faction {faction} not found")
            raise exceptions.FactionNotFoundError(f"Faction {faction} not found")
        elif self._legitimacy[faction] <= 1:
            logging.debug(f"Legitimacy for {faction} is already at minimum")
            return
        else:
            self._legitimacy[faction] -= 1
            logging.debug(f"Legitimacy dropped for {faction}")
            return
        
    def add_legiitmacy_token(self, faction):
        """
        Adds a legitimacy token to a class.
        """
        logging.debug(f"Adding legitimacy token for {faction}")
        if faction not in self._legitimacy.keys():
            logging.error(f"Faction {faction} not found")
            raise exceptions.FactionNotFoundError(f"Faction {faction} not found")
        elif self._legitimacy_tokens[faction] >= 6:
            logging.debug(f"Legitimacy for {faction} is already at maximum")
            return
        else:
            self._legitimacy[faction] += 1
            logging.debug(f"Legitimacy token added for {faction}")
            return
        
    def score_legitimacy(self):
        """
        Scores the legitimacy for the state class, divides them by 2, and adds the the legitimacy tokens.
        This is used at the end of each round, and adds the legitimacy score to the victory points.
        """
        from utilities import round_up

        logging.debug('Scoring legitimacy for State Class')
        self.add_victory_points(sum(list(self._legitimacy.values()).sort()[:2]))  # sum the lowest two legitimacy scores
        for faction in self._legitimacy.keys():
            self._legitimacy[faction] = int(round_up(self._legitimacy[faction] / 2, 0))  # round up to the nearest 2
            self._legitimacy[faction] += self._legitimacy_tokens[faction]  # add the legitimacy tokens to the score
        return
    



