import logging
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass

@dataclass
class ContextCall:
    """
    Simple class to contain information sent to the agent
    """
    from game.data.factions import Player
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
    operator: str # Human, Script, NN
    name: str # Unique name for the agent
    from game.data.factions import Player

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
        possible_options = self.extract_options(call.options)
        if call.role == 'Action':
            answer = self.action(call.faction, possible_options)
        #       -more calls to role-specific methods as they are created
        else:
            raise Exception('Role not understood from ContextCall')
        
        return answer

    
    def action(self, player: Player, options: list):
        #       - Some logic
        answer = AgentAnswer('Action', [])
        return answer

