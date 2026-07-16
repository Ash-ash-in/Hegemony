import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field

@dataclass
class Config:
    player_count: int
    agents: dict
    crisis_expansion: bool
    historic_expansion: bool


@dataclass
class Engine:
    from game.states import GameState

    def setup_gamestate(self, config: Config):
        logger.debug("Establishing gamestate in engine")
        from game.states import GameState

        # Validity Checks
        if config.player_count < 2 or config.player_count > 4:
            raise Exception('player count must be between 2 and 4')
        if config.player_count != len(config.agents.keys()):
            raise Exception("player_count and agents mismatch")
        
        # Setup Players
        logger.debug("Setting up players within gamestate setup")
        from game.states import WorkingClass, MiddleClass, Capitalists, PlayerState, NPCState
        players = {}
        players["Working Class"] = WorkingClass()
        if config.player_count == 2:
            players["Capitalists"] = Capitalists()
        else:
            players["Middle Class"] = MiddleClass()
            players['Capitalists'] = Capitalists()
        if config.player_count == 4:
            players["State"] = PlayerState()
        else:
            players["State"] = NPCState()
        

        # Setup GameState
        gamestate = GameState(
                players,
                config.player_count
            )

        return gamestate

    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances according to those defined in the dictionary passed.
        Agents can be found in the engine, or in the player objects
        This modifies the engine and players in-place
        """
        logger.debug("Setting up agents")
        from game.agents import agent_refs
        from game.data.references import faction_play_order
        agent_references = {}
        for faction, agent_name in faction_agents.items():
            if faction not in faction_play_order:
                raise Exception(f"{faction} not recognised")
            if agent_name not in agent_refs.keys():
                raise Exception(f"{agent_name} not recognised")
            faction_instance = gamestate.players[faction]
            agent_references[faction] = agent_refs[agent_name](faction_instance)
            faction_instance.agent = agent_references[faction]
        self.agents = agent_references
        return
    
    def engine_startup(self, config) -> GameState:
        """Runs all the engine setup functions"""
        logger.debug("Executing engine startup")
        gamestate = self.setup_gamestate(config)
        self.setup_agents(config.agents, gamestate)
        return gamestate


    @staticmethod
    def start_position(gamestate: GameState): 
