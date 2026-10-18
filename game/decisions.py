"""
# game/actions.py

This is the orchestration file for handling decision chains.

## Notes
I still need to decide whether this is going to contain yield or return functions

    
## Hierarchy
#### Sits above:
- agents.py
- context.py
- rules.py
- messages.py
#### Sits below:
- engine.py
- HEGEMONY.py
"""
# Imports and Logging
import logging
logger = logging.getLogger(__name__)

from copy import deepcopy
import inspect
from abc import ABC, abstractmethod
from typing import ClassVar # Create attributes that can't be overwritten

import game.context as ctx
import game.agents as ag
import game.assets.messages as msg
from game.states import GameState, Player
import training.postprocessing as pp

class Decision(ABC):
    registry: ClassVar[dict[str, type["Decision"]]] = {}
    key: ClassVar[str | None] = None   # abstract intermediates (e.g. MultiStepDecision) leave this None

    @classmethod
    def __init__(cls, gamestate: GameState, player: Player, agent: ag.Agent) -> None:
        faction = player.faction
        cls.acting_faction = faction
        cls.original_gamestate = deepcopy(gamestate)
        cls.original_player = cls.original_gamestate.players[faction]
        cls.agent = agent

    def __init_subclass__(cls, **kwargs) -> None:
        # Prevent duplicate keys being created by subclasses
        super().__init_subclass__(**kwargs)
        if cls.key is None:
            return
        if cls.key in Decision.registry:
            raise TypeError(
                f"Decision key {cls.key!r} already registered by "
                f"{Decision.registry[cls.key].__name__}; {cls.__name__} can't reuse it"
            )
        Decision.registry[cls.key] = cls

    @classmethod
    def create(cls, key: str, gamestate, player, agent) -> "Decision":
        try:
            decision_cls = cls.registry[key]
        except KeyError:
            raise KeyError(
                f"No Decision registered for {key!r}. Known: {sorted(cls.registry)}"
            ) from None
        return decision_cls(gamestate, player, agent)

    @classmethod
    def _build_call(cls, context: ctx.BaseContext) -> msg.ContextCall:
        return context.build_call(cls.current_gamestate, cls.current_player)

    @classmethod
    def _call_agent(cls, agent: ag.Agent, ctx_call: msg.ContextCall) -> msg.AgentAnswer:
        return agent.call(ctx_call)

    @abstractmethod
    def _execute(self, 
            gamestate: GameState, 
            player: Player, 
            agent: ag.Agent, 
            d_chain: list, 
            answer: msg.AgentAnswer
            ) -> tuple[GameState, list]:
        pass

    @abstractmethod
    def run(self, gamestate: GameState, player: Player, agent: ag.Agent, d_chain: list) -> tuple[GameState, list]:
        pass

class ActionDecision(Decision):
    """
    ActionDecision is one of two primary decisions taken. 
    All other decisions cascade from here until a full move is made.
    
    Handles action decisions:
    - Creates the context for the given player
    - Stores the seq from that context as the parent_seq, which is passed to all other contexts in the chain.
    - Saves that context as part [1/3] of the decision log
    - Calls agent to decide which option to pick
    - Saves that answer [2/3] for the decision log
    - Begins next decision process as requred
    - Runs recursion until no more decisions are required to execute
    - Receives all decision log entries generated from that recursion and appends them to chain
    - Saves the new context [3/3] for comparison
    - Calls post-processing to evaluate, backfill, and log decision chain
    - UNDECIDED: Repeat process again for FreeAction? OR handle that in engine?
    """
    key = "choose_action"

    def __init__(self, gamestate: GameState, player: Player, agent: ag.Agent) -> None:
        super().__init__(gamestate, player, agent)
        return

    def _get_context(self, gamestate: GameState, player: Player, agent: ag.Agent) -> ctx.BaseContext:
        context = ctx.ActionContext(gamestate, player, agent)
        return context

    def _execute(self, 
            gamestate: GameState, 
            player: Player, 
            agent: ag.Agent, 
            d_chain: list, 
            answer: msg.AgentAnswer
            ) -> tuple[GameState, list]:
        # -------
        # logic for free/main action
        # launch new Decision based on answer
        # Pass parent info down
        # Get episode info back
        # -------

        # Handle 'None' free_action
        if answer.answer.get("free_action") == "None":
            return gamestate, d_chain

        # Start Trigger Recusrion
        next_decision = Decision.create(answer.answer["action"], gamestate, player, agent)
        gamestate, d_chain = next_decision.run(gamestate, player, agent, d_chain)

        return gamestate, d_chain
    
    def run(self, gamestate: GameState, player: Player, agent: ag.Agent, d_chain: list) -> tuple[GameState, list]:

        # Start Episode (Holds each part of the decision for this link in the chain)
        episode = []

        # Build Context
        context = self._get_context(gamestate, player, agent)
        self.original_context = context
        episode.append(context)
        call = self._build_call(context)

        # Call Agent
        agent_response = self._call_agent(self.agent, call)

        # Reset state to origin and re-run 
        if len({"RESET", "UNDO"}.intersection(set(agent_response.answer.values()))) > 0:
            d_chain = []
            gamestate = self.original_gamestate
            player = self.original_player
            return self.run(gamestate, player, agent, d_chain)

        # Add first step in the decision chain
        episode.append(agent_response)
        d_chain.append(msg.DecisionLogEntry(*episode))

        # Execute
        gamestate, d_chain_additions = self._execute(gamestate, player, agent, d_chain, agent_response)
        d_chain += d_chain_additions

        # Score & Save Decsion Chain (TOP LEVEL ONLY)
        d_chain = pp.score_decision(d_chain, gamestate, player)
        pp.save_decision_log(d_chain)

        return gamestate, d_chain


class MultiStepDecision(Decision):
    def __init__(self) -> None:
        return