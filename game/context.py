"""
This module pertains to every part of making a call to an agent
- Masking the gamestate
- Building the file format (Context) to send
- Activating the agent's call function
- Updating the Context with the response
- Adding rewards?
- Saving all communications for model training
- Summarising game for victory rewards and grouping sequences
"""
import logging
logger = logging.getLogger(__name__)

from typing import Any
from dataclasses import dataclass
from game.states import GameState, Player
from game.rules import ActionResult


@dataclass
class MaskedState:
    """
    Masked representation of GameState.

    The nested sections are dictionaries rather than nested dataclasses,
    so asdict(MaskedState(...)) produces a normal nested dictionary.
    """

    GameMetaData: dict[str, Any]
    BoardData: dict[str, Any]
    PlayerData: dict[str, Any]
    Faction: dict[str, Any]

    def __init__(self, gamestate: GameState, player: Player) -> None:

        self.GameMetaData = {
            "player_count": gamestate.player_count,
            "round": gamestate.round,
            "phase": gamestate.phase,
            "turn": gamestate.turn,
            "player_turn": gamestate.active_player,
        }

        self.BoardData = {
            "worker_pool": gamestate.worker_pool,
            "storages": gamestate.storages,
            "election_cubes": gamestate.election_cubes,
            "unemployed_workers": gamestate.unemployed_workers,
            "companies": gamestate.companies,
            "unions": gamestate.unions,
            "laws": gamestate.laws,
            "tariff_level": gamestate.tariff_level,
            "voting_area": gamestate.voting_area,
            "demonstration": gamestate.demonstration,
            "business_deals": gamestate.active_business_deals,
            "export_card": gamestate.active_export_card,
        }

        # If you want one entry per player, use a dictionary keyed by
        # whatever uniquely identifies the player.
        self.PlayerData = {}

        for player_id, player_data in gamestate.players.items():
            data = {
                "faction": player_data.faction,
                "victory_points": player_data.victory_points,
                "money": player_data.money,
                "loans": player_data.loans,
                "resources": player_data.resources,
                "influence": player_data.influence,
                "market": player_data.market,
            }

            if player_data.faction in ("Working Class", "Middle Class"):
                data["population_track"] = player_data.population_track
                data["population"] = player_data.population
                data["prosperity"] = player_data.prosperity

            if player_data.faction == "Working Class":
                data["strike_tokens"] = player_data.strike_tokens
            else:
                data["storage"] = player_data.storage

            if player_data.faction == "Middle Class":
                data["prosperity_track"] = player_data.prosperity_track

            if player_data.faction in ("Middle Class", "Capitalists"):
                data["storages"] = player_data.storages

            if player_data.faction == "Capitalists":
                data["revenue"] = player_data.revenue
                data["capital"] = player_data.capital
                data["free_trade_zone"] = player_data.free_trade_zone
                data["machinery_tokens"] = player_data.machinery_tokens

            elif player_data.faction == "State" and gamestate.player_count == 4:
                data["legitimacy"] = player_data.legitimacy
                data["legitimacy_tokens"] = player_data.legitimacy_tokens

            self.PlayerData[player_id] = data

        self.Faction = {
            "faction": player.faction,
            "hand": player.hand,
        }
     
@dataclass
class ContextCall:
    """
    # ContextCall
    This class contains the infomation that is sent to an agent.
    This is the uniform call class that must be sent.
    Forcing all types on contexts to use the same call class ensures uniformity

    ### Game information
    - Meta information about the game itself
    - It must contain all necessary masked data (player hands, card decks etc.)
    - If must be perosonalised for the agent's faction
    - It should only contain the bare minimum representation of that data (eg. a law will be "6B")
    - It must contain "temporal" data of what stage of the game this is from

    ### Decision information
    - It needs to state what level of decision this is (primary, sub)
        - Assign Workers is primary
        - Each movement is a sub
    - It needs a unique ID for the request
    - It needs a parent ID for the main request, to keep subs grouped together
    - It needs to detail what action is in progress, and the actions taken so far (which workers are moved so far)
    - If needs to detail the actual options for the agent to make (which worker to move, and where)
    """
    masked_gamestate: MaskedState
    seq: int
    game_id: str
    parent_seq: int
    faction: str
    agent_type: str
    decision_in_progress: dict
    decision_type: str
    step: tuple
    parent_name: str
    available_choices: dict

@dataclass
class AgentAnswer:
    """
    # Agent Answer
    Simply contains the response for the agent

    This should be a simple dict that can be understood by the requester that made the call. 
    Dictionary values must be strings, so that the NN can read them. 
    This means objects and methods can't be passed directly, so they should be help in the context object and returned to the engine from there.

    Example: {"Worker": "WC1", "Slot": "Company3Slot2"}
    """
    answer: dict[str, str]
    value_estimate: float | None
    log_prob: float | None

class DecsionLogEntry:

    def __init__(self, call: ContextCall, response: AgentAnswer, reward = None, outcome = None) -> None:

        from dataclasses import asdict
        # Context at Observation
        self.call = asdict(call)

        # Response at Observation
        self.response = asdict(response)

        # Agent Evaluation
        self.reward = reward
        self.outcome = outcome


@dataclass
class GameSummary:

    game_id: str
    winner: str
    scores: dict[str,int]
    total_decisions: int

class Context:
    """
    Parent Class for all Context types.
    Child classes must compose all data for a ContextCall
    
    Ingests the least amount of variables, so that they can be parsed downstream
    """
    from game.states import Player, GameState
    from game.context import AgentAnswer
    import itertools
    seq_gen = itertools.count()
    def __init__(
            self,
            gamestate: GameState, 
            player: Player
        ):
        # Update State
        from game.context import MaskedState
        self.masked_state = MaskedState(gamestate, player)
        # Context Metadata
        self.seq = next(self.seq_gen)
        self.game_id = gamestate.game_id
        self.parent_seq = self.seq
        self.faction = player.faction
        self.agent_type = player.agent.name # type: ignore
        self.decision_in_progress = {}
        self.decision_type = ""
        self.step = (0,0)
        self.parent_name = ""
        self.available_choices = {}
        # Context internal attributes (not included in ContextCall)
        self.references = {} # Objects and methods for easy selection
        # while self.step[0] < self.step[1]:
        #     self.compile_options(gamestate, player)
        #     self.call(gamestate, player)
        #     self.execute(gamestate, player)

    def compile_options(self, gamestate: GameState, player: Player) -> None:
        raise Exception("Parent compile_options method called")
        
    def call(self, gamestate: GameState, player: Player) -> None:
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
    from game.states import GameState, Player

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
        while self.step[0] <= self.step[1]:
            self.compile_options(gamestate, player)
            self.call(gamestate, player)
            self.execute(gamestate, player)
            
    def compile_options(self, gamestate: GameState, player: Player) -> None:
        """
        Takes the list of attributes from the Action classes. 
        Looks for a 'check' method (which all actions should have). 
        Runs the check and records the result. 
        Classes with a valid check are appended to self.available_choices.
        """
        logger.debug("Compiling ActionContext options")
        import inspect
        from game.rules import FreeAction, MainAction

        self.available_choices["action"] = []

        # Determine what actions have already been taken
        if len(self.decision_in_progress.keys()) > 0:
            if self.decision_in_progress[str(self.step[0] - 1)] in self.references["free_action"]:
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
                    if clsmthd.check(gamestate, player).validity:
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
                    if clsmthd.check(gamestate, player).validity:
                        self.references["main_action"][name] = clsmthd
                        self.available_choices["action"].append(name)

        logger.debug(f'Compiled ActionContext options for {player.faction}')
        return
    
    def call(self, gamestate: GameState, player: Player) -> None:
        """
        - Activates the agent's call function 
        - Updates self with response data
        - Activate the relevent action's context function
        - Increases step iterator
        """

        # Call the agent
        logger.debug("ActionContext making call to agent")
        call = ContextCall(
            self.masked_state, self.seq, self.game_id, self.parent_seq, 
            self.faction, self.agent_type, self.decision_in_progress, self.decision_type,
            self.step, self.parent_name, self.available_choices
        )
        answer = player.agent.call(call)
        logger.info(f"Action selected: {answer.answer["action"]}")

        # Build refs from answer
        action_name = answer.answer["action"]
        action_method = None
        if action_name != "None":
            for action_type, name_method_dict in self.references.items():
                if action_name in name_method_dict.keys():
                    action_method = name_method_dict[action_name]
                    break
            if action_method is None:
                raise Exception("Action not found in context references")
        logger.debug(f"Agent selected: {action_name}")

        # Update self with response
        self.decision_in_progress[str(self.step[0])] = answer.answer["action"]
        self.answer = answer
        self.action_method = action_method
        self.action_type = "free_action" if action_name == "None" else action_type
        self.action_name = action_name
        self.step = (self.step[0] + 1, self.step[1])
        return

    def execute(self, gamestate: GameState, player: Player) -> None:
        """Manages interactions with all top-level action classes"""
        logger.debug("Executing ActionContext decision")        

        # Handle 'None' free_action
        if self.action_name == "None":
            return
        
        # All other actions       
        import inspect
        # Gather context if method exists
        args = {}
        for name, clsmthd in inspect.getmembers(self.action_method, inspect.isfunction):
            if name == "context":
                args = self.action_method.context(gamestate, player, self)
                break

        changes = self.action_method.resolve(gamestate, player, args)
        logger.info(changes)
        return

class SpawnedWorkerSkillContext(Context):
    """Used by a player to decide what worker to spawn
    
    Methods in this class are chained together in init"""
    from game.states import GameState, Player

    def __init__(
            self,
            gamestate: GameState, 
            player: Player,
            parent_decision: str,
            total_steps: int
        ) -> None:
        logger.debug('New SpawnedWorkerSkillContext')
        super().__init__(gamestate, player)
        self.decision_type = "spawn_worker_skill"
        self.step = (1,total_steps)
        self.parent_name = parent_decision
        self.selected_workers = []
        while self.step[0] < self.step[1]:
            self.compile_options(gamestate, player)
            self.call(gamestate, player)
        self.execute(gamestate, player)

    def compile_options(self, gamestate: GameState, player: Player) -> None:
        logger.debug("Compiling options for ActionContext")

        # Build skills references to limit options to one per industry
        from game.data.references import industries
        skills_dict = {}
        for skill in industries.keys():
            skills_dict[skill] = False

        # Find an example worker of eack skill
        options_dict = {}
        for worker in gamestate.worker_pool[player.faction]:
            if worker not in self.selected_workers and not skills_dict[worker.skill]:
                options_dict[worker.skill] = worker # Keep reference of the real worker object
                skills_dict[worker.skill] = True # So only one example of the skill is used

        # Update internal references to manage agent's answer
        self.references = options_dict

        # Final list of strings for agent call
        self.available_choices = {'worker_skill': list(self.references.keys())}
        return

    def call(self, gamestate: GameState, player: Player) -> None:

        logger.debug(f"[{self.step[0]}/{self.step[1]}] ActionContext making call to agent")
        call = ContextCall(
            self.masked_state, self.seq, self.game_id, self.parent_seq, 
            self.faction, self.agent_type, self.decision_in_progress, self.decision_type,
            self.step, self.parent_name, self.available_choices
        )
        answer = player.agent.call(call)

        # Build refs from answer
        worker_skill = answer.answer["worker_skill"]
        logger.debug(f"Agent selected: {worker_skill}")
        if worker_skill not in self.references.keys():
            raise Exception("Agent selected a worker but no reference object exists in WorkerSpawnContext")

        # Update self with response
        self.decision_in_progress[str(self.step[0])] = worker_skill # for next call to agent
        self.answer = answer # for saving data
        self.selected_workers.append(self.references[worker_skill])
        self.step = (self.step[0] + 1, self.step[1])

        return

    def execute(self, gamestate: GameState, player: Player) -> None:
        """Iteratively calls the spawn worker rules base on decision_in_progress"""
        logger.debug("Executing ActionContext decision")

        changes = []
        for _, skill in self.decision_in_progress:
            from game.rules import _WorkerSpawn
            changes.append(_WorkerSpawn.resolve(gamestate, player, skill))

        return