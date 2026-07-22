import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

# Setup Decision Log
decision_log = []

@dataclass
class Agent:
    """
    This is a template agent to provide the core functionality of the agents
    
    Many of their methods will be overwritten by its subclasses.

    If this agent is actually used, it will just pick the first option every time.
    """
    from game.states import GameState, Player
    from game.context import ContextCall, AgentAnswer, BasicMaskedState
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

    def call(self, call: ContextCall) -> AgentAnswer:
        """
        Determines the behaviour when the agent is called by the DecisionContext

        Its basically a triage for incoming calls
        """
        logger.debug(f"Call made to {self.name}")

        # Validation
        if call.faction != self.faction:
            logger.error(f"call meant for {call.faction} sent to {self.faction}")
            raise Exception("Context call Players do not match")
        if len(call.available_choices.keys()) == 0:
            raise Exception("No types of response were requested of the agent. Ensure context.available_choices is updated.")
        for response_type, options in call.available_choices.items():
            if len(options) <= 0:
                raise Exception(F'No response from agent is possible when selection {response_type}. Consider adding "None" option')
        
        # Decision Orchestration
        # if call.decision_type == "choose_action":
        #     answer = self.action(call.masked_state, call.available_choices)
        # elif call.decision_type == 'Election':
        #     answer = self.election(call.masked_state, call.available_choices)
        # elif call.decision_type == 'Worker':
        #     answer = self.spawn_worker(call.masked_state, call.available_choices)
        #       -more calls to role-specific methods as they are created
        # else:
        #     raise Exception('Role not understood from ContextCall')

        # Normally you would forward the answer from the commented section above.
        # To ease development, we will just return an empty answer for now
        return self.AgentAnswer({})

    def spawn_worker(self, masked_state: BasicMaskedState, options: dict) -> AgentAnswer:
        """Used to decide which worker to spawn"""
        logger.debug("Agent's worker process called")
        from game.context import AgentAnswer
        answer = AgentAnswer({})
        return answer

    def action(self, masked_state: BasicMaskedState, options: dict) -> AgentAnswer:
        logger.debug("Agent's action process called")
        from game.context import AgentAnswer
        answer = AgentAnswer({})
        return answer
    
    def election(self, masked_state: BasicMaskedState, options: dict) -> AgentAnswer:
        logger.debug("Agent's election process called")
        from game.context import AgentAnswer
        answer = AgentAnswer({})
        return answer

@dataclass
class RandomAgent(Agent):
    from game.states import GameState
    from game.context import ContextCall, AgentAnswer
    operator = 'Script'
    name = 'Randy Random'

    def call(self, call: ContextCall) -> AgentAnswer:
        """
        Rather than triaging, Randy just loops through all options and picks one at random.
        """
        logger.debug(f"Call made to {self.name}")
        import random as rand
        from game.context import AgentAnswer, DecsionLogEntry

        # Validation
        if call.faction != self.faction:
            logger.error(f"call meant for {call.faction} sent to {self.faction}")
            raise Exception("Context call Players do not match")
        if len(call.available_choices.keys()) == 0:
            raise Exception("No types of response were requested of the agent. Ensure context.available_choices is updated.")
        for response_type, options in call.available_choices.items():
            if len(options) <= 0:
                raise Exception(f'No response from agent is possible when selection {response_type}. Consider adding "None" option')

        # Option Selection
        answer = {}
        for request_type, options in call.available_choices.items():
            answer[request_type] = rand.choice(options)

        response = AgentAnswer(answer)
        decision_log.append(DecsionLogEntry(call, response))
        return response

agent_refs = {
    'Random': RandomAgent
}

