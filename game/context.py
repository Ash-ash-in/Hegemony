from dataclasses import asdict, dataclass
import logging
from typing import Any
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActionContext:
    """
    Checks what is available when making an action.
    Seperate methods for different types of agent.
    """
    logger.debug('Called ActionContext')
    from game.factions import Player
    from game.agents import Agent, AgentAnswer
    from game.data.classes import GameState

    @staticmethod
    def compile_options(player: Player, allowed_free: bool, allowed_main: bool) -> dict:
        """
        Takes the list of attributes from the Action classes
        Looks for a 'check' method (which all actions should have)
        Runs the check and records the result

        The result is a dict - string: (classmethod, CheckResponse)
        """
        logger.debug("called DecisionContext.ActionContext.compile_options()")
        from game.rules import FreeAction, MainAction, CheckResponse

        context = {}

        # Compile free actions from rules
        if allowed_free:
            free_options = FreeAction.context(player)
            context = {**context, **free_options}
            logging.debug(f"Options from FreeAction.context(): {free_options}")

            if allowed_main: # Create a default option to pass regardless
                context['None'] = (None,CheckResponse(False, "", "Free", []))
            else: # Create a way to not perform anything if necessary
                context['None'] = (None,CheckResponse(True, "", "Free", []))

        # Compile main actions
        if allowed_main:
            main_options = MainAction.context(player)
            context = {**context, **main_options}
            logging.debug(f"Options from MainAction.context(): {main_options}")

        logger.debug(f'Compiled ActionContext options for {player.faction}')
        return context
    
    # Setup call process in one function for reusability
    @staticmethod
    def action_call(agent: Agent, allowed_main: bool, allowed_free: bool, gamestate: GameState, player: Player):
        """
        Builds a context call for an action, calls the agent, and returns the response
        """
        logger.debug("Engine.Calls.action_call called")
        from game.agents import ContextCall

        # Build options and prepare to call agent
        all_options = ActionContext.compile_options(player, allowed_free, allowed_main)
        call = ContextCall(
            gamestate,      # Instance
            player,         # Instance
            'Action',       # String
            all_options     # Dictionary - str: class
        )

        # Call the agent for a reponse
        answer = agent.call(call)
        logging.debug(f"Answer: {answer}")
        return answer

@dataclass
class SimpleContext:
    from game.data.classes import GameState
    from game.factions import Player
    from game.agents import Agent, AgentAnswer

    
    @staticmethod
    def spawn_worker_call(gamestate: GameState, player: Player, agent: Agent) -> AgentAnswer:
        """
        Checks the worker pool for a players available skills, and sends it to the agent
        """
        logger.debug("Engine.Call.worker_call called")
        from game.data.classes import industries
        from game.rules import CheckResponse
        from game.agents import ContextCall

        skilldict = {'Unskilled':0}
        for skill in industries:
            skilldict[skill] = 0
        for worker in gamestate.worker_pool[player.faction]:
            skilldict[worker.skill] += 1
        
        answerdict = {}
        for skill, val in skilldict.items():
            if val > 0:
                answerdict[skill] = (skill, CheckResponse(True, "", "Worker", []))
            else:
                answerdict[skill] = (skill, CheckResponse(False, "No workers available", "Worker", []))

        call = ContextCall(gamestate, player, "Worker", answerdict)
        answer = agent.call(call)
        return answer




    