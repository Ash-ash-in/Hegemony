# This file should be moved to a main file once the game is fully developed. 
# For now, it serves as a testing ground for the gamestate and other objects. It also allows us to easily set up a new game or load a saved game.

###### User Inputs #######
player_count = 4
save_file = None
###### User Inputs #######

########## Initialise GameState ##########
import engine.save_control as save
from dataclasses import dataclass, replace

if save_file:
    live_gamestate = save.load_game(save_file)
else:
    live_gamestate = save.new_game(player_count)
    save.save_game(live_gamestate, "temporary_save")

# print(str(live_gamestate))
