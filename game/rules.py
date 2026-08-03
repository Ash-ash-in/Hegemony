import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass
from game.states import GameState, Player, WorkingClass, MiddleClass

# Rule Interaction Classes
@dataclass
class CheckResponse:
    """
    Contains the validity of an action, and the reason why if False

    # Attributes:
    validity: bool
    tooltip: str
    """
    validity: bool
    tooltip: str

@dataclass
class ActionResult:
    """
    Ensures uniformatiy of the text response from a sequence of actions

    # Attributes
    state_changes[list[str]]
    """
    state_changes: list[str] # Details of all changes for UI
    
###################### Simple Rule Layer ####################################
### These rules do not handle any decsiion making ###
### They are the final layer of confirmation before affecting player/gamestates ###
#############################################################################

@dataclass
class _PointAssign:
    """
    Handles assigning points to players. Intermediate layer
    """
    logger.debug("called PointAssign class")
    from game.states import GameState, Player

    @staticmethod
    def check(gamestate: GameState, player: Player, amount: int) -> CheckResponse:
        """
        Determines whether a transaction is possible. 
        This should ALWAYS be called before resolving.
        This is called as part of the resolve process, but will crash the program if it fails at that point.

        ### Args
        player:         - Player object instance
        amount:         - integer

        ### Returns
        bool            - is the transaction valid?
        str             - failure reason if bool = False
        """
        logger.debug("PointAssign check called")
        import game.data.references as refs
        global player_count

        # Basic check flow
        if refs.faction_instantiate_order.index(player.faction) > gamestate.player_count - 1:
            return CheckResponse(False, 'Only active players in the game can receive points')
        return CheckResponse(True, '')

    @staticmethod
    def resolve(gamestate: GameState, player: Player, amount: int) -> ActionResult:
        """
        Apply the points. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("PointAssign resolve called")
        # Confirm validity
        check = PointAssign.check(gamestate, player, amount)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")

        # Execute
        player._add_victory_points(amount) # Negative values are handled internally
        logger.info("f'Added {amount} victory points to {player.faction}'")
        changes = [f'Added {amount} victory points to {player.faction}']
        return ActionResult(state_changes=changes)

@dataclass
class _MoneyTransfer:
    """
    Handles both mandatory and optional transfers.

    mandatory=False (optional):  block the transfer if sender can't afford it.
    mandatory=True:              auto-take a loan to cover the shortfall.
    """
    logger.debug("called MoneyTransfer class")
    from game.states import Player

    @staticmethod
    def check(sender: Player | None, receiver: Player | None, amount: int, mandatory: bool) -> CheckResponse:
        """
        Determines whether a transaction is possible. 
        This should ALWAYS be called before resolving.
        This is called as part of the resolve process, but will crash the program if it fails at that point.

        ### Args
        sender:         - player instance or None for bank
        receiver:       - player instance or None for bank
        amount:         - integer
        mandatory:      - bool. Determines whether it will force loans when insufficient funds.

        ### Returns
        CheckResponse(
            validity: bool,
            tooltip: str,
            actiontype: str,
            params: list
            )
        """
        logger.debug("MoneyTransfer check called")


        # Basic check flow
        if amount <= 0:
            return CheckResponse(False, "Amount must be positive")
        if (sender is None) & (receiver is None):
            return CheckResponse(False, 'Cannot tranfer from None to None')
        if sender is receiver:
            return CheckResponse(False, "Cannot transfer to yourself")
        if sender is None:
            return CheckResponse(True, "")
        if sender.money >= amount:
            return CheckResponse(True, "")
        
        # For senders with insufficient funds:
        shortfall = sender.money - amount
        if not mandatory:
            return CheckResponse(False, f"{sender.faction} cannot afford transaction. Needs {shortfall} more")
        return CheckResponse(True, "")
    
    @staticmethod
    def resolve(sender: Player | None, receiver: Player | None, amount: int, mandatory: bool) -> ActionResult:
        """
        Apply the transfer. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("MoneyTransfer resolve called")

        # Confirm validity
        check = _MoneyTransfer.check(sender,receiver,amount,mandatory)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")
        
        # Setup generic response
        changes = []
        loan_needed = False
        loan_count = 0

        ### Sender ###

        # Payment from bank - always successful
        if sender is None:
            if receiver is None:
                raise Exception("Sender and receiver both None")
            receiver._add_money(amount)
            changes.append(f"{receiver.faction} received {amount} Vardis")
            changes.append(f"{receiver.faction} money: {receiver.money}")
            logger.info(f"{receiver.faction} received {amount} from Bank")
            return ActionResult(
                state_changes=changes
            )
        
        # Handle loans if necessary
        elif sender.money < amount:
            while sender.money < amount:
                sender._take_loan()
                sender._add_money(50)
                loan_count += 1
            changes.append(f"{sender.faction} took {loan_count} loan{'s' if loan_count > 1 else ''}")
            loan_needed = True
            logger.info(f"{sender.faction} took {loan_count} loans")
        
        # Sender has enough money:
        sender._add_money(amount * -1)
        changes.append(f"{sender.faction} sent {amount} Vardis")
        changes.append(f"{sender.faction} money: {sender.money}")
        logger.info(f"removed {amount} money from {sender.faction}")

        ### Receiver ###

        # Payment to bank
        if receiver is None:
            log = (f"{sender.faction} paid {amount} to bank")
            return ActionResult(
                state_changes=changes
            )

        # Payment to player
        else:
            receiver._add_money(amount)
            changes.append(f"{receiver.faction} received {amount} Vardis")
            changes.append(f"{receiver.faction} money: {receiver.money}")
            logger.info(f"added {amount} money to {receiver.faction}")
            return ActionResult(
                state_changes=changes
            )
        
@dataclass
class _WorkerSpawn:
    """
    Handles birthing workers from the pool to the unemployment area.
    There is no room for ambiguity, it need to receive a class and skill to function.
    """
    logger.debug("called WorkerSpawn class")
    from game.states import Player, GameState

    @staticmethod
    def check(gamestate: GameState, player: WorkingClass | MiddleClass, skill: str) -> CheckResponse:
        """
        Determines whether spawning is possible. 
        This should ALWAYS be called before resolving.
        This is called as part of the resolve process, but will crash the program if it fails at that point.

        ### Args
        player:         - Player object instance
        skill:          - string, must be one of the industries or 'unskilled'

        ### Returns
        CheckResponse
        """
        logger.debug("WorkerSpawn check called")

        # Check class
        if player.faction in ('Capitalists', 'State'):
            return CheckResponse(False, f'{player.faction} does not have workers')
        if player.faction == 'Middle Class' and gamestate.player_count < 3:
            return CheckResponse(False, f'{player.faction} is not in the game')
        if len(gamestate.worker_pool[player.faction]) == 0:
            return CheckResponse(False, 'No workers available for this faction')

        # Check skill
        found = False
        for worker in gamestate.worker_pool[player.faction]:
            if worker.skill == skill:
                found = True
                break
        if not found:
            return CheckResponse(False, 'Worker of requested skill unavailable')
        return CheckResponse(True, '')

    @staticmethod
    def resolve(gamestate: GameState, player: WorkingClass | MiddleClass, skill: str) -> ActionResult:
        """
        Spawn the worker into the unemployment area. 
        Updates player's population.
        
        Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("WorkerSpawn resolve called")

        # Confirm validity
        check = _WorkerSpawn.check(gamestate, player, skill)
        if not check.validity:
            raise Exception("Invalid call to resolve. Ensure validity check is being called prior and is working.")

        ### Execute ###
        changes = []

        # Find the worker and remove from pool
        for candidate in gamestate.worker_pool[player.faction]:
            if candidate.skill == skill:
                worker = candidate
                gamestate.worker_pool[player.faction].remove(worker)
                break
        # Add to unemployment area and update player's population
        gamestate.unemployed_workers[player.faction].append(worker) # type: ignore
        changes.append('Worker added to unemployment area')

        # Update player's population
        pop = player.population
        player._add_population()
        changes.append(f"{player.faction} population track adjusted")
        logger.info(f'{player.faction} {worker.skill} worker spawned in unemployment area') # type: ignore
        if player.population != pop:
            changes.append(f"{player.faction} population has increased")
            logger.info(f"{player.faction} population has increased")
        return ActionResult(changes)

@dataclass
class _WorkerHire:
    """
    Moves a worker from the unemployment area to a company
    
    This handles the movement of a specific worker to a specific slot. 
    It does not check if this is wise.
    It does not check if this would result in a fully staffed company.
    It does not check if this would cause the source companies to become inactive.
    Handles checks related to worker skill and class.
    """
    logger.debug("called WorkerHire class")
    from game.data.classes import Company, Worker
    from game.states import CompanySlot

    @staticmethod
    def check(gamestate: GameState, worker: Worker, target_companyslot: CompanySlot, target_slot: int) -> CheckResponse:
        """
        ### Args
        source_company: Company | list (for company or unemployment_area)
        source_slot: int
        target_company: Company
        target_slot: int

        ### Returns
        CheckResponse
        """
        logger.debug("Called WorkerHire.check()")

        # Validation flow
        if target_companyslot.company is None:
            return CheckResponse(False,"Slot has no company")
        if target_companyslot.workers[target_slot] is not None:
            return CheckResponse(False, "Slot already occupied")
        if worker not in gamestate.unemployed_workers[worker.faction]:
            return CheckResponse(False, "Worker is not currently enemployed")
        target_class = target_companyslot.company.worker_requirements[target_slot]["faction"]
        target_skill = target_companyslot.company.worker_requirements[target_slot]["skill"]
        if worker.faction != target_class and target_class != 'Any':
            return CheckResponse(False, "Worker class not suitable for slot")
        if worker.skill != target_skill and target_skill != 'Any':
            return CheckResponse(False, "Worker does not have the appropriate skill")
        return CheckResponse(True, "")

    @staticmethod
    def resolve(gamestate: GameState, worker: Worker, target_companyslot: CompanySlot, target_slot: int) -> ActionResult:
        """
        ### Args
        source_company: Company
        source_slot: int
        target_company: Company
        target_slot: int

        ### Returns
        ActionResult
        """
        logger.debug("Called WorkerHire.resolve()")

        ### Validation check
        if not _WorkerHire.check(gamestate, worker, target_companyslot, target_slot).validity:
            raise Exception("CompanyFound resolve called but failed check")
        if target_companyslot.company is None:
            raise Exception("Target slot is empty but check passed")

        ### Execute
        changes = []

        # Remove worker from unemplyment area
        gamestate.unemployed_workers[worker.faction].remove(worker)
        changes.append("Worker removed from unemployment area")
        logger.debug(changes[-1])

        # Add to new slot
        target_companyslot.workers[target_slot] = worker
        changes.append(f"Worker added to {target_companyslot.company.name} in worker slot {target_slot}")
        logger.debug(changes[-1])
        return ActionResult(changes)

@dataclass
class _LoanRemove:
    """
    Handles the intermediate step for paying a loan.
    """
    logger.debug("called MoneyTransfer class")
    from game.states import Player

    @staticmethod
    def check(player: Player) -> CheckResponse:
        """
        Determines whether there are any loans to pay.

        ### Args
        player          - instance to check for loans

        ### Returns
        CheckResponse
        """
        logger.debug("LoanRemoval check called")

        # Basic check flow
        if player.loans <= 0:
            return CheckResponse(False, "Player has no loans")
        if player.money < 50:
            return CheckResponse(False, "Player cannot afford to repay loan")
        return CheckResponse(True, "")
    
    @staticmethod
    def resolve(player: Player) -> ActionResult:
        """
        Apply the transfer. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("MoneyTransfer resolve called")

        # Confirm validity
        check = _LoanRemove.check(player)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")

        # Enact
        changes = []
        player._repay_loan()
        changes.append(f"{player.faction} had 1 loan removed")
        return ActionResult(changes)

@dataclass
class _CompanyFound:
    """
    Puts a company from one player's market onto the board
    
    This handles the physical aspects of putting the card in place, 
    but does not involve any exchange of money or assignment of workers.
    """
    from game.states import Player, GameState
    from game.data.classes import Company
        
    @staticmethod
    def check(player: Player, gamestate: GameState, company: Company) -> CheckResponse:
        """
        ### Args
        - player - the player with the company in their hand
        - gamestate
        - args
            - company - the Company object to found
            - slot - optional, the slot to move the company to
        """
        logger.debug("Called CompanyFound.check()")

        if company not in player.market:
            return CheckResponse(False, "Company is not in the player's hand")

        # Look for a free slot if not passed
        free_slot = 'x'
        for i in range(len(gamestate.companies[player.faction])):
            if gamestate.companies[player.faction][i].company is None:
                free_slot = i
                break
        if free_slot == 'x':
            return CheckResponse(False, "No company slots free")
        return CheckResponse(True, "")

    @staticmethod
    def resolve(player: Player, gamestate: GameState, company: Company) -> ActionResult:
        """
        ### Args
        - player - the player with the company in their hand
        - gamestate
        - company - Company object, which should be in the player's market
        """
        logger.debug("Called CompanyFound.resolve()")
        changes = []

        # Validation check
        if not _CompanyFound.check(player, gamestate, company).validity:
            raise Exception("CompanyFound resolve called but failed check")

        # Execute

        # Point to slot
        slotnum = 'x'
        for i in range(len(gamestate.companies[player.faction])):
            if gamestate.companies[player.faction][i].company is None:
                slotnum = i
                slot = gamestate.companies[player.faction][i]
                break
        if slotnum == 'x':
            raise Exception("Company slot could not be found, but check already passed.")

        # Remove card from market
        player._remove_company_from_market(company)
        changes.append(f"{company.name} removed from {player.faction}'s market")
        logger.debug(changes[-1])

        # Put company in slot
        slot.company = company
        changes.append(f'{company.name} founded in {player.faction} company slot {slotnum}')
        logger.debug(changes[-1])

        # Update CompanySlot's workers list
        worker_count = len(company.worker_requirements.keys())
        for i in range(worker_count):
            slot.workers.append(None)
        logger.debug(f"{worker_count} empty worker slots founded in CompanySlot.workers")

        return ActionResult(changes)

########################## Intermediate Rule Layer ###########################
### These rules handle functions of the system ###
### Or handle actions the require more than one simple rule to be checked ###
##############################################################################

@dataclass
class ImmigrationCardDraw:
    """
    Handles drawing of the card
    Spawning the worker
    Requesting the agent to choose if necessary
    """
    logger.debug("called ImmigrationCardDraw")

    @staticmethod
    def check(gamestate: GameState, player: Player):
        logger.debug("called ImmigrationCardDraw.check")
        if player.faction in ('State','Capitalists'):
            return CheckResponse(False, f"{player.faction} cannot draw immigration cards", "Intermediate", [])
        return CheckResponse(True, "")
    
    @staticmethod
    def resolve(gamestate: GameState, player: Player):
        logger.debug("Called ImmigrationCardDraw.resolve")
        check = ImmigrationCardDraw.check(gamestate, player)
        if not check.validity:
            raise Exception("Invalid call to resolve immigration card. Ensure validity check is being called prior and is working.")
        changes = []

        # Draw a card
        card = gamestate.immigration_cards[0]
        gamestate.update_immigration_card # Moves the card to the back of the deck
        changes.append('Immigration card drawn')

        # Check if a worker of that skill is available
        if player.faction == 'Working Class':
            skill = card.WorkingClass[1]
        else:
            skill = card.MiddleClass[1]
        check = _WorkerSpawn.check(gamestate, player, skill)

        # Request player decision if worker skill not available
        if not check.validity:
            logger.info(f"No {player.faction} worker available with skill: {skill}")

            # Handle no workers at all (extremely rare)
            if len(gamestate.worker_pool[player.faction]) == 0:
                changes.append("No workers were available")
                return ActionResult(changes)

            if skill == 'Unskilled':
                # Request to agent
                from game.context import SpawnedWorkerSkillContext
                SpawnedWorkerSkillContext(gamestate, player, "", 1)
            else:
                skill = 'Unskilled'
            # Now handling the alternative skill
            check = _WorkerSpawn.check(gamestate, player, skill)
            if not check.validity:
                raise Exception(f"{skill} worker was returned by SpawnedWorkerSkillContext, but check could not be validated")

        # Spawn the worker
        inner_response = _WorkerSpawn.resolve(gamestate, player, skill)
        changes += inner_response.state_changes
        return ActionResult(changes)

    
####################### Action Rules Layer ################################

@dataclass    
class FreeAction:
    """
    Used by the DecisionContext to create a list of possible actions, which it will check for validity

    Args
        player: Player instance

    Returns
        dict (name: (classmethod, checkresponse)
    """
    logger.debug("called FreeAction class")
    
    @dataclass
    class RepayLoan:
        logger.debug("called RepayLoan subclass")

        @staticmethod
        def context(gamestate: GameState, player: Player, parent) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            from game.context import Context
            if not isinstance(parent, Context):
                raise Exception("parent arg must be a Context instance")
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}) -> CheckResponse:
            logger.debug('RepayLoan check called')

            # This has a simple intermediate step, so call that 
            return _LoanRemove.check(player)

        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}) -> ActionResult:
            logger.debug('ReplayLoan resolve called')

            # Confirm validity
            check = FreeAction.RepayLoan.check(gamestate, player, args)
            if not check.validity:
                raise Exception("Invalid call to resolve loan repayment. Ensure validity check is being called prior and is working.")

            # This has a simple intermediate step, so call that 
            return _LoanRemove.resolve(player)

@dataclass
class MainAction:
    logger.debug("called MainAction class")

    @dataclass
    class TestAction1:
        """
        Sends 30 quid to the player. Don't forget to remove before training begins!
        """

        @staticmethod
        def context(gamestate: GameState, player: Player, parent) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            from game.context import Context
            if not isinstance(parent, Context):
                raise Exception("parent arg must be a Context instance")
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}) -> CheckResponse:
            logger.warning('Called MainAction.TestAction1.check()')
            check = _MoneyTransfer.check(None, player, 30, False)
            if not check.validity:
                return CheckResponse(False, f"Money check failed: {check.tooltip}")
            return CheckResponse(True, '')
        
        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}) -> ActionResult:
            logger.warning('Called MainAction.TestAction1.resolve()')

            # Validity
            check = MainAction.TestAction1.check(gamestate, player, args)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            result = _MoneyTransfer.resolve(None, player, 30, False)
            return ActionResult(result.state_changes)

    @dataclass
    class TestAction2:
        """
        Adds a loan to a player. Don't forget to remove before training begins!
        """

        @staticmethod
        def context(gamestate: GameState, player: Player, parent) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            from game.context import Context
            if not isinstance(parent, Context):
                raise Exception("parent arg must be a Context instance")
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}) -> CheckResponse:
            logger.warning('Called MainAction.TestAction2.check()')
            return CheckResponse(True, '')
        
        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}) -> ActionResult:
            logger.warning('Called MainAction.TestAction2.resolve()')

            # Validity
            check = MainAction.TestAction2.check(gamestate, player, args)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            player._take_loan()
            logger.info(f"{player.faction} took a loan.")
            state_changes = [f"{player.faction} took a loan."]
            return ActionResult(state_changes)
