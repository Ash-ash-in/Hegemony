"""
# game/context.py

This file SHOULD contain everything to do with controlling the steps of a decision process. 
Including: 
- Creating snapshots of the game from a players perspective 
- Determining available options to a player
- Providing that information to an agent in a uniform format
- Passing parent_seq values around to maintain records of a chain
- Creating new seq values

## Hierarchy
Sits above:
- messages.py
Sit alongside (no interaction):
- agents.py
- rules.py
Sits below:
- engine.py
- HEGEMONY.py
"""
"""
OLD DESC
This module pertains to every part of making a call to an agent
- Masking the gamestate
- Building the file format (Context) to send
- Activating the agent's call function
- Updating the Context with the response
"""

# Imports and Logging
import logging
logger = logging.getLogger(__name__)

from typing import Any
import itertools
import inspect
from dataclasses import dataclass

from game.rules import FreeAction, MainAction, _WorkerSpawn
from game.assets.references import industries
from game.assets.messages import MaskedState, ContextCall
from game.states import GameState, Player


class BaseContext:
    """
    Parent Class for Context objects, it cannot be called directly.

    - Establishes the basic structure of a context
    - Stores the seq generator
    - Masks gamestate from the players perspective
    - Compiles options for the player (unique per Context class)
    """
    seq_gen = itertools.count()

    def __new__(cls, *args, **kwargs):
        """Prevents incorrect instantiation"""
        if cls is BaseContext:
            raise TypeError("BaseContext cannot be instantiated directly.")
    
    def __init__(
            self,
            gamestate: GameState, 
            player: Player,
            agent,
            step_max: int,
            parent: int | None = None,
            parent_name: str | None = None
        ):
        """Sets up the core components without masking or compiling options"""
        self.seq = next(self.seq_gen)
        self.game_id = gamestate.game_id
        self.parent_seq = parent if parent else self.seq
        self.faction = player.faction
        self.agent_type = agent.name
        self.decision_in_progress = {} # Used for multi-step decisions like assign workers
        self.decision_type = ""
        self.step = (
            0 if step_max == 0 else 1,
            step_max
        )
        self.parent_name = parent_name if parent_name else ""
        self.available_choices = {}
        self.references = {}

    def compile_options(self, gamestate, player) -> tuple[dict[str, list], dict]:
        raise Exception("Parent compile_options method called")

    def mask_state(self, gamestate, player) -> MaskedState:
        return MaskedState(gamestate, player)

    def build_call(self, gamestate, player) -> ContextCall:
        if self.decision_type == "":
            raise TypeError("decision_type not set, cannot build call")
        self.masked_state = self.mask_state(gamestate, player)
        self.options = self.compile_options(gamestate, player)

        call = ContextCall(
            self.masked_state, self.seq, self.game_id, self.parent_seq,
            self.faction, self.agent_type, self.decision_in_progress,
            self.decision_type, self.step, self.parent_name,
            self.options
        )
        return call

    def update_decision_in_progress(self, decision: dict) -> None:
        """Updates decision in progress for multi-step decisions"""
        self.decision_in_progress.update(decision)
        return

    def next_step(self) -> None:
        assert self.step[0] != self.step[-1]
        self.step = (self.step[0] + 1, self.step[-1])
        return


class ActionContext(BaseContext):
    def __init__(self, gamestate, player, agent) -> None:
        # Set up a context with 2 steps and no parent
        super().__init__(gamestate, player, agent, 2)
        self.decision_type = 'choose_action'

    def compile_options(self, gamestate: GameState, player: Player) -> tuple[dict[str, list], dict]:
        """
        Takes the list of attributes from the Action classes. 
        Looks for a 'check' method (which all actions should have). 
        Runs the check and records the result. 
        Classes with a valid check are appended to self.available_choices.
        """

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
        return self.available_choices, self.references




class __ActionContext(Context):
    """
    ActionContext is one of two primary decisions taken. 
    All other context windows cascade from here until a full move is made.
    
    Handles action decsisions
    - Contains context instance for action decision
    - Sets the action chain value (parent_seq)
    - Calls agent to choose
    - Initialises context for chosen action
    - Runs until turn is complete (recursive contexts inside 2 actions)
    """

    def __init__(self, gamestate: GameState, player: Player):
        logger.debug('New ActionContext')
        global d_chain
        from training.postprocessing import d_chain

        super().__init__(gamestate, player)
        self.decision_type = "choose_action"
        self.step = (1,2)
        self.parent_name = ""

        # Context Lifecycle
        while self.step[0] <= self.step[1]:
            if len(d_chain) != 0:
                logger.warning("Decision chain is not empty at start of ActionContext run")
            d_chain = []
            self.compile_options(gamestate, player)
            self._call(gamestate, player)
            self._execute(gamestate, player)
            self._reward(gamestate, player)
            
    def _compile_options(self, gamestate: GameState, player: Player) -> None:
        """
        Takes the list of attributes from the Action classes. 
        Looks for a 'check' method (which all actions should have). 
        Runs the check and records the result. 
        Classes with a valid check are appended to self.available_choices.
        """
        logger.debug("Compiling ActionContext options")

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
    
    def _call(self, gamestate: GameState, player: Player) -> None:
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
            if len(self.references) == 0:
                logger.warning("No references found in context window")
            for action_type, name_method_dict in self.references.items():
                if action_name in name_method_dict.keys():
                    action_method = name_method_dict[action_name]
                    break
            if action_method is None:
                raise Exception("Action not found in context references")

        # Update self with response
        self.decision_in_progress[str(self.step[0])] = answer.answer["action"]
        self.call = call
        self.answer = answer
        self.action_method = action_method
        self.action_type = "free_action" if action_name == "None" else action_type
        self.action_name = action_name
        self.step = (self.step[0] + 1, self.step[1])
        return

    def _execute(self, gamestate: GameState, player: Player) -> None:
        """Manages interactions with all top-level action classes"""
        logger.debug("Executing ActionContext decision")        

        # Handle 'None' free_action
        if self.action_name == "None":
            return
        
        # All other actions       
        # Gather context if method exists
        args = {}
        for name, clsmthd in inspect.getmembers(self.action_method, inspect.isfunction):
            if name == "context":
                args = self.action_method.context(gamestate, player, self)
                break

        changes = self.action_method.resolve(gamestate, player, args)
        logger.info(changes)
        return

    def _reward(self, gamestate: GameState, player: Player) -> None:
        """
        Unique for Action/ElectionContexts:
        - Defines the points for the whole action context decision chain
        - Appends the chain to the log
        - Clears the decision chain
        """
        logger.debug("Rewarding ActionContext decision")     
        global d_chain
        from training.postprocessing import dense_score, d_chain 

        dense_score(d_chain, gamestate, player)
        d_chain = []
        return
        
class SpawnedWorkerSkillContext(Context):
    """Used by a player to decide what worker to spawn"""

    def __init__(
            self,
            gamestate: GameState, 
            player: Player,
            parent_decision: str,
            parent_seq: int,
            total_steps: int
        ) -> None:
        logger.debug('New SpawnedWorkerSkillContext')
        super().__init__(gamestate, player)
        self.decision_type = "spawn_worker_skill"
        self.step = (1,total_steps)
        self.parent_name = parent_decision
        self.parent_seq = parent_seq
        self.selected_workers = []

        # Context Lifecycle
        while self.step[0] < self.step[1]:
            self._compile_options(gamestate, player)
            self._call(gamestate, player)
        self._execute(gamestate, player)

    def _compile_options(self, gamestate: GameState, player: Player) -> None:
        logger.debug("Compiling options for SpawnedWorkerSkillContext")

        # Build skills references to limit options to one per industry
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

    def _call(self, gamestate: GameState, player: Player) -> None:

        logger.debug(f"[{self.step[0]}/{self.step[1]}] SpawnedWorkerSkillContext making call to agent")
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

    def _execute(self, gamestate: GameState, player: Player) -> None:
        """Iteratively calls the spawn worker rules base on decision_in_progress"""
        logger.debug("Executing SpawnedWorkerSkillContext decision")

        changes = []
        for _, skill in self.decision_in_progress:
            changes.append(_WorkerSpawn.resolve(gamestate, player, skill))

        return
