from dataclasses import asdict, dataclass
import logging
logger = logging.getLogger(__name__)
logger.debug("importing game_engine module")

@dataclass(frozen=True)
class Save:

    # Imports
    from datetime import datetime
    import game.data.factions as factions
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
            return False
        
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
            return False, False

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
                return
            
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


@dataclass(frozen=True)
class Engine:
    from game.data.common import GameState
    from game.agents import Agent, AgentAnswer
    from game.data.factions import Player
    agent_refs: dict

    @staticmethod
    def startup(player_count=None, filename=None, overwrite=False):
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
        # Maybe I just move the PlayerReference into new_game and load_game, and call them directly?
        # Or better yet, startup takes no arguements and requires it of the player?
        # Maybe I just pass one "args_dict" into this function, and if it's none, I request it all from the player.
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
        player_references = common.PlayerReference(
            common.faction_instantiate_order[:player_count],
            common.faction_play_order,
            working_class=gamestate.players['Working Class'],
            middle_class=gamestate.players['Middle Class'] if player_count > 2 else None,
            capitalists = gamestate.players['Capitalists'],
            state=gamestate.players['State']
        )

        return gamestate, player_references
    

    def call_agent(self, role:str, gamestate: GameState, player: Player) -> AgentAnswer:
        """
        Builds a context call, sends it to the agent, and receives an answer
        """
        from game.agents import ContextCall
        target = self.agent_refs[player.faction]
        options = DecisionContext.ActionContext.compile_options(player)
        call = ContextCall(gamestate, player, role, options)
        logger.debug(f'ContextCall sent to {target.name}')
        return target.call(call)

    @staticmethod
    def start_position(gamestate: GameState):
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a band new game.
        """
        logger.debug('Called Engine.start_position')
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
        
        WARNING: This modifies GameState's 'turn' and 'active_player' in place.
        WARNING: This replaces the GameState based on ~decisions taken~
        """
        from game.agents import ContextCall
        logger.debug('Called Engine.action_phase')

        for turn_num in range(1,6):
            logger.debug(f'Starting action phase turn {turn_num}')
            for faction_name, player_instance in gamestate.players.items():
                logger.debug(f"It's the {faction_name}'s turn")

                all_options = DecisionContext.ActionContext.compile_options(player_instance)
                call = ContextCall(
                    gamestate,
                    player_instance,
                    'Action',
                    all_options
                )

                # Call the agent for a reponse
                answer = self.agent_refs[player_instance.faction].call(call)
                print(f"Answer: {answer}")
        return gamestate
    
                ### Interaction Layer ###
                # This section needs to connect to the interfaces of each player.
                # It needs to check what agent is in control
                # Call their layer
                # And pass the relevent information to it

                ## Development
                ##  - Player
                #       Start with a text input
                #       Display the key metrics for that player only
                #       Display options
                #       Take the input and enact that choice
                #
                ##  - AI
                #       Pass container with options
                #       Receive instruction back
                #
                ## Live
                ##  - Player
                #       Display everything in UI
                #       There will be an action screen that always passes relevent information
                #       Elections etc will need their own screen
                #       Pass options for display, and impossible ones for explanations why
                #       Return user input and enact
                #
                #   - AI
                #       Who knows

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

        for round in range(0,5):
            logger.info(f'Starting Round {round}')

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

        @staticmethod
        def compile_options(player: Player) -> dict:
            """
            Takes the list of attributes from the Action classes
            Looks for a 'check' method (which all actions should have)
            Runs the check and records the result

            The result is a dict - 
            """
            from game.rules import FreeAction
            options = FreeAction.context()
            context = {}
            print(options)
            for o in options:
                print(o)
                instance = o()
                if hasattr(instance, 'check'):
                    context[o] = instance.check(player)
            logger.debug(f'Compiled ActionContext options for {player.faction}')
            return context
        

