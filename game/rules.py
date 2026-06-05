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
class ActionResult:
    """
    Parent class for the result of action rules
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
    Handles assigning points to players
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
            return False, 'Only active players in the game can receive points'
        return True, ''

    @staticmethod
    def resolve(player: Player, amount: int):
        """
        Apply the points. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("PointAssign resolve called")
        # Confirm validity
        valid,_ = PointAssign.check(player, amount)
        if not valid:
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
    def check(sender: Player | None, receiver: Player | None, amount: int, mandatory: bool) -> tuple[bool,str]:
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
        bool            - is the transaction valid?
        str             - failure reason if bool = False
        """
        logger.debug("MoneyTransfer check called")


        # Basic check flow
        if amount <= 0:
            return False, "Amount must be positive"
        if (sender is None) & (receiver is None):
            return False, 'Cannot tranfer from None to None'
        if sender is receiver:
            return False, "Cannot transfer to yourself"
        if sender is None:
            return True, ""
        if sender.money >= amount:
            return True, ""
        
        # For senders with insufficient funds:
        shortfall = sender.money - amount
        if not mandatory:
            return False, f"{sender.faction} cannot afford transaction. Needs {shortfall} more"
        return True, ""
    
    @staticmethod
    def resolve(sender: Player | None, receiver: Player | None, amount: int, mandatory: bool) -> ActionResult:
        """
        Apply the transfer. Only call this after check returns True, or risk an exception.
        All mutations happen here — never partially applied.
        """
        logger.debug("MoneyTransfer resolve called")

        # Confirm validity
        valid,_ = MoneyTransfer.check(sender,receiver,amount,mandatory)
        if not valid:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")
        
        # Setup generic response
        changes = []
        loan_needed = False
        loan_count = 0

        ### Sender ###

        # Payment from bank - always successful
        if sender is None:
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
                f"{sender.faction} paid {amount} to {receiver.faction}"
                + f"{sender.faction} took {loan_count} loan{'s' if loan_count > 1 else ''}"
            )
            return ActionResult(
                outcome = Outcome.LOAN if loan_needed else Outcome.OK,
                log=log,
                state_changes=changes
            )


############################# Action Layer ########################################

@dataclass    
class FreeAction:
    """
    Lists the free actions avaialbe to all players
    
    The actions here contain the complete process with checks, and can be called directly from the agent interface
    
    ALL METHODS MUST CONTAIN PLAYER OBJECT AS AN ARGUMENT
    """
    logger.debug("called FreeAction class")
    from game.data.factions import Player

    @staticmethod
    def context() -> list:
        """
        Used by the DecisionContext to create a list, which it will check for validity
        """
        subclasses = []
        for attribute in dir(FreeAction):
            if isinstance(getattr(FreeAction, attribute), type):
                if hasattr(attribute, 'check'):
                    subclasses.append(attribute)
        return subclasses

    @dataclass
    class RepayLoan:
        logger.debug("called RepayLoan subclass")
        from game.data.factions import Player

        @staticmethod
        def check(player: Player):
            logger.debug('RepayLoan check called')

            # Check flow
            if player.loans <= 0:
                return False, 'Player has no loans'
            if player.money < 50:
                return False, 'Not enough money'
            return True, ''
        
        @staticmethod
        def resolve(player: Player):
            logger.debug('ReplayLoan resolve called')

            # Confirm validity
            valid,_ = FreeAction.RepayLoan.check(player)
            if not valid:
                raise Exception("Invalid call to resolve loan repayment. Ensure validity check is being called prior and is working.")

            # Execute
            changes = []
            log = f"{player.faction} paid 50 to repay a loan"
            player._add_money(-50)
            changes.append(f"{player.faction} paid 50")
            changes.append(f"{player.faction} money: {player.money}")
            player._remove_loan()
            changes.append(f"{player.faction} removed a loan")
            changes.append(f"{player.faction} loans: {player.loans}")
            return ActionResult(Outcome.OK, log, changes)






logger.debug("Finished importing rules.rules module")