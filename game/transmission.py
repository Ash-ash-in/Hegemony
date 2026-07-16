import logging
logger = logging.getLogger(__name__)
logger.debug("Importing agents.test_agents module")

from dataclasses import dataclass
from game.states import GameState

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

    return {}


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

    # Game Engine Data
    round: int
    phase: str
    turn: int
    player_turn: str

    # Board Data
    board: dict
    """
    Format:
    {
        "companies: {
            "capitalist: {
                "company_2": {
                    "workers": ["w1","w5"],
                    "wages": 2,
                    "automation: False,
                    "committed": True
                },
                "company_7": {
                    "workers": ["w2","w9","w11"],
                    "wages": 3,
                    "automation: True,
                    "committed": False
                }
            },
            "state": {
                "company_20": {
                    "workers": [None, None],
                    "wages": 1,
                    "automation: False,
                    "committed": False
                }
            }
        },
        "unions": {
            "luxury": w23,
            "agriculture: None
        },
        "laws": {
            "labour": 1,
            "taxation": 3
        },
        "unemployed_workers": [
            "w67", "w3"
        ]

    }
    """

    players: dict # public knowledge about the players
    """
    Format:
    {
        "working_class": {
            "points": 8,
            "money": 100,
            "resources: {
                "food": 2,
                "healthcare": 5,
                "influence: 1
            },
            "prosperity": 5,
            "worker_count": 12,
            "population": 3
        }
        "capitalists": {
            "points": 10
            "revenue": 30,
            "capital": 100,
            "resources: {
                "food": 2,
                "healthcare": 5,
                "influence: 1
            },
            "storage: {
                "food": 12,
                "healthcare": 10
            },
        }
    }

    """

    # This Decision
    decision_type: str # The kind of call being made eg main_action, free_action, worker_placement, company_selling
    step: tuple # For decisions with multiple stages, this is how the agent knows how far along the process it is.
        # For multistage, use (2,3) for the second of three calls. 
        # For indefinite calls, use (2, 0) for the second of an unknown number of calls
        # For single stage, use (0)

    # Parent Decision
    parent_name: str # The name of primary reason for this call
        # "" for primary decisions
    action_in_progress: dict # For helping the agent keep a cohesive view
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
    game_id: str # set when the game is set up, and remains consistent throughout
    seq: int # The unique ID for this call
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
