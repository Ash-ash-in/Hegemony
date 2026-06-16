import logging
logger = logging.getLogger(__name__)
logger.debug("Importing rules.rules module")

from dataclasses import dataclass
from enum import Enum, auto

######################### Utilities #######################################
class Outcome(Enum):
    OK = auto()
    INVALID = auto()
    LOAN = auto()

@dataclass
class CheckResponse:
    """
    Contains all the information that would allow an agent to successfully complete this action
    
    # Attributes:
    validity: bool
    tooltip: str
    actiontype: str
    params: list    
    """
    validity: bool
    tooltip: str
    actiontype: str
    params: list

@dataclass
class ActionResult:
    """
    Parent class for the result of action rules

    # Attributes
    outcome: Outcome instance
    log: str
    state_changes[list[str]]
    """
    outcome: Outcome
    log: str # Simple description of the action
    state_changes: list[str] # Details of all changes for UI

    def print(self):
        print(self.log)
        return
    

############################# Rule Layer ####################################
@dataclass
class PointAssign:
    """
    Handles assigning points to players. Intermediate layer
    """
    logger.debug("called PointAssign class")
    from game.data.factions import Player

    @staticmethod
    def check(player: Player, amount: int):
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
        import game.data.common as common
        global player_count

        # Basic check flow
        if common.faction_instantiate_order.index(player.faction) > player_count - 1:
            return CheckResponse(False, 'Only active players in the game can receive points', 'Intermediate', [])
        return CheckResponse(True, '', 'Intermediate', [])

    @staticmethod
    def resolve(player: Player, amount: int):
        """
        Apply the points. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("PointAssign resolve called")
        # Confirm validity
        check = PointAssign.check(player, amount)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")

        # Execute
        player._add_victory_points(amount) # Negative values are handled internally
        log = f'Added {amount} victory points to {player.faction}'
        changes = [log]
        return ActionResult(outcome=Outcome.OK, log=log, state_changes=changes)

@dataclass
class MoneyTransfer:
    """
    Handles both mandatory and optional transfers.

    mandatory=False (optional):  block the transfer if sender can't afford it.
    mandatory=True:              auto-take a loan to cover the shortfall.
    """
    logger.debug("called MoneyTransfer class")
    from game.data.factions import Player

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
            return CheckResponse(False, "Amount must be positive", "Intermediate", [])
        if (sender is None) & (receiver is None):
            return CheckResponse(False, 'Cannot tranfer from None to None', 'Intermediate', [])
        if sender is receiver:
            return CheckResponse(False, "Cannot transfer to yourself", 'Intermediate', [])
        if sender is None:
            return CheckResponse(True, "", 'Intermediate', [])
        if sender.money >= amount:
            return CheckResponse(True, "", "Intermediate", [])
        
        # For senders with insufficient funds:
        shortfall = sender.money - amount
        if not mandatory:
            return CheckResponse(False, f"{sender.faction} cannot afford transaction. Needs {shortfall} more", "Intermediate", [])
        return CheckResponse(True, "", "Intermediate", [])
    
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
            log = (f"Bank paid {amount} to {receiver.faction}")
            logger.debug(f"{receiver.faction} received {amount} from Bank")
            return ActionResult(
                outcome = Outcome.OK,
                log=log,
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
            logger.debug(f"{sender.faction} took {loan_count} loans")
        
        # Sender has enough money:
        sender._add_money(amount * -1)
        changes.append(f"{sender.faction} sent {sender.money} Vardis")
        changes.append(f"{sender.faction} money: {sender.money}")
        logger.debug(f"removed {amount} money from {sender.faction}")

        ### Receiver ###

        # Payment to bank
        if receiver is None:
            log = (f"{sender.faction} paid {amount} to bank")
            return ActionResult(
                outcome = Outcome.OK,
                log=log,
                state_changes=changes
            )

        # Payment to player
        else:
            receiver._add_money(amount)
            changes.append(f"{receiver.faction} received {receiver.money} Vardis")
            changes.append(f"{receiver.faction} money: {receiver.money}")
            logger.debug(f"added {amount} money to {receiver}")
            log = (
                f"{sender.faction} paid {amount} to {receiver.faction}."
                + f" {sender.faction} took {loan_count} loan{'s' if loan_count > 1 else ''}."
            )
            return ActionResult(
                outcome = Outcome.LOAN if loan_needed else Outcome.OK,
                log=log,
                state_changes=changes
            )

@dataclass
class LoanRemoval:
    """
    Handles the intermediate step for paying a loan.
    """
    logger.debug("called MoneyTransfer class")
    from game.data.factions import Player

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
            return CheckResponse(False, "Player has no loans", "Intermediate", [])
        return CheckResponse(True, "", "Intermediate", [])
    
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
        logger.debug(f"removed a loan from {player}")
        log = (
            f"{player.faction} had a loan removed."
        )
        return ActionResult(
            outcome = Outcome.OK,
            log=log,
            state_changes=changes
        )

@dataclass
class CompanyFoundation:
    """
    Puts a company from one player's pool into their 
    
    This handles the physical aspects of putting the card in place, but does not involve any exchange of money or assignment of workers.
    """
    logger.debug("called CompanyFoundation class")
    from game.data.factions import Player
    from game.data.common import GameState, Company

    @staticmethod
    def check(player: Player, gamestate: GameState, comp: Company) -> CheckResponse:
        """
        ### Args
        player - the player to check
        gamestate
        comp_name - the name of the company to found
        """
        logger.debug("Called CompanyFoundation.check()")
        # Validation flow
        if comp not in player.company_hand:
            return CheckResponse(False, "Company is not in the player's hand", "Intermediate", []) 
        if None not in gamestate.companies[player.faction].values():
            return CheckResponse(False, "No slots free", "Intermediate", [])
        return CheckResponse(True, "", "Intermediate", [])

    @staticmethod
    def resolve(player: Player, gamestate: GameState, comp: Company) -> ActionResult:
        """
        ### Args
        player - the player to check
        gamestate
        comp_name - the name of the company to found
        """
        logger.debug("Called CompanyFoundation.resolve()")

        # Validation check
        if not CompanyFoundation.check(player, gamestate, comp).validity:
            raise Exception("CompanyFoundation resolve called but failed check")

        # Execute
        changes = []
        slot = None
        for c_num, occupant in gamestate.companies[player.faction].items():
            if occupant is None:
                slot = c_num
                break
        if slot is None:
            raise Exception("Company slot could not be found, but check already passed.")
        player._remove_company_card_from_hand(comp)
        changes.append(f"{comp.name} removed from {player.faction}'s market")
        gamestate.companies[player.faction][slot] = comp
        changes.append(f'{comp.name} founded in slot {slot[-1]}')
        log = f"{player.faction} founded {comp.name}"
        return ActionResult(Outcome.OK, log, changes)



############################# Action Layer ########################################

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
    from game.data.factions import Player

    @staticmethod
    def context(player: Player) -> dict:
        """
        Used by the DecisionContext to create a list, which it will check for validity

        ### Agrs
            player
        ### Returns 
            CheckResponse
        """
        import inspect
        logger.debug("FreeAction.context() called")

        options_dict = {}
        for name, clsmthd in inspect.getmembers(FreeAction, inspect.isclass):
            if hasattr(clsmthd, "check"):
                options_dict[name] = (clsmthd, clsmthd.check(player))
        return options_dict
    

    @dataclass
    class RepayLoan:
        logger.debug("called RepayLoan subclass")
        from game.data.factions import Player

        @staticmethod
        def check(player: Player):
            logger.debug('RepayLoan check called')

            # This has a simple intermediate step, so call that 
            return LoanRemoval.check(player)
        
        @staticmethod
        def resolve(player: Player):
            logger.debug('ReplayLoan resolve called')

            # Confirm validity
            check = FreeAction.RepayLoan.check(player)
            if not check.validity:
                raise Exception("Invalid call to resolve loan repayment. Ensure validity check is being called prior and is working.")

            # This has a simple intermediate step, so call that 
            return LoanRemoval.resolve(player)

class MainAction:
    logger.debug("called MainAction class")
    from game.data.factions import Player

    @staticmethod
    def context(player: Player) -> dict:
        """
        Used by the DecisionContext to create a list of possible actions, which it will check for validity

        Args
            player: Player instance

        Returns
            dict (name: (classmethod, checkresponse)
        """
        import inspect
        logger.debug("MainAction.context() called")

        options_dict = {}
        for name, clsmthd in inspect.getmembers(MainAction, inspect.isclass):
            if hasattr(clsmthd, "check"):
                options_dict[name] = (clsmthd, clsmthd.check(player))
        return options_dict

    @dataclass
    class TestAction1:
        """
        Sends 50 quid to the player. Don't forget to remove before training begins!
        """
        from game.data.factions import Player

        @staticmethod
        def check(player: Player):
            logger.debug('Called MainAction.TestAction1.check()')
            check = MoneyTransfer.check(None, player, 30, False)
            if not check.validity:
                return CheckResponse(False, f"Money check failed: {check.tooltip}", "Main", [])
            return CheckResponse(True, '', 'Main', [])
        
        @staticmethod
        def resolve(player: Player):
            logger.debug('Called MainAction.TestAction1.resolve()')

            # Validity
            check = MainAction.TestAction1.check(player)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            result = MoneyTransfer.resolve(None, player, 30, False)
            return ActionResult(Outcome.OK, result.log, result.state_changes)

    @dataclass
    class TestAction2:
        """
        Adds a loan to a player. Don't forget to remove before training begins!
        """
        from game.data.factions import Player

        @staticmethod
        def check(player: Player):
            logger.debug('Called MainAction.TestAction2.check()')
            return CheckResponse(True, '', 'Main', [])
        
        @staticmethod
        def resolve(player: Player):
            logger.debug('Called MainAction.TestAction2.resolve()')

            # Validity
            check = MainAction.TestAction2.check(player)
            if not check.validity:
                raise Exception('Check failed when calling resolve')
            
            # Resolve
            player._take_loan()
            log = f"{player.faction} took a loan."
            state_changes = [f"{player.faction} took a loan."]
            return ActionResult(Outcome.OK, log, state_changes)

logger.debug("Finished importing rules.rules module")