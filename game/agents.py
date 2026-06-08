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
    name: str # The name of the instruction for human comprehension
    order: classmethod | None # The direct object to interact with
    primary_response: bool # Is this response expected to end the turn?
    args: list # list of all arguments to be passed when the game calls the engine

@dataclass
class Agent:
    from game.data.factions import Player
    from game.data.common import GameState
    faction: Player
    name = 'Template Agent'

    def extract_options(self, options_dict: dict):
        """
        reads the options dictionary passed in the ContextCall
        and splits it into a list of possible actions
        """
        logger.debug('Extracting options from ContextCall')
        possible = []
        for name, tpl in options_dict.items():
            cls = tpl[0]
            CR = tpl[1]
            if CR.validity == True:
                possible.append((name, cls, CR))
        logger.debug(f"Extracted options: {possible}")
        return possible

    def call(self, call: ContextCall):
        """
        Determines the behaviour when the agent is called by the DecisionContext
        """
        logger.debug(f"Call made to {self.name}")
        logger.debug(f"Call options: {call.options}")

        # Validation
        if call.faction != self.faction:
            logger.error(f"call containing {call.faction.faction} sent to {self.faction.faction}")
            raise Exception("Context call Players do not match")
        
        # Decision Orchestration
        possible_options = self.extract_options(call.options)
        if len(possible_options) == 0:
            raise Exception('No response from agent is possible')
        logging.debug(f"Call options = {possible_options}")

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
        answer = AgentAnswer(options[0], options[1], True, [])
        return answer
    
    def election(self, gamestate: GameState, options: list):
        logger.debug("Agent's election process called")
        #       - Some logic
        answer = AgentAnswer(options[0], options[1], True, [])
        return answer

@dataclass
class RandomAgent(Agent):
    operator = 'Script'
    name = 'Randy Random'

    def action(self, gamestate, options):
        logger.debug("Agent's action process called")
        import random
        action_choice = random.choice(options)
        logger.error(f"ACTION_CHOICE = {action_choice}")
        if options[-1].actiontype == 'Free':
            primary = False
        else:
            primary = True
        answer = AgentAnswer(
            action_choice[0],
            action_choice[1],
            primary, 
            []
            )
        return answer
    



agent_refs = {
    'Random': RandomAgent
}