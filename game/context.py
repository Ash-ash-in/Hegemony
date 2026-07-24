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
from typing import Any
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass
from game.states import GameState, Player

@dataclass
class BasicMaskedState:
    """
    This is the masking process for all agents except the NN.
    No concerns are taken over multicollinerarity.
    Ease of representation is prioritised.
    Raw values are submitted, nothing is normalised.
    """
    class _GameMetaData:
        def __init__(self, gamestate: GameState) -> None:
            self.player_count = gamestate.player_count,
            self.round = gamestate.round,
            self.phase = gamestate.phase,
            self.turn = gamestate.turn,
            self.player_turn = gamestate.active_player

    class _BoardData:
        def __init__(self, gamestate: GameState) -> None:
            self.worker_pool = gamestate.worker_pool,
            self.storages = gamestate.storages,
            self.election_cubes = gamestate.election_cubes,
            self.unemployed_workers = gamestate.unemployed_workers,
            self.companies = gamestate.companies, # figure this out, may need to unpack
            self.unions = gamestate.unions, # unpack too?
            self.laws = gamestate.laws,
            self.tariff_level = gamestate.tariff_level,
            self.voting_area = gamestate.voting_area,
            self.demonstration = gamestate.demonstration,
            self.business_deals = gamestate.active_business_deals,
            self.export_card = gamestate.active_export_card

    class _PlayerData:
        def __init__(self, gamestate: GameState, player: Player) -> None:
            self.faction = player.faction,
            self.victory_points = player.victory_points,
            self.money = player.money,
            self.loans = player.loans,
            self.resources = player.resources,
            self.influence = player.influence,
            self.market = player.market
            if player.faction in ("Working Class", "Middle Class"):
                self.population_track = player.population_track, # pyright: ignore[reportAttributeAccessIssue]
                self.population = player.population, # pyright: ignore[reportAttributeAccessIssue]
                self.prosperity = player.prosperity # pyright: ignore[reportAttributeAccessIssue]
            if player.faction == "Working Class":
                self.strike_tokens = player.strike_tokens # pyright: ignore[reportAttributeAccessIssue]
            else:
                self.storage = player.storage # pyright: ignore[reportAttributeAccessIssue]
            if player.faction == "Middle Class":
                self.prosperity_track = player.prosperity_track # pyright: ignore[reportAttributeAccessIssue]
            if player.faction in ("Middle Class", "Capitalists"):
                self.storages = player.storages # pyright: ignore[reportAttributeAccessIssue]
            if player.faction == "Capitalists":
                self.revenue = player.revenue # pyright: ignore[reportAttributeAccessIssue]
                self.capital = player.capital # pyright: ignore[reportAttributeAccessIssue]
                self.free_trade_zone = player.free_trade_zone # pyright: ignore[reportAttributeAccessIssue]
                self.machinery_tokens = player.machinery_tokens # pyright: ignore[reportAttributeAccessIssue]
            elif player.faction == "State" and gamestate.player_count == 4:
                self.legitimacy = player.legitimacy # pyright: ignore[reportAttributeAccessIssue]
                self.legitimacy_tokens = player.legitimacy_tokens # pyright: ignore[reportAttributeAccessIssue]
    
    class _OwnPlayerData(_PlayerData):
        def __init__(self, gamestate: GameState, player: Player) -> None:
            super().__init__(gamestate, player)
            self.hand = player.hand

    class _OtherPlayerData:
        def __init__(self, gamestate: GameState, player: Player) -> None:
            for other_player in gamestate.players.values():
                if other_player.faction == player.faction:
                    continue
                elif other_player.faction == "Working Class":
                    self.working_class = BasicMaskedState._PlayerData(gamestate, other_player)
                elif other_player.faction == "Middle Class":
                    self.middle_class = BasicMaskedState._PlayerData(gamestate, other_player)
                elif other_player.faction == "Capitalists":
                    self.capitalists = BasicMaskedState._PlayerData(gamestate, other_player)
                elif other_player.faction == "State":
                    self.state = BasicMaskedState._PlayerData(gamestate, other_player)

    def __init__(self, gamestate: GameState, player: Player) -> None:
        self.GameMetaData = BasicMaskedState._GameMetaData(gamestate)
        self.BoardData = BasicMaskedState._BoardData(gamestate)
        self.OwnPlayerData = BasicMaskedState._OwnPlayerData(gamestate, player)
        self.OtherPlayerData = BasicMaskedState._OtherPlayerData(gamestate, player)
        
def mask_gamestate_basic(gamestate: GameState, player) -> dict:
    """
    # OBSOLETE FUNCTION
    This is the masking process for all agents except the NN.
    No concerns are taken over multicollinerarity.
    Ease of representation is prioritised.
    Raw values are submitted, nothing is normalised.
    """
    game_metadata = {
        "player_count": gamestate.player_count,
        "round": gamestate.round,
        "phase": gamestate.phase,
        "turn": gamestate.turn,
        "player_turn": gamestate.active_player
    }

    board_data = {
        "worker_pool": gamestate.worker_pool,
        "storages": gamestate.storages,
        "election_cubes": gamestate.election_cubes,
        "unemployed_workers": gamestate.unemployed_workers,
        "companies": gamestate.companies, # figure this out
        "unions": gamestate.unions,
        "laws": gamestate.laws,
        "tariff_level": gamestate.tariff_level,
        "voting_area:": gamestate.voting_area,
        "demonstration": gamestate.demonstration,
        "business_deals": gamestate.active_business_deals,
        "export_card": gamestate.active_export_card
    }

    def compile_player_data(gamestate, player) -> dict:
        player_data = {
            "faction": player.faction,
            "victory_points": player.victory_points,
            "money": player.money,
            "loans": player.loans,
            "resources": player.resources,
            "influence": player.influence,
            "market": player.market
        }
        if player.faction in ("Working Class", "Middle Class"):
            player_data["population track"] = player.population_track,
            player_data["population"] = player.population,
            player_data["prosperity"] = player.prosperity
        if player.faction == "Working Class":
            player_data["strike_tokens"] = player.strike_tokens
        else:
            player_data["storage"] = player.storage
        if player.faction == "Middle Class":
            player_data["prosperity_track"] = player.prosperity_track
        if player.faction in ("Middle Class", "Capitalists"):
            player_data["storages"] = player.storages
        if player.faction == "Capitalists":
            player_data["revenue"] = player.revenue
            player_data["capital"] = player.capital
            player_data["free_trade_zone"] = player.free_trade_zone
            player_data["machinery_tokens"] = player.machinery_tokens
        elif player.faction == "State" and gamestate.player_count == 4:
            player_data["legitimacy"] = player.legitimacy
            player_data["legitimacy_tokens"] = player.legitimacy_tokens
        return player_data
    own_player_data = compile_player_data(gamestate, player)
    own_player_data["hand"] = player.hand

    other_player_data = {}
    for other_player in gamestate.players:
        if other_player.faction == player.faction:
            continue
        else:
            other_player_data[other_player.faction] = compile_player_data(gamestate, other_player)

    return {
        "game_metadata": game_metadata,
        "board_data": board_data,
        "own_player_data": own_player_data,
        "other_player_data": other_player_data
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
    masked_gamestate: BasicMaskedState
    seq: int
    game_id: str
    parent_seq: int
    faction: str
    agent_type: str
    action_in_progress: dict
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

@ dataclass
class DecsionLogEntry:

    # Context at Observation
    call: ContextCall

    # Response at Observation
    response: AgentAnswer

    # Agent Evaluation
    reward: None = None
    game_outcome: None = None

@dataclass
class GameSummary:

    game_id: str
    winner: str
    scores: dict[str,int]
    total_decisions: int


