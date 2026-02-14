import logging
logger = logging.getLogger(__name__)
logger.debug("importing save_control module")

from pathlib import Path
from datetime import datetime
import json
from dataclasses import asdict

import game.data.states as states

# Point to the saves folder
directory = Path('saves')
# Create directory if it doesn't exist
directory.mkdir(parents=True, exist_ok=True)


def save_game(gamestate, filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), overwrite = False):
    """
    Saves the json of a gamestate to a file
    
    :param gamestate: GameState object to be saved
    :param filename: str - Name of the file to save the gamestate to. 
    """
    logger.debug(f"Saving game to saves/{filename}.json")

    # Write a new file if not exists, write a new file if exists
    filepath = directory / filename
    try:
        f = open(f"{filepath}.json", "w" if overwrite else "x")
    except FileExistsError:
        logger.error(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
        return
    
    # Parse various state instances to dicts and write to file
    save = {
        "Game": asdict(gamestate),
        "Players": {k: asdict(v) for k, v in gamestate.players.items()}
    }
    f.write(json.dumps(save, indent=4))
    f.close()

    logger.info(f"Game saved to {filename}")
    return



def new_game(player_count, filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), overwrite = False):
    """
    Sets up a new game with the specified number of players and saves it to a file. Returns the gamestate object.
    
    :param player_count: int - Number of factions to set up
    :param filename: str - Name of the save file to create. Defaults to a timestamp.
    """
    logger.debug(f"Setting up new game with {player_count} players")
    from game.data.common import faction_list

    active_factions = faction_list[:player_count]
    logger.info(f"Active factions: {active_factions}")
    gamestate = states.GameState(
        player_count = player_count,
        players = {faction_name: states.PlayerState(faction=faction_name) for faction_name in active_factions}
    )

    # Write a new file
    filepath = directory / filename
    try:
        f = open(f"{filepath}.json", "w" if overwrite else "x")
    except FileExistsError:
        logger.error(f"File {filename}.json already exists.")
        return
    
    # Parse various state instances to dicts and write to file
    save = {
        "Game": asdict(gamestate),
        "Players": {k: asdict(v) for k, v in gamestate.players.items()}
    }
    f.write(json.dumps(save, indent=4))
    f.close()

    logger.info(f"New game set up with player count: {player_count}")
    return gamestate


def load_game(filename):
    """
    Loads a gamestate from a file and returns the gamestate object.
    
    :param filename: str - Name of the save file to load
    """
    logger.debug(f"Loading game from saves/{filename}.json")

    # Read the file
    from game.data.states import GameState
    with open(f"saves/{filename}.json", 'r') as f:
        try:
            gamestate_str = f.read()
        except FileNotFoundError:
            logger.error(f"File {filename}.json not found in saves folder.")
            return
        
        # Convert the string back to a GameState object
        save_dict = json.loads(gamestate_str)
        gamestate = GameState(**save_dict['Game'])
        save_dict['Players'] = {k: states.PlayerState(**v) for k, v in save_dict['Players'].items()}
        f.close()

    logger.info(f"Game loaded from saves/{filename}.json")
    return gamestate

logger.debug("save_control module imported")