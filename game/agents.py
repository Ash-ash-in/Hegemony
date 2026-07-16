import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

@dataclass
class Agent:
    """
    This is a template agent to provide the core functionality of the agents
    
    Many of their methods will be overwritten by its subclasses.

    If this agent is actually used, it will just pick the first option every time.
    """
    from game.states import GameState, Player
    from game.context import Context, AgentAnswer
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
        return possible

    def call(self, call: Context) -> AgentAnswer:
        """
        Determines the behaviour when the agent is called by the DecisionContext

        Its basically a triage for incoming calls
        """
        logger.debug(f"Call made to {self.name}")

        # Validation
        if call.faction != self.faction:
            logger.error(f"call meant for {call.faction.faction} sent to {self.faction.faction}")
            raise Exception("Context call Players do not match")
        
        # Decision Orchestration
        possible_options = self.extract_options(call.options)
        if len(possible_options.keys()) == 0:
            raise Exception('No response from agent is possible')

        if call.role == 'Action':
            answer = self.action(call.gamestate, possible_options)
        elif call.role == 'Election':
            answer = self.election(call.gamestate, possible_options)
        elif call.role == 'Worker':
            answer = self.spawn_worker(call.gamestate, possible_options)

        #       -more calls to role-specific methods as they are created
        else:
            raise Exception('Role not understood from ContextCall')
        return answer

    def spawn_worker(self, gamestate: GameState, options: dict) -> AgentAnswer:
        """Used to decide which worker to spawn"""
        logger.debug("Agent's worker process called")
        from game.context import AgentAnswer
        key = list(options.keys())[0]
        method = options[key][0]
        primary_bool = True
        params = options[key][1].params
        
        answer = AgentAnswer(key, method, primary_bool, params)
        return answer

    def action(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's action process called")
        from game.context import AgentAnswer
        key = list(options.keys())[0]
        method = options[key][0]
        primary_bool = True if options[key][1].actiontype == 'Main' else False
        params = options[key][1].params
        
        answer = AgentAnswer(key, method, primary_bool, params)
        return answer
    
    def election(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's election process called")
        from game.context import AgentAnswer
        #       - Some logic
        answer = AgentAnswer(options[0], options[1], True, [])
        return answer

@dataclass
class RandomAgent(Agent):
    from game.states import GameState
    from game.context import ContextCall, AgentAnswer
    operator = 'Script'
    name = 'Randy Random'

    def action(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's action process called")
        import random
        from game.context import AgentAnswer

        key = random.choice(list(options.keys()))
        logger.debug(f"Action choice = {key}")
        method = options[key][0]
        primary_bool = True if options[key][1].actiontype == 'Main' else False
        params = options[key][1].params

        answer = AgentAnswer(key, method, primary_bool, params)
        return answer
    
    def spawn_worker(self, gamestate: GameState, options: dict) -> AgentAnswer:
        logger.debug("Agent's worker process called")
        import random
        from game.context import AgentAnswer

        key = random.choice(list(options.keys()))
        logger.debug(f"Worker choice = {key}")
        method = options[key][0]
        primary_bool = True if options[key][1].actiontype == 'Main' else False
        params = options[key][1].params

        answer = AgentAnswer(key, method, primary_bool, params)
        return answer


agent_refs = {
    'Random': RandomAgent
}

