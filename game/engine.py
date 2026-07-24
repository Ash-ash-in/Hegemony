import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from game.data.classes import Config

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

class Context:
    """
    Parent Class for all Context types.
    Child classes must compose all data for a ContextCall
    
    Ingests the least amount of variables, so that they can be parsed downstream
    """
    from game.states import Player, GameState
    from game.agents import Agent
    from game.context import AgentAnswer
    import itertools
    seq_gen = itertools.count()
    def __init__(
            self,
            gamestate: GameState, 
            player: Player
        ):
        # Update State
        from game.context import BasicMaskedState
        self.masked_state = BasicMaskedState(gamestate, player)
        # Context Metadata
        self.seq = next(self.seq_gen)
        self.game_id = gamestate.game_id
        self.parent_seq = self.seq
        self.faction = player.faction
        self.agent_type = player.agent.name # type: ignore
        self.action_in_progress = {}
        self.decision_type = ""
        self.step = (0,0)
        self.parent_name = ""
        self.available_choices = {}
        # Context internal attributes (not included in ContextCall)
        self.references = {} # Objects and methods for easy selection
        # self.compile_options(player)
        # while self.step[0] < self.step[1]:
        #     self.call(player.agent) # type: ignore
        #     self.execute()

    def compile_options(self, player: Player) -> dict:
        raise Exception("Parent compile_options method called")
        
    def call(self, agent: Agent) -> AgentAnswer:
        raise Exception("Parent call method called")
    
    def execute(self, gamestate: GameState, player: Player) -> None:
        raise Exception("Parent execute method called")

class ActionContext(Context):
    """
    Handles action decsisions
    - Contains context instance for action decision
    - Calls agent to choose
    - Initialises context for chosen action
    - Runs until action is complete
    """
    from game.agents import Agent
    from game.states import GameState, Player
    from game.context import AgentAnswer

    def __init__(
            self,
            gamestate: GameState, 
            player: Player
        ):
        logger.debug('New ActionContext')
        super().__init__(gamestate, player)
        self.decision_type = "choose_action"
        self.step = (1,2)
        self.parent_name = ""
        # while self.step[0] < self.step[1]:
        #     self.compile_options(player)
        #     self.call(player.agent) # type: ignore
        #     self.execute(gamestate, player)

    def compile_options(self, player: Player) -> dict:
        """
        Takes the list of attributes from the Action classes
        Looks for a 'check' method (which all actions should have)
        Runs the check and records the result
        Classes with a valid check are appended to self.available_choices
        """
        logger.debug("Compiling ActionContext options")
        import inspect
        from game.rules import FreeAction, MainAction

        self.available_choices["action"] = []

        # Determine what actions have already been taken
        if len(self.action_in_progress.keys()) > 0:
            if self.action_in_progress[self.step[0] - 1] in self.references["free_action"]:
                allowed_free = False
                allowed_main = True
            else:
                allowed_free = True
                allowed_main = False
        else:
            allowed_free = True
            allowed_main = True

        # Compile free actions from rules
        if allowed_free:
            self.references["free_action"] = {}
            for name, clsmthd in inspect.getmembers(FreeAction, inspect.isclass):
                if hasattr(clsmthd, "check"):
                    if clsmthd.check(player).validity:
                        self.references["free_action"][name] = clsmthd
                        self.available_choices["action"].append(name)

            # Create a default option if only free action is available
            if not allowed_main:
                self.references["free_action"]['None'] = None
                self.available_choices["action"].append("None")

        # Compile main actions from rules
        if allowed_main:
            self.references["main_action"] = {}
            for name, clsmthd in inspect.getmembers(MainAction, inspect.isclass):
                if hasattr(clsmthd, "check"):
                    if clsmthd.check(player).validity:
                        self.references["main_action"][name] = clsmthd
                        self.available_choices["action"].append(name)

        logger.debug(f'Compiled ActionContext options for {player.faction}')
        return self.available_choices
    
    def call(self, agent: Agent) -> AgentAnswer:
        """
        - Activates the agent's call function 
        - Updates self with response data
        - Activate the relevent action's context function
        - Increases step iterator
        """
        from game.context import ContextCall

        # Call the agent
        logger.debug("ActionContext making call to agent")
        call = ContextCall(
            self.masked_state, self.seq, self.game_id, self.parent_seq, 
            self.faction, self.agent_type, self.action_in_progress, self.decision_type,
            self.step, self.parent_name, self.available_choices
        )
        answer = agent.call(call)

        # Build refs from answer
        action_name = answer.answer["action"]
        action_method = None
        for action_type, name_method_dict in self.references.items():
            if action_name in name_method_dict.keys():
                action_method = name_method_dict[action_name]
                break
        if action_method is None:
            raise Exception("Action not found in context references")
        logger.info(f"Agent selected: {action_name}")

        # Update self with response
        self.action_in_progress[self.step[0]] = answer.answer["action"]
        self.answer = answer
        self.action_method = action_method
        self.action_type = action_type
        self.action_name = action_name
        return answer

    def execute(self, gamestate: GameState, player: Player) -> None:
        """Manages interactions with all top-level action classes"""
        
        # Handle 'None' free_action
        if self.action_method == None:
            return
        
        # if self.action_name == "TestAction1":
        #     self.action_method.execute()
        # elif self.action_name == "TestAction2":



class Engine:
    from game.states import GameState

    def setup_gamestate(self, config: Config):
        logger.debug("Establishing gamestate in engine")
        from game.states import GameState

        # Validity Checks
        if config.player_count < 2 or config.player_count > 4:
            raise Exception('player count must be between 2 and 4')
        if config.player_count != len(config.agents.keys()):
            raise Exception("player_count and agents mismatch")
        
        # Setup Players
        logger.debug("Setting up players within gamestate setup")
        from game.states import WorkingClass, MiddleClass, Capitalists, PlayerState, NPCState
        players = {}
        players["Working Class"] = WorkingClass()
        if config.player_count == 2:
            players["Capitalists"] = Capitalists()
        else:
            players["Middle Class"] = MiddleClass()
            players['Capitalists'] = Capitalists()
        if config.player_count == 4:
            players["State"] = PlayerState()
        else:
            players["State"] = NPCState()
        

        # Setup GameState
        gamestate = GameState(
                players,
                config.player_count,
                config.game_id
            )

        return gamestate

    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances according to those defined in the dictionary passed.
        Agents can be found in the engine, or in the player objects
        This modifies the engine and players in-place
        """
        logger.debug("Setting up agents")
        from game.agents import agent_refs
        from game.data.references import faction_play_order
        agent_references = {}
        for faction, agent_name in faction_agents.items():
            if faction not in faction_play_order:
                raise Exception(f"{faction} not recognised")
            if agent_name not in agent_refs.keys():
                raise Exception(f"{agent_name} not recognised")
            faction_instance = gamestate.players[faction]
            agent_references[faction] = agent_refs[agent_name](faction_instance)
            faction_instance.agent = agent_references[faction]
        self.agents = agent_references
        return
    
    def engine_startup(self, config) -> GameState:
        """Runs all the engine setup functions"""
        logger.debug("Executing engine startup")
        gamestate = self.setup_gamestate(config)
        self.setup_agents(config.agents, gamestate)
        return gamestate

    @staticmethod
    def start_position(gamestate: GameState): 
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a brand new game.
        """
        logger.debug('Called Engine.start_position')
        import game.rules as rules

        # Build player refs
        for name, cls in gamestate.players.items():
            if name == "Working Class":
                working_class = cls
            elif name == "Middle Class":
                middle_class = cls
            elif name == "Capitalists":
                capitalists = cls
            elif name == "State":
                state = cls
            else:
                raise Exception("Unrecognised faction")

        ####################################
        ### TEMPORARY give everyone 120 ####
        for name, inst in gamestate.players.items():
            if rules.MoneyTransfer.check(None, inst, 120, True).validity:
                rules.MoneyTransfer.resolve(None, inst, 120, True)
        logger.debug('Temporary start position money complete')
        ### TEMPORARY give everyone 120 ####
        ####################################


    def preparation_phase(self, gamestate: GameState):
        """
        Runs the system - driven preparation actions.
        All actions are mandatory.
        """
        logger.debug('Called Engine.preparation_phase')
        return gamestate
    

    def action_phase(self, gamestate: GameState):
        """
        Handles the process for calling the DecisionContext and sending commands downstream
        
        WARNING: This modifies GameState's 'turn', 'active_player', and 'free_action_taken' in place.
        WARNING: This replaces the GameState based on ~decisions taken~
        """
        from game.context import ActionContext
        from game.data.references import faction_play_order
        logger.debug('Called Engine.action_phase')

        ### Start the Action Phase ###

        for turn_num in range(1,6):
            logger.info(f'Starting action phase turn {turn_num}')
            gamestate.turn = turn_num # Update for save file
            for faction_name in faction_play_order:
                if faction_name == 'State' and gamestate.player_count < 4:
                    continue
                if faction_name == "Middle Class" and gamestate.player_count < 3:
                    continue
                logger.info(f"It's the {faction_name}'s turn")
                gamestate.active_player = faction_name
                player = gamestate.players[faction_name]

                # Call the agent
                agent = self.agents[player.faction]
                context = ActionContext(gamestate, player)
                answer = context.call(agent)

                # Build refs from answer
                action_name = answer.answer["action"]
                for action_type, name_method_dict in context.references.items():
                    if action_name in name_method_dict.keys():
                        action_method = name_method_dict[action_type]
                        break
                    raise Exception("Action not found in context references")
                if action_method is None:
                    raise Exception('Order "None" response given before any action taken')
                logger.info(f"Agent selected: {action_name}")

                # Build Context for action requred
                

                # Check for a free action following a main
                if answer.primary_response == True:
                    answer = ActionContext.action_call(agent, False, True, gamestate, player)
                    if answer.order is None:
                        continue
                    args = [player] + answer.args
                    mini_log = f"Enacting {answer.name}."
                    if len(answer.args) > 0:
                        mini_log += f" Args = {answer.args}"
                    logger.info(mini_log)
                    answer.order.resolve(*args)      
                
                # Otherwise demand a main action response
                elif answer.primary_response == False:
                    answer = ActionContext.action_call(agent, True, False, gamestate, player)
                    if answer.order is None:
                        raise Exception('Main action required, None cannot be passed')
                    else:
                        args = [player] + answer.args
                        mini_log = f"Enacting {answer.name}."
                        if len(answer.args) > 0:
                            mini_log += f" Args = {answer.args}"
                        logger.info(mini_log)
                        answer.order.resolve(*args) 

        return gamestate

    @staticmethod
    def production_phase(gamestate: GameState):
        logger.debug('Called Engine.production_phase')
        return gamestate

    @staticmethod
    def elections_phase(gamestate: GameState):
        logger.debug('Called Engine.elections_phase')
        return gamestate

    @staticmethod
    def scoring_phase(gamestate: GameState):
        logger.debug('Called Engine.scoring_phase')
        return gamestate

    @staticmethod
    def endgame_scoring(gamestate: GameState):
        logger.debug('Called Engine.endgame_scoring')
        return gamestate

    def flow(self, gamestate: GameState):
        """
        Main Execution of game. Runs constantly during play.

        WARNING: This modifies GameState's 'round' and 'phase' in place.
        """
        logger.debug('Called Engine.flow')
        from game.data.common import phases

        for round in range(0,6):
            logger.info(f'Starting Round {round}')
            gamestate.round = round

            if round == 0:
                self.start_position(gamestate)
                continue

            for phase in phases:

                if phase == phases[0] and round == 1:
                    continue # First round gets no preparation phase
                
                logger.info(f'Begining phase: {phase}')

                if phase == phases[0]:
                    gamestate = self.preparation_phase(gamestate)
                elif phase == phases[1]:
                    gamestate = self.action_phase(gamestate)
                elif phase == phases[2]:
                    gamestate = self.production_phase(gamestate)
                elif phase == phases[3]:
                    gamestate = self.elections_phase(gamestate)
                elif phase == phases[4]:
                    gamestate = self.scoring_phase(gamestate)

        gamestate = self.endgame_scoring(gamestate)
