from dataclasses import asdict, dataclass
import logging
logger = logging.getLogger(__name__)
logger.debug("importing game_engine module")

@dataclass
class save:

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
        filepath = os.path.join(save.directory, filename)
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

        success = save.save_game(gamestate, filename=filename, overwrite=overwrite)
        if not success:
            logger.warning('File name already exists, no overwrite permission')
            return False, False

        # # Write a new file
        # filepath = os.path.join(save.directory, filename)
        # try:
        #     f = open(f"{filepath}.json", "w" if overwrite else "x")
        # except FileExistsError:
        #     logger.error(f"File {filename}.json already exists.")
        #     raise FileExistsError(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
        
        # # Parse various state instances to dicts and write to file
        # savedict = {
        #     "Game": asdict(gamestate),
        #     "Players": {name:instance.to_dict() for name, instance in gamestate.players.items()}
        # }
        # f.write(json.dumps(savedict, indent=4))
        # f.close()

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

        filepath = os.path.join(save.directory, f"{filename}.json")
        try:
            os.remove(filepath)
            logger.info(f"Save file {filename}.json deleted successfully.")
        except FileNotFoundError:
            logger.error(f"File {filename}.json not found in saves folder.")
        return



def startup(player_count=None, filename=None, overwrite=False):
    """
    Process for launching a game.
    Handles validity checks and decides whether to load or start new game
    
    If player_count is None, a game is loaded
    If player_count exists, a new game is created
        New game uses filename if provided, else creates from timestamp
    If both player_count and filename are none, raise exception
    """
    from game.engine.game_engine import save
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
        gamestate = save.load_game(filename)
        player_count = gamestate.player_count
    else:
        gamestate, filename = save.new_game(player_count, filename=filename, overwrite=overwrite)
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



class DecisionContext:
    """
    Decides what the engine gives to an agent when they need to make a decsion
    AI and Humans receive the same information
    """
    def __init__(self, available: list, unavailable: list[tuple]):
        self.available_actions = available # List of actions, which should correspond to a function to call
        self.unavailable_actions = unavailable # List of (action, reason)

    
