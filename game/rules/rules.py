import logging
logger = logging.getLogger(__name__)
logger.debug("Importing rules.rules module")

from dataclasses import dataclass
from enum import Enum, auto

class Outcome(Enum):
    OK = auto()
    INVALID = auto()
    LOAN = auto()

@dataclass
class MoneyActionResult:
    outcome: Outcome
    log: str # Simple description of the action
    state_changes: list[str] # Details of all changes for UI

    def print(self):
        print(self.log)
        return

@dataclass
class MoneyTransfer:
    """
    Handles both mandatory and optional transfers.

    mandatory=False (optional):  block the transfer if sender can't afford it.
    mandatory=True:              auto-take a loan to cover the shortfall.
    """
    logger.debug("Establishing MoneyTransfer rules")
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
    def resolve(sender: Player | None, receiver: Player | None, amount: int, mandatory: bool) -> MoneyActionResult:
        """
        Apply the transfer. Only call this after can_transfer returns True.
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
            return MoneyActionResult(
                outcome = Outcome.OK,
                log=log,
                state_changes=changes
            )
        
        # Handle loans if necessary
        elif sender.money < amount:
            while sender.money < amount:
                sender._take_loan()
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
            return MoneyActionResult(
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
            return MoneyActionResult(
                outcome = Outcome.LOAN if loan_needed else Outcome.OK,
                log=log,
                state_changes=changes
            )

logger.debug("Finished importing rules.rules module")