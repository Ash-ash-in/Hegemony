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


class MoneyTransfer:
    """
    Handles both mandatory and optional transfers.

    mandatory=False (optional):  block the transfer if sender can't afford it.
    mandatory=True:              auto-take a loan to cover the shortfall.
    """
    logger.debug("Establishing MoneyTransfer rules")
    from game.data.factions import Player

    @staticmethod
    def can_transfer(sender: Player, receiver: Player, amount: int, mandatory: bool) -> tuple[bool,str]:
        if amount <= 0:
            return False, "Amount must be positive"
        if sender is receiver:
            return False, "Cannot transfer to yourself"
        if sender.money >= amount:
            return True, ""
        
        # For senders with insufficient funds:
        shortfall = sender.money - amount
        if not mandatory:
            return False, f"{sender.faction} cannot afford transaction. Needs {shortfall} more"
        return True, ""
    
    @staticmethod
    def resolve(sender: Player, receiver: Player, amount: int, mandatory: bool) -> MoneyActionResult:
        """
        Apply the transfer. Only call this after can_transfer returns True.
        All mutations happen here — never partially applied.
        """
        # Confirm validity
        valid, reason = MoneyTransfer.can_transfer(sender,receiver,amount,mandatory)
        if not valid:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is working")
            return MoneyActionResult(
                outcome=MoneyOutcome.INVALID,
                log=reason,
                state_changes=[]
            )
        
        # Take loans if neccessary
        changes = []
        loan_needed = False
        if sender.money < amount:
            loan_count = 0
            while sender.money < amount:
                sender._take_loan()
                loan_count += 1
            changes.append(f"{sender.faction} took {loan_count} loan{'s' if loan_count > 1 else ''}")
            loan_needed = True

        # Transfer the money
        sender._add_money(amount * -1)
        changes.append(f"{sender.faction} money: {sender.money}")
        receiver._add_money(amount)
        changes.append(f"{receiver.faction} money: {receiver.money}")

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