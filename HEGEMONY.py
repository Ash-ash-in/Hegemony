###################################
############# HEGEMONY ############
###################################
###### User Inputs #######
player_count = 3
filename = 'HegemonySave'
###### User Inputs #######

# Establish Log
# -------------
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
if filename:
    if type(filename) == int | type(filename) == float:
        raise Exception("save_file must be string or None type")
    
########## Initialise GameState ##########
# ----------------------------------------
import game.engine.save_control as save
import game.engine.game_engine as engine

LiveGamestate, PlayerRefs = engine.startup(player_count=2)

# Set up references
# -----------------
# player_references = engine.gen_refs(LiveGamestate) # Keep this or just look at gamestate?


print(PlayerRefs.capitalists)


