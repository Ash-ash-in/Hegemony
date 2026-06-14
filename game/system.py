from dataclasses import asdict, dataclass
import logging
from typing import Any
logger = logging.getLogger(__name__)
logger.debug("importing game_engine module")

@dataclass(frozen=True)
class Save:

    # Imports
    from datetime import datetime
    from game.data import factions
    import os

    # Point to and set up save directory
    directory = os.path.join(os.getcwd(), 'saves')
    os.makedirs(directory, exist_ok=True)

    ### Methods ###
    @staticmethod
    def save_game(gamestate, filename = None, overwrite = False):
        """
        Saves the json of a gamestate to a file
        # Args
        gamestate: GameState object to be saved
        filename: str - Name of the file to save the gamestate to
        overwrite: bool, whether to allow overwrite of existing file with same name 
        # Returns
        returns bool based on whether save was successful
        """
        logger.debug(f"save.save called with filename:{filename}, overwrite:{overwrite}")

        import json
        import os
        from datetime import datetime

        # Write a new file if not exists, write a new file if exists
        if filename == None:
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(Save.directory, filename)
        try:
            f = open(f"{filepath}.json", "w" if overwrite else "x")
        except FileExistsError:
            logger.error(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
            raise FileExistsError(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
        
        # Parse various state instances to dicts and write to file
        players_dict = {}
        for name,player_instance in gamestate.players.items():
            players_dict[name] = player_instance.to_dict()
        
        savedict = {
            "Game": {
                "player_count": gamestate.player_count,
                "round": gamestate.round,
                "turn": gamestate.turn,
                "active_player": gamestate.active_player
            },
            "Players": players_dict
        }
        f.write(json.dumps(savedict, indent=4))
        f.close()

        logger.info(f"Game saved to {filename}")
        return True


    @staticmethod
    def new_game(player_count, filename = None, overwrite = False):
        """
        Sets up a new game with the specified number of players and saves it to a file. Returns the gamestate object.
        
        :param player_count: int - Number of factions to set up
        :param filename: str - Name of the save file to create. Defaults to a timestamp.
        """
        logger.debug(f"save.new_game called with player_count: {player_count}")
        from game.data import common
        import json
        import game.data.factions as factions
        import os
        from datetime import datetime

        # Setup factions
        active_factions = common.faction_instantiate_order[:player_count]
        if player_count > 2: # Arrange factions in play order if middle class exists
            index_order = [0,2,1,3]
            active_factions = list(map(active_factions.__getitem__,index_order[:player_count]))
            logger.debug("Reordered factions due to player_count > 2")
        existing_factions = active_factions.copy()
        logger.info(f"active_factions: {active_factions}")

        # Append state if not controlled by a player
        if player_count < 4:
            existing_factions.append('State')
            logger.debug("State added to game due to player_count < 4")
        logger.info(f"existing_factions: {existing_factions}")

        # Initialise gamestate
        gamestate = common.GameState(
            player_count = player_count,
            players = {faction_name: factions.Player(faction_name) for faction_name in existing_factions}
        )
        logger.debug('Initial gamestate instantiated')

        success = Save.save_game(gamestate, filename=filename, overwrite=overwrite)
        if not success:
            logger.warning('File name already exists, no overwrite permission')
            raise Exception('File name already exists')

        logger.info(f"New game set up with player_count: {player_count}")
        return gamestate, filename

    @staticmethod
    def load_game(filename):
        """
        Loads a gamestate from a file and returns the gamestate object.
        
        :param filename: str - Name of the save file to load
        """
        logger.debug(f"game.load called with filename:{filename}")

        import json
        import game.data.factions as factions

        # Read the file
        from game.data.common import GameState
        with open(f"saves/{filename}.json", 'r') as f:
            try:
                gamestate_str = f.read()
            except FileNotFoundError:
                logger.error(f"File {filename}.json not found in saves folder.")
                raise FileNotFoundError()
            
            # Convert the string back to a GameState object
            save_dict = json.loads(gamestate_str)
            gamestate_dict = save_dict['Game']
            gamestate_dict['players'] = {k:factions.Player(**v) for k,v in save_dict['Players'].items()}
            gamestate = GameState(**gamestate_dict)
            f.close()

        logger.info(f"Game loaded from saves/{filename}.json")
        return gamestate

    @staticmethod
    def delete_save(filename):
        """
        Deletes a save file. Does not throw an exception if the file is not found.
        
        :param filename: str - Name of the save file to delete
        """
        logger.debug(f"save.delete called with filename:{filename}")

        import os

        filepath = os.path.join(Save.directory, f"{filename}.json")
        try:
            os.remove(filepath)
            logger.info(f"Save file {filename}.json deleted successfully.")
        except FileNotFoundError:
            logger.error(f"File {filename}.json not found in saves folder.")
        return

@dataclass
class Engine:
    from game.data.common import GameState
    from game.agents import Agent, AgentAnswer
    from game.data.factions import Player
    logger.debug("Calling engine class")
    agents = {}

    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances, according to those defined in the dictionary passed.
        This modifies the engine in place
        """
        logger.debug("Setting up agents")
        from game.agents import agent_refs
        from game.data.common import faction_play_order
        agent_references = {}
        for faction, agent_name in faction_agents.items():
            if faction not in faction_play_order:
                raise Exception(f"{faction} not recognised")
            if agent_name not in agent_refs.keys():
                raise Exception(f"{agent_name} not recognised")
            faction_instance = gamestate.players[faction]
            agent_references[faction] = agent_refs[agent_name](faction_instance)
        self.agents = agent_references
        return

    @staticmethod
    def startup(faction_agents: dict, player_count=None, filename=None, overwrite=False):
        """
        Process for launching a game.
        Handles validity checks and decides whether to load or start new game
        
        If player_count is None, a game is loaded
        If player_count exists, a new game is created
            New game uses filename if provided, else creates from timestamp
        If both player_count and filename are none, raise exception
        """
        ######################
        #### NOTE TO SELF ####
        ######################

        # New game should load a game for a default template
        # Setup should read a settings file

        ################################
    
        from game.system import Save
        logger.debug(f'startup called with player_count: {player_count}, filename: {filename}, overwrite:{overwrite}')

        # Validity Checks
        if filename == 'None':
            raise Exception('filename cannot be null')
        if filename:
            if type(filename) != str:
                raise Exception('filename must be a string')
        if player_count:
            if type(player_count) != int:
                raise Exception('player_count must be an integer')
        if len(faction_agents) != player_count:
            raise Exception('Number of agents passed does not match player_count')    

        # Load / Create savefile
        logging.debug(f"engine.startup called with player_count: {player_count if player_count else 'None'} and filename: {filename if filename else 'None'}")
        if player_count is None:
            if filename is None:
                raise Exception('Must provide either filename or player_count when calling setup')
            logging.info(f"Loading game from save file: {filename}")
            gamestate = Save.load_game(filename)
            player_count = gamestate.player_count
        else:
            gamestate, filename = Save.new_game(player_count, filename=filename, overwrite=overwrite)
            logging.info(f'Created new save file: {filename}')

        from game.data import common
        logger.debug("Setting up player references")
        player_references = common.PlayerReference(
            common.faction_instantiate_order[:player_count],
            common.faction_play_order,
            working_class=gamestate.players['Working Class'],
            middle_class=gamestate.players['Middle Class'] if player_count > 2 else None,
            capitalists = gamestate.players['Capitalists'],
            state=gamestate.players['State']
        )

        return gamestate, player_references


    @staticmethod
    def start_position(gamestate: GameState):
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a brand new game.
        """
        logger.debug('Called Engine.start_position')
        import game.rules as rules
        # TEMPORARY give everyone 120
        for name, inst in gamestate.players.items():
            if rules.MoneyTransfer.check(None, inst, 120, True).validity:
                rules.MoneyTransfer.resolve(None, inst, 120, True)
        return gamestate
    
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
        from game.agents import ContextCall, AgentAnswer, Agent
        from game.rules import CheckResponse
        logger.debug('Called Engine.action_phase')

        # Setup call process in one function for reusability
        def call_agent(agent: Agent, allowed_main: bool, allowed_free: bool, gamestate, player):
            """
            Builds a context call for an action, calls the agent, and returns the response
            """
            logger.debug("Engine.action_phase(call_agent()) called")

            # Build options and prepare to call agent
            all_options = DecisionContext.ActionContext.compile_options(player, allowed_free, allowed_main)
            call = ContextCall(
                gamestate,      # Instance
                player,         # Instance
                'Action',       # String
                all_options     # Dictionary - str: class
            )

            # Call the agent for a reponse
            answer = agent.call(call)
            logging.debug(f"Answer: {answer}")
            return answer

        ### Start the Action Phase ###

        for turn_num in range(1,6):
            logger.info(f'Starting action phase turn {turn_num}')
            gamestate.turn = turn_num # Update for save file
            for faction_name, player_instance in gamestate.players.items():
                if faction_name == 'State' and gamestate.player_count < 4:
                    continue
                logger.info(f"It's the {faction_name}'s turn")
                gamestate.active_player = faction_name # Update for save file

                # Call the agent
                agent = self.agents[player_instance.faction]
                answer = call_agent(agent, True, True, gamestate, player_instance)
                logger.debug(f"Agent answer: {answer}")

                # Enact the response
                if answer.order is None:
                    raise Exception('Order "None" response given before any action taken')
                args = [player_instance] + answer.args
                answer.order.resolve(*args)         

                # Check for a free action following a main
                if answer.primary_response == True:
                    answer = call_agent(agent, False, True, gamestate, player_instance)
                    if answer.order is None:
                        continue
                    args = [player_instance] + answer.args
                    answer.order.resolve(*args)      
        
                
                # Otherwise demand a main action response
                elif answer.primary_response == False:
                    answer = call_agent(agent, True, False, gamestate, player_instance)
                    if answer.order is None:
                        raise Exception('Main action required, None cannot be passed')
                    else:
                        args = [player_instance] + answer.args
                        answer.order.resolve(*args)      

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
        from game.data.common import phases

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


@dataclass(frozen=True)
class DecisionContext:
    """
    Contains the classes that connect the gamestate to the interfaces, for AI and Human agents
    Decides what the engine gives to an agent when they need to make a decsion
    AI and Humans receive the same information
    """
    logger.debug('Called DecisionContext')
    available: list
    unavailable: list[tuple]

    @dataclass(frozen=True)
    class ActionContext:
        """
        Checks what is available when making an action.
        Seperate methods for different types of agent.
        """
        logger.debug('Called ActionContext')
        from game.data.factions import Player
        from game.agents import AgentAnswer
        from game.data.common import GameState

        @staticmethod
        def compile_options(player: Player, allowed_free: bool, allowed_main: bool) -> dict:
            """
            Takes the list of attributes from the Action classes
            Looks for a 'check' method (which all actions should have)
            Runs the check and records the result

            The result is a dict - string: (classmethod, CheckResponse)
            """
            logger.debug("called DecisionContext.ActionContext.compile_options()")
            from game.rules import FreeAction, MainAction, CheckResponse

            context = {}

            # Compile free actions from rules
            if allowed_free:
                free_options = FreeAction.context(player)
                context = {**context, **free_options}
                logging.debug(f"Options from FreeAction.context(): {free_options}")

                if allowed_main: # Create a default option to pass regardless
                    context['None'] = (None,CheckResponse(False, "", "Free", []))
                else: # Create a way to not perform anything if necessary
                    context['None'] = (None,CheckResponse(True, "", "Free", []))

            # Compile main actions
            if allowed_main:
                main_options = MainAction.context(player)
                context = {**context, **main_options}
                logging.debug(f"Options from MainAction.context(): {main_options}")

            logger.debug(f'Compiled ActionContext options for {player.faction}')
            return context
        

