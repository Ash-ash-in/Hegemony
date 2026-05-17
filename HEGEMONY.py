############# START OF CODE TO MOVE #############
# This file should be moved to a main file once the game is fully developed. 
# For now, it serves as a testing ground for the gamestate and other objects. 
# It also allows us to easily set up a new game or load a saved game.

import logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("game.log", mode = 'w'),
        logging.StreamHandler()
        ]
    )


###### User Inputs #######
player_count = 2
save_file = None
###### User Inputs #######

############# END OF CODE TO MOVE #############

########## Initialise GameState ##########
import game.engine.save_control as save

if save_file:
    logging.debug(f"Loading game from save file: {save_file}")
    live_gamestate = save.load_game(save_file)
else:
    live_gamestate = save.new_game(player_count, "temporary_save")



