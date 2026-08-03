import logging
logger = logging.getLogger(__name__)
logger.debug("Importing rules.rules module")

from dataclasses import dataclass
from enum import Enum, auto
from game.old_game.old_factions import Player, WorkingClass, MiddleClass
from game.data.classes import GameState

######################### Utilities #######################################
class Outcome(Enum):
    OK = auto()
    INVALID = auto()
    LOAN = auto()
    INACTION = auto() # When nothing is a passable outcome eg. points cannot go lower

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
class CompanyFound:
    """
    Puts a company from one player's pool on to the board
    
    This handles the physical aspects of putting the card in place, but does not involve any exchange of money or assignment of workers.
    """
    logger.debug("called CompanyFound class")
    from game.old_game.old_factions import Player
    from game.data.classes import GameState, Company

    @staticmethod
    def check(player: Player, gamestate: GameState, comp: Company) -> CheckResponse:
        """
        ### Args
        player - the player to check
        gamestate
        comp_name - the name of the company to found
        """
        logger.debug("Called CompanyFound.check()")
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
        logger.debug("Called CompanyFound.resolve()")

        # Validation check
        if not CompanyFound.check(player, gamestate, comp).validity:
            raise Exception("CompanyFound resolve called but failed check")

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
        logger.debug(changes[-1])
        gamestate.companies[player.faction][slot] = comp
        changes.append(f'{comp.name} founded in {player.faction} company slot {slot[-1]}')
        logger.debug(changes[-1])
        log = f"{player.faction} founded {comp.name}"
        return ActionResult(Outcome.OK, log, changes)

@dataclass
class WorkerHire:
    """
    Moves a worker from the unemployment area to a company
    
    This handles the movement of a specific worker to a specific slot. 
    It does not check if this is wise.
    It does not check if this would result in a fully staffed company.
    It does not check if this would cause the source companies to become inactive.
    Handles checks related to worker skill and class.
    """
    logger.debug("called WorkerHire class")
    from game.data.classes import GameState, Company, Worker

    @staticmethod
    def check(gamestate: GameState, worker: Worker, target_company: Company, target_slot: int) -> CheckResponse:
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
        if target_company.workers[target_slot] is not None:
            return CheckResponse(False, "Slot already occupied", "Intermediate", [])
        if worker not in gamestate.unemployed_workers[worker.faction]:
            return CheckResponse(False, "Worker is not currently enemployed", "Intermediate", [])
        target_class = target_company.worker_slots[target_slot].faction
        target_skill = target_company.worker_slots[target_slot].skill
        if worker.faction != target_class and target_class != 'Any':
            return CheckResponse(False, "Worker class not suitable for slot", "Intermediate", [])
        if worker.skill != target_skill and target_skill != 'Any':
            return CheckResponse(False, "Worker does not have the appropriate skill", "Intermediate", [])
        if worker.committed:
            raise Exception("Unemployed workers cannot be committed")
            return CheckResponse(False, "Worker is committed", "Intermediate", [])
        return CheckResponse(True, "", "Intermediate", [])

    @staticmethod
    def resolve(gamestate: GameState, worker: Worker, target_company: Company, target_slot: int) -> ActionResult:
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
        if not WorkerHire.check(gamestate, worker, target_company, target_slot).validity:
            raise Exception("CompanyFound resolve called but failed check")

        ### Execute
        changes = []

        # Clear source slot
        gamestate.unemployed_workers[worker.faction].remove(worker)
        changes.append("Worker removed from unemployment area")

        # Add to new slot
        target_company.workers[target_slot] = worker
        changes.append(f"Worker added to {target_company.name} in worker slot {target_slot}")
        logger.debug(changes[-1])
        log = f"Unemployed worker hired at {target_company.name}"
        return ActionResult(Outcome.OK, log, changes)

@dataclass
class WorkerSpawn:
    """
    Handles birthing workers from the pool to the unemployment area
    """
    logger.debug("called WorkerSpawn class")
    from game.old_game.old_factions import WorkingClass, MiddleClass
    from game.data.classes import GameState

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
            return CheckResponse(False, f'{player.faction} does not have workers', 'Intermediate', [])
        if player.faction == 'Middle Class' and gamestate.player_count < 3:
            return CheckResponse(False, f'{player.faction} is not in the game', 'Intermediate', [])
        if len(gamestate.worker_pool[player.faction]) == 0:
            return CheckResponse(False, 'No workers available for this faction', 'Intermediate', [])
        found = False
        for worker in gamestate.worker_pool[player.faction]:
            if worker.skill == skill:
                found = True
                break
        if not found:
            return CheckResponse(False, 'No remaining workers of that skill', 'Intermediate', [])
        return CheckResponse(True, '', 'Intermediate', [])

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
        pop = player.population
        player._add_population()
        changes.append(f"{player.faction} population track adjusted")
        if player.population != pop:
            changes.append(f"{player.faction} population has increased")
        log = f'{player.faction} {worker.skill} worker spawned in unemployment area' # type: ignore
        return ActionResult(outcome=Outcome.OK, log=log, state_changes=changes)

@dataclass
class ImmigrationCardDraw:
    """
    Handles drawing of the card
    Spawning the worker
    Resetting the deck if empty
    """
    logger.debug("called ImmigrationCardDrawing")


    @staticmethod
    def check(gamestate: GameState, player: Player):
        logger.debug("called ImmigrationCardDraw.check")
        if player.faction in ('State','Capitalists'):
            return CheckResponse(False, f"{player.faction} cannot draw immigration cards", "Intermediate", [])
        return CheckResponse(True, "", "Intermediate", [])
    
    @staticmethod
    def resolve(gamestate: GameState, player: Player):
        logger.debug("Called ImmigrationCardDraw.resolve")
        check = ImmigrationCardDraw.check(gamestate, player)
        if not check.validity:
            raise Exception("Invalid call to resolve transfer. Ensure validity check is being called prior and is working.")
        changes = []

        # Redraw deck if no cards are left
        if len(gamestate.immigration_card_deck) == 0:
            gamestate.build_immigration_cards()
        
        # Draw a card
        card = gamestate.immigration_card_deck[0]
        gamestate.immigration_card_deck.remove(card)
        changes.append('Immigration card drawn')
        log = "Drew an immigration card"
        logger.debug("Immigration card removed from deck")

        # Spawn the worker
        if player.faction == 'Working Class':
            skill = card.WorkingClass.skill
        else:
            skill = card.MiddleClass.skill
        check = WorkerSpawn.check(gamestate, player, skill)

        # Request player decision if worker not available
        if not check.validity:
            logger.info(f"No {player.faction} worker available with skill: {skill}")
            if skill == 'Unskilled':
                # Request to agent
                from game.old_game.old_agents import Calls
                Calls.worker_call(gamestate, player, player.agent)
                # assign answer to 'skill'
                pass # temp
            else:
                skill = 'Unskilled'
            # Now handling the alternative skill
            check = WorkerSpawn.check(gamestate, player, skill)
            if not check.validity:
                log += ", but there were no workers available"
                return ActionResult(Outcome.INACTION, log, changes)

        inner_response = WorkerSpawn.resolve(gamestate, player, skill)
        changes += inner_response.state_changes
        return ActionResult(Outcome.OK, log, changes)
        

############################# Action Layer ########################################

logger.debug("Finished importing rules.rules module")