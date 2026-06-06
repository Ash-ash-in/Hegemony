import logging
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass

@dataclass
class ContextCall:
    """
    Simple class to contain information sent to the agent
    """
    from game.data.common import GameState
    from game.data.factions import Player
    gamestate: GameState
    faction: Player # Player object the agent is controlling
    role: str # The type of decision that needs to be made eg. actions, voting
    options: dict # Contains all the actions, whether they are valid, and if not, why not

@dataclass
class AgentAnswer:
    """
    Simple class to contain information sent from an agent to the game engine
    """
    action: str # MAYBE?? or some type of object/instance?
    args: list # list of all arguments to be passed when the game calls the engine

@dataclass
class Agent:
    from game.data.factions import Player
    from game.data.common import GameState
    faction: Player

    def extract_options(self, options_dict: dict):
        """
        reads the options dictionary passed in the ContextCall
        and splits it into a list of possible actions
        """
        logger.debug('Extracting options from ContextCall')
        possible = []
        for action_class, check_result in options_dict.items():
            if check_result[0] == True:
                possible.append(action_class)
        return possible

    def call(self, call: ContextCall):
        """
        Determines the behaviour when the agent is called by the DecisionContext
        """
        logger.debug(f"Call made to {self.name}")
        # Validation
        if call.faction != self.faction:
            logger.error(f"call containing {call.faction.faction} sent to {self.faction.faction}")
            raise Exception("Context call Players do not match")
        
        # Decision Orchestration
        possible_options = self.extract_options(call.options)
        if len(possible_options) == 0:
            return AgentAnswer('None', [])
        print(f"Call options = {possible_options}")
        if call.role == 'Action':
            answer = self.action(call.gamestate, possible_options)
        elif call.role == 'Election':
            answer = self.election(call.gamestate, possible_options)
        #       -more calls to role-specific methods as they are created
        else:
            raise Exception('Role not understood from ContextCall')
        
        return answer

    
    def action(self, gamestate: GameState, options: list):
        logger.debug("Agent's action process called")
        #       - Some logic
        answer = AgentAnswer('some answer', [])
        return answer
    
    def election(self, gamestate: GameState, options: list):
        logger.debug("Agent's election process called")
        #       - Some logic
        answer = AgentAnswer('some answer', [])
        return answer

@dataclass
class RandomAgent(Agent):
    operator = 'Script'
    name = 'Randy Random'

    def action(self, gamestate, options):
        logger.debug("Agent's action process called")
        import random
        answer = AgentAnswer(
            random.choice(options), []
            )
        return answer
    



agent_refs = {
    'Random': RandomAgent
}