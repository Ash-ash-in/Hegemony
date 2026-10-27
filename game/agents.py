"""
# game/agents.py

    This file contains everything to do with Agent classes.

## Generic Process
- Extract options passed in the Context Call
- Triage incoming calls, to decide which of its internal processes should handle it.
- The internal process uses its decision logic to select an answer
- The decision is appended to the log
- The AgentAnswer is returned

## Hierarchy
Sits above:
- messages.py
Sit alongside (no interaction):
- context.py
- rules.py
Sits below:
- engine.py
- HEGEMONY.py
"""

import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass
import game.assets.messages as m

@dataclass
class Agent:
    """
    This is a template agent to provide the core functionality of the agents
    
    Many of their methods will be overwritten by its subclasses.

    If this agent is actually used, it will just pick the first option every time.
    """
    from game.states import GameState, Player
    player: Player
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

    def call(self, call):
        """
        Determines the behaviour when the agent is called by the DecisionContext
        - Validates incoming calls
        - Triages incoming calls by activating the relevent method
        - Appends the call and answer to the decision log
        """
        logger.debug(f"Call made to {self.name}")

        # Check dtypes (done here to avoid circular imports)
        if not isinstance(call, m.ContextCall):
            raise Exception(TypeError)

        # Validation
        if call.faction != self.player.faction:
            logger.error(f"call meant for {call.faction} sent to {self.player.faction}")
            raise Exception("Context call Players do not match")
        if len(call.available_choices.keys()) == 0:
            raise Exception("No types of response were requested of the agent. Ensure context.available_choices is updated.")
        for response_type, options in call.available_choices.items():
            if len(options) <= 0:
                raise Exception(f'No response from agent is possible when selection {response_type}. Consider adding "None" option')
        
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
        return m.AgentAnswer({})

    def spawn_worker(self, masked_state, options: dict):
        """Used to decide which worker to spawn"""
        logger.debug("Agent's worker process called")
    
        # Check dtypes (done here to avoid circular imports)
        if not isinstance(masked_state, m.MaskedState):
            raise Exception(TypeError)

        answer = m.AgentAnswer({})
        return answer

    def action(self, masked_state, options: dict):
        logger.debug("Agent's action process called")
        
        # Check dtypes (done here to avoid circular imports)
        if not isinstance(masked_state, m.MaskedState):
            raise Exception(TypeError)        
        answer = m.AgentAnswer({})
        return answer
    
    def election(self, masked_state, options: dict):
        logger.debug("Agent's election process called")
        
        # Check dtypes (done here to avoid circular imports)
        if not isinstance(masked_state, m.MaskedState):
            raise Exception(TypeError)        
        answer = m.AgentAnswer({})
        return answer

@dataclass
class RandomAgent(Agent):
    from game.states import GameState
    operator = 'Script'
    name = 'Randy Random'

    def call(self, call):
        """
        Rather than triaging, Randy just loops through all options and picks one at random.
        The decision is still added to the log
        """
        logger.debug(f"Call made to {self.name}")
        import random as rand
        
        # Check dtypes (done here to avoid circular imports)
        if not isinstance(call, m.ContextCall):
            raise Exception(TypeError)    

        # Validation
        if call.faction != self.player.faction:
            logger.error(f"call meant for {call.faction} sent to {self.player.faction}")
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

        # Final Output
        response = m.AgentAnswer(answer, None, None)
        return response

agent_refs = {
    'Random': RandomAgent
}

