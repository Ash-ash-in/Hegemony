###################################
############# HEGEMONY ############
###################################
###### User Inputs #######
player_count = 2
save_file = None
filename = 'HegemonySave'
###### User Inputs #######

# Establish Log
import logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("game.log", mode = 'w'),
        logging.StreamHandler()
        ]
    )

# Check Parameters
# ----------------
if player_count < 2 | player_count > 4:
    raise Exception("Player count must be between 2 and 4")

########## Initialise GameState ##########
# ----------------------------------------
import game.engine.save_control as save

if save_file:
    logging.debug(f"Loading game from save file: {save_file}")
    live_gamestate = save.load_game(save_file)
else:
    live_gamestate = save.new_game(player_count)
    logging.debug(f'Created new save file: ')

# Setup easy references
logging.debug('Setting up player references')
player_list = live_gamestate.players
print(player_list)
working_class = player_list[0]
state = live_gamestate.players[-1]
capitalists = player_list[-2]
if player_count > 2:
    middle_class = player_list[2]

print(capitalists)