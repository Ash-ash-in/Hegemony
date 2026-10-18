import logging
logger = logging.getLogger(__name__)

from game.states import GameState, Player
from game.assets.messages import DecisionLogEntry

    
def score_decision(chain: list[DecisionLogEntry], 
                new_state: GameState, player: Player) -> list[DecisionLogEntry]:
    """Calculates reward for a decision chain, and appends it to the log"""

    # Read in key variables to compare
    pre_state = chain[0].call["gamestate"]

    faction = player.faction
    pre_money = pre_state["PlayerData"][faction]["money"]
    pre_points = pre_state["PlayerData"][faction]["victory_points"]
    pre_loans = pre_state["PlayerData"][faction]["loans"]
    pre_resources = pre_state["PlayerData"][faction]["resources"]
    pre_influence = pre_state["PlayerData"][faction]["influence"]

    post_money = player.money
    post_points = player.victory_points
    post_loans = player.loans
    post_resources = player.resources
    post_influence = player.influence

    # Award points - (Modify these to steer critic's target)
    # Still to add: faction-specific rewards

    reward = sum([
        (post_money - pre_money) / 50,
        post_points - pre_points,
        (pre_loans - post_loans) * 1.2,
        post_influence - pre_influence * 0.5
    ])
    for r, val in post_resources.items():
        reward += (val - pre_resources[r]) * 0.3

    # Modify the last record in the chain to assign reward
    chain[-1].assign_reward(reward)

    return chain

def save_decision_log(decision_chain):
    # Save to Log
    import os
    import orjson

    path = os.path.join("training", "data", "decisions.jsonl")
    with open(path, "ab") as f:   # append in binary mode
        for d in decision_chain:
            f.write(orjson.dumps(d.__dict__))
            f.write(b"\n")