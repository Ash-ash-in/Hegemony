"""
This module pertains to every part of making a call to an agent
"""
import logging
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass
from game.states import GameState, Player


class Context:
    """
    Parent Class for all Context types.
    Child classes must compose all data for a ContextCall
    
    Ingests the least amount of variables, so that they can be parsed downstream
    """
    import itertools
    seq_gen = itertools.count()
    def __init__(
            self,
            gamestate: GameState, 
            player: Player
        ):
        # Update State
        self.masked_state = mask_gamestate_normal(gamestate, player)
        # Context Metadata
        self.seq = next(self.seq_gen)
        self.game_id = gamestate.game_id
        self.parent_seq = self.seq
        self.faction = player.faction
        self.agent_type = player.agent.name # type: ignore
        self.action_in_progress = {}
        self.decision_type = ""
        self.step = ()
        self.parent_name = ""
        self.available_actions = {}


class ActionContext(Context):
    """
    Checks what is available when making an action.
    Seperate methods for different types of agent.
    """
    from game.agents import Agent
    from game.states import GameState, Player

    def __init__(
            self,
            gamestate: GameState, 
            player: Player
        ):
        super().__init__(gamestate, player)
        logger.debug('New ActionContext')
        self.decision_type = "Action"
        self.step = (1,2)
        self.parent_name = "Action Phase"
        self.available_actions = self.compile_options(player, True, True)

    @staticmethod
    def compile_options(player: Player, allowed_free: bool, allowed_main: bool) -> dict:
        """
        Takes the list of attributes from the Action classes
        Looks for a 'check' method (which all actions should have)
        Runs the check and records the result

        The result is a dict - string: (classmethod, CheckResponse)
        """
        logger.debug("Compiling ActionContext options")
        from game.rules import FreeAction, MainAction, CheckResponse

        context = {}

        # Compile free actions from rules
        if allowed_free:
            free_options = FreeAction.context(player)
            context = {**context, **free_options}
            logging.debug(f"Options from FreeAction.context(): {free_options}")

            if allowed_main: # Create a default option to pass regardless
                context['None'] = (None,CheckResponse(False, ""))
            else: # Create a way to not perform anything if necessary
                context['None'] = (None,CheckResponse(True, ""))

        # Compile main actions
        if allowed_main:
            main_options = MainAction.context(player)
            context = {**context, **main_options}
            logging.debug(f"Options from MainAction.context(): {main_options}")

        logger.debug(f'Compiled ActionContext options for {player.faction}')
        return context
    

@dataclass
class ContextCall:
    """
    # ContextCall
    This class contains the infomation that is sent to an agent.

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
    masked_gamestate: dict

    # This Decision
    decision_type: str # The kind of call being made eg action, worker_placement, company_selling
    step: tuple # For decisions with multiple stages, this is how the agent knows how far along the process it is.
        # For multistage, use (2,3) for the second of three calls. 
        # For indefinite calls, use (2, 0) for the second of an unknown number of calls
        # For single stage, use (1, 1)

    # Parent Decision
    parent_name: str # The name of primary reason for this call
    action_in_progress: dict # For helping the agent keep a cohesive view
        # {} for primary decisions
        # Include free/main actions for choosing a primary, but not for their subordinate decisions
    """
    Format:
     {
        "action": "assign_workers",
        "placements_so_far": [
            {"worker": "w3", "slot": "company_1_slot_3"}
        ],
        "placements_remaining": 2
    }
    """

    # Available Actions
    available_actions: dict[str, dict[str, list]]
    """
    Format:

    {"available_actions": {
        "workers": ["w1", "w2"],
        "slots": ["company_1_slot_1"]
        }
    }
    """
    
    # Logging - For data collection
    seq: int # unique ID for this call
    game_id: str # set when the game is set up, and remains consistent throughout
    parent_seq: int # The parent ID for this call if it's a sub. Same as Seq if this is a main
    faction: str # The faction making this decision
    agent_type: str # The kind of agent that made this decision eg Automa

@dataclass
class AgentAnswer:
    """
    # Agent Answer
    Simply contains the response for the agent

    This should be a simple dict that can be understood by the requester that made the call. 
    Example: {Worker: "WC1", Slot: "Company3Slot2"}
    """
    answer: dict[str,dict[str,str]]

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


def mask_gamestate_normal(gamestate: GameState, player) -> dict:
    """
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


# Internal Engine Checks

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