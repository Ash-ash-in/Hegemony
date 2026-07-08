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

    def setup_gamestate(self, config: Config):

        # Validity Checks
        if config.player_count != len(config.agents.keys()):
            raise Exception("player_count and agents mismatch")
        
        # Imitialise Players
        



    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances, according to those defined in the dictionary passed.
        Agents can be found in the engine, or in the player objects
        This modifies the engine and players in place
        """
        logger.debug("Setting up agents")
        from game.old_agents import agent_refs
        from game.data.classes import faction_play_order
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