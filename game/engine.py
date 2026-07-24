import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from game.data.classes import Config

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
                config.player_count,
                config.game_id
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
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a brand new game.
        """
        logger.debug('Called Engine.start_position')
        import game.rules as rules

        # Build player refs
        for name, cls in gamestate.players.items():
            if name == "Working Class":
                working_class = cls
            elif name == "Middle Class":
                middle_class = cls
            elif name == "Capitalists":
                capitalists = cls
            elif name == "State":
                state = cls
            else:
                raise Exception("Unrecognised faction")

        ####################################
        ### TEMPORARY give everyone 120 ####
        for name, inst in gamestate.players.items():
            if rules.MoneyTransfer.check(None, inst, 120, True).validity:
                rules.MoneyTransfer.resolve(None, inst, 120, True)
        logger.debug('Temporary start position money complete')
        ### TEMPORARY give everyone 120 ####
        ####################################


    def preparation_phase(self, gamestate: GameState):
        """
        Runs the system - driven preparation actions.
        All actions are mandatory.
        """
        logger.debug('Called Engine.preparation_phase')
        return gamestate
    

    def action_phase(self, gamestate: GameState):
        """
        Handles the process for calling the DecisionContext and sending commands downstream
        
        WARNING: This modifies GameState's 'turn', 'active_player', and 'free_action_taken' in place. 
        WARNING: This replaces the GameState based on ~decisions taken~
        """
        from game.context import ActionContext
        from game.data.references import faction_play_order
        logger.debug('Called Engine.action_phase')

        ### Start the Action Phase ###

        for turn_num in range(1,6):
            logger.info(f'Starting action phase turn {turn_num}')
            gamestate.turn = turn_num
            for faction_name in faction_play_order:

                # Update gamestate's temporal data with who's turn it is
                if faction_name == 'State' and gamestate.player_count < 4:
                    continue
                if faction_name == "Middle Class" and gamestate.player_count < 3:
                    continue
                logger.info(f"It's the {faction_name}'s turn")
                gamestate.active_player = faction_name
                player = gamestate.players[faction_name]

                # Run the action
                context = ActionContext(gamestate, player)
                while context.step[0] < context.step[1]:
                    context.compile_options(gamestate, player)
                    answer = context.call(player.agent) # type: ignore
                    logger.info(f"Action selected: {answer.answer["action"]}")
                    result = context.execute(gamestate, player)
                    logger.info(result.state_changes)

        return gamestate

    @staticmethod
    def production_phase(gamestate: GameState):
        logger.debug('Called Engine.production_phase')
        return gamestate

    @staticmethod
    def elections_phase(gamestate: GameState):
        logger.debug('Called Engine.elections_phase')
        return gamestate

    @staticmethod
    def scoring_phase(gamestate: GameState):
        logger.debug('Called Engine.scoring_phase')
        return gamestate

    @staticmethod
    def endgame_scoring(gamestate: GameState):
        logger.debug('Called Engine.endgame_scoring')
        return gamestate

    def flow(self, gamestate: GameState):
        """
        Main Execution of game. Runs constantly during play.

        WARNING: This modifies GameState's 'round' and 'phase' in place.
        """
        logger.debug('Called Engine.flow')
        from game.data.references import phases

        for round in range(0,6):
            logger.info(f'Starting Round {round}')
            gamestate.round = round

            if round == 0:
                self.start_position(gamestate)
                continue

            for phase in phases:

                if phase == phases[0] and round == 1:
                    continue # First round gets no preparation phase
                
                logger.info(f'Begining phase: {phase}')

                if phase == phases[0]:
                    gamestate = self.preparation_phase(gamestate)
                elif phase == phases[1]:
                    gamestate = self.action_phase(gamestate)
                elif phase == phases[2]:
                    gamestate = self.production_phase(gamestate)
                elif phase == phases[3]:
                    gamestate = self.elections_phase(gamestate)
                elif phase == phases[4]:
                    gamestate = self.scoring_phase(gamestate)

        gamestate = self.endgame_scoring(gamestate)
