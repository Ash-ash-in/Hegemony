import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from datetime import datetime
logging.basicConfig(filename='game.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import game.data.states as states

def save_game(gamestate, filename):
    # Saves the text of a gamestate to a file
    logging.debug(f"Saving game to saves/{filename}.txt")
    with open(f"saves/{filename}.txt", 'w') as f:
        f.write(str(gamestate))
    logging.info(f"Game saved to {filename}")
    return

def new_game(player_count, filename):
    logging.debug(f"Setting up new game with {player_count} players")
    from game.data.common import faction_list
    active_factions = faction_list[:player_count]
    gamestate = states.GameState(
        player_count = player_count,
        players = {faction_name: states.PlayerState(faction=faction_name) for faction_name in active_factions}
    )
    save_game(gamestate, filename)
    logging.info(f"New game set up with {player_count}")
    return gamestate

def load_game(filename):
    logging.debug(f"Loading game from saves/{filename}.txt")
    with open(f"saves/{filename}.txt", 'r') as f:
        gamestate_str = f.read()
        # Convert the string back to a GameState object
        gamestate = eval(gamestate_str)
    logging.info(f"Game loaded from saves/{filename}.txt")
    return gamestate
    

new_game(1, "test_save")