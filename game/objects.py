from dataclasses import dataclass

@dataclass(frozen = True)
class GameState:
    player_count: int
    turn: int
    round: int
    active_player: int
    players: list[PlayerState]
    victory_points: list[int]
    


@dataclass(frozen = True)
class PlayerState:
    faction: str
    victory_points: int

    # resources
    personal_food: int
    personal_luxuries: int
    personal_health: int
    personal_education: int
    personal_influence: int

    sale_food: int
    sale_luxuries: int
    sale_health: int   
    sale_education: int
    sale_influence: int

    food_storage: int
    luxuries_storage: int
    health_storage: int
    education_storage: int

    food_price: int
    luxuries_price: int
    health_price: int
    education_price: int

    # money
    money: int
    revenue: int
    capital: int
    income: int
    taxes: int
    expenses: int

    # population
    population: int
    prosperity: int
    worker_count: int
    unemployed: int

    # legitimacy
    workingclass_legitimacy: int
    middleclass_legitimacy: int
    capitalist_legitimacy: int


class Worker:
    def __init__(self, faction: Faction, skill: int):
        self.faction = faction
        self.skill = skill




