from dataclasses import dataclass

class DecisionContext:
    """
    Decides what the engine gives to an agent when they need to make a decsion
    AI and Humans receive the same information
    """
    def __init__(self, available: list, unavailable: list[tuple]):
        self.available_actions = available # List of actions, which should correspond to a function to call
        self.unavailable_actions = unavailable # List of (action, reason)

    
