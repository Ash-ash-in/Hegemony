import logging
logger = logging.getLogger(__name__)

from game.context import ContextCall, AgentAnswer, GameState, Player

# Setup Decision Log
decision_log = []
d_chain = []

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

    
def dense_score(chain: list[DecisionLogEntry], 
                new_state: GameState, player: Player) -> None:
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

    # Add the chain to the decision log and clear
    global decision_log, d_chain
    decision_log += d_chain
    d_chain = []

    return