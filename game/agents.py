import logging
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass

@dataclass
class ContextCall:
    """
    Simple class to contain information sent to the agent

    Attributes
        gamestate: GameState
        faction: Player
        role: str
        options: dict of all actions, regardless of validity (name: (classmethod, checkresult))
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
    
    Attributes
        name: str
        order: classmethod
        primary_response: bool
        args: list
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

    def extract_options(self, options_dict: dict) -> dict:
        """
        reads the options dictionary passed in the ContextCall
        and splits it into a list of possible actions
        """
        logger.debug('Extracting options from ContextCall')
        possible = {}
        for name, tpl in options_dict.items():
            method = tpl[0]
            check = tpl[1]
            if check.validity:
                possible[name] = (method, check)
        logger.debug(f"Extracted options: {possible}")
        return possible

    def call(self, call: ContextCall) -> AgentAnswer:
        """
        Determines the behaviour when the agent is called by the DecisionContext
        """
        logger.debug(f"Call made to {self.name}")
        logger.debug(f"Call options: {call.options}")

        # Validation
        if call.faction != self.faction:
            logger.error(f"call meant for {call.faction.faction} sent to {self.faction.faction}")
            raise Exception("Context call Players do not match")
        
        # Decision Orchestration
        possible_options = self.extract_options(call.options)
        if len(possible_options.keys()) == 0:
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

    
    def action(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's action process called")
        #       - Some logic
        key = list(options.keys())[0]
        method = options[key][0]
        primary_bool = True if options[key][1].actiontype == 'Main' else False
        params = options[key][1].params
        
        answer = AgentAnswer(key, method, primary_bool, params)
        return answer
    
    def election(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's election process called")
        #       - Some logic
        answer = AgentAnswer(options[0], options[1], True, [])
        return answer

@dataclass
class RandomAgent(Agent):
    from game.data.common import GameState
    operator = 'Script'
    name = 'Randy Random'

    def action(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's action process called")
        import random

        key = random.choice(list(options.keys()))
        logger.debug(f"Action choice = {key}")
        method = options[key][0]
        primary_bool = True if options[key][1].actiontype == 'Main' else False
        params = options[key][1].params

        answer = AgentAnswer(key, method, primary_bool, params)
        return answer
    



agent_refs = {
    'Random': RandomAgent
}