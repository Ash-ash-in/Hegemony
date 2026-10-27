"""
# assets/messages.py

This contains all the classes that are involved in moving data between modules. 
It aims to enforce strict data quality

## Hierarchy
Sits above:
- classes.py
- references.py
Sits below:
- rules.py
- context.py
- agents.py
- engine.py
- HEGEMONY.py
"""

# Imports and Logging
import logging
logger = logging.getLogger(__name__)

from typing import Any
from dataclasses import dataclass
from copy import deepcopy

from game.assets.references import industries
from game.states import GameState, Player

# ---------------------------------------------------
# Message Classes
@dataclass (init=False)
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

        gamestate = deepcopy(gamestate)
        player = deepcopy(player)
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
    gamestate: MaskedState
    seq: int
    game_id: str
    parent_seq: int
    faction: str
    agent_type: str
    decision_in_progress: list
    decision_type: str
    step: tuple
    parent_name: str
    available_choices: dict

@dataclass
class AgentAnswer:
    """
    # Agent Answer
    Contains:
    - the response for the agent
    - the value_estimate of the critic (none if not NN)
    - the log_prob of the critic (none if not NN)

    The "answer" should be a simple dict that can be understood by the requester that made the call. 
    Dictionary values must be strings, so that the NN can read them. 
    This means objects and methods can't be passed directly - those should be held in the context object and returned to the engine from there.

    Example: {"Worker": "WC1", "Slot": "Company3Slot2"}
    """
    answer: dict[str, str]
    value_estimate: float | None = None
    log_prob: float | None = None

@dataclass
class GameSummary:
    game_id: str
    winner: str
    scores: dict[str,int]
    total_decisions: int


class DecisionLogEntry:
    """Controls formatting for saving the outcome of decisions."""

    def __init__(self, call: ContextCall, response: AgentAnswer, 
                 reward = 0) -> None:
        from dataclasses import asdict
        
        # Context at Observation
        self.call = asdict(call)
        # Response at Observation
        self.response = asdict(response)
        # Agent Evaluation
        self.reward = reward # Rewards should only be handled in post-processing

    def assign_reward(self, value: int) -> None:
        self.reward = value