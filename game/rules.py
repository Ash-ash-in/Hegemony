import logging
logger = logging.getLogger(__name__)
logger.debug("Importing rules.rules module")

from dataclasses import dataclass
from enum import Enum, auto
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
    
###################### Intermadiate Rule Layer ####################################

@dataclass
class PointAssign:
    """
    Handles assigning points to players. Intermediate layer
    """
    logger.debug("called PointAssign class")
    from game.states import GameState, Player

    @staticmethod
    def check(gamestate: GameState, player: Player, amount: int):
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
    def resolve(gamestate: GameState, player: Player, amount: int):
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
class MoneyTransfer:
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
        check = MoneyTransfer.check(sender,receiver,amount,mandatory)
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
            changes.append(f"{receiver.faction} received {receiver.money} Vardis")
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
        changes.append(f"{sender.faction} sent {sender.money} Vardis")
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
            changes.append(f"{receiver.faction} received {receiver.money} Vardis")
            changes.append(f"{receiver.faction} money: {receiver.money}")
            logger.info(f"added {amount} money to {receiver}")
            return ActionResult(
                state_changes=changes
            )
        
@dataclass
class WorkerSpawn:
    """
    Handles birthing workers from the pool to the unemployment area
    """
    logger.debug("called WorkerSpawn class")
    from game.states import Player, GameState

    @staticmethod
    def check(gamestate: GameState, player: WorkingClass | MiddleClass, skill: str):
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

        # Basic check flow
        if player.faction in ('Capitalists', 'State'):
            return CheckResponse(False, f'{player.faction} does not have workers')
        if player.faction == 'Middle Class' and gamestate.player_count < 3:
            return CheckResponse(False, f'{player.faction} is not in the game')
        if len(gamestate.worker_pool[player.faction]) == 0:
            return CheckResponse(False, 'No workers available for this faction')
        found = False
        for worker in gamestate.worker_pool[player.faction]:
            if worker.skill == skill:
                found = True
                break
        if not found:
            return CheckResponse(False, 'No remaining workers of that skill')
        return CheckResponse(True, '')

    @staticmethod
    def resolve(gamestate: GameState, player: WorkingClass | MiddleClass, skill: str):
        """
        Spawn the worker into the unemployment area. 
        Updates player's population.
        
        Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("WorkerSpawn resolve called")
        # Confirm validity
        check = WorkerSpawn.check(gamestate, player, skill)
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
class LoanRemoval:
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
        return CheckResponse(True, "")
    
    @staticmethod
    def resolve(player: Player) -> ActionResult:
        """
        Apply the transfer. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("MoneyTransfer resolve called")

        # Confirm validity
        check = LoanRemoval.check(player)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")
        
        # Setup generic response
        changes = []

        # Enact
        player._remove_loan()
        changes.append(f"{player.faction} had 1 loan removed")
        logger.info(f"removed a loan from {player.faction}")
        return ActionResult(
            changes
        )


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
        def context(gamestate: GameState, player: Player) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}) -> CheckResponse:
            logger.debug('RepayLoan check called')

            # This has a simple intermediate step, so call that 
            return LoanRemoval.check(player)

        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}):
            logger.debug('ReplayLoan resolve called')

            # Confirm validity
            check = FreeAction.RepayLoan.check(gamestate, player)
            if not check.validity:
                raise Exception("Invalid call to resolve loan repayment. Ensure validity check is being called prior and is working.")

            # This has a simple intermediate step, so call that 
            return LoanRemoval.resolve(player)

@dataclass
class MainAction:
    logger.debug("called MainAction class")

    @dataclass
    class TestAction1:
        """
        Sends 50 quid to the player. Don't forget to remove before training begins!
        """

        @staticmethod
        def context(gamestate: GameState, player: Player) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}):
            logger.warning('Called MainAction.TestAction1.check()')
            check = MoneyTransfer.check(None, player, 30, False)
            if not check.validity:
                return CheckResponse(False, f"Money check failed: {check.tooltip}")
            return CheckResponse(True, '')
        
        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}):
            logger.warning('Called MainAction.TestAction1.resolve()')

            # Validity
            check = MainAction.TestAction1.check(gamestate, player)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            result = MoneyTransfer.resolve(None, player, 30, False)
            return ActionResult(result.state_changes)

    @dataclass
    class TestAction2:
        """
        Adds a loan to a player. Don't forget to remove before training begins!
        """

        @staticmethod
        def context(gamestate: GameState, player: Player) -> dict:
            """Builds the args for a successful call 
            These are made with the context layer for complex decisions 
            Otherwise a blank dictionary is returned""" 
            return {}

        @staticmethod
        def check(gamestate: GameState, player: Player, args: dict = {}):
            logger.warning('Called MainAction.TestAction2.check()')
            return CheckResponse(True, '')
        
        @staticmethod
        def resolve(gamestate: GameState, player: Player, args: dict = {}):
            logger.warning('Called MainAction.TestAction2.resolve()')

            # Validity
            check = MainAction.TestAction2.check(gamestate, player)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            player._take_loan()
            logger.info(f"{player.faction} took a loan.")
            state_changes = [f"{player.faction} took a loan."]
            return ActionResult(state_changes)
