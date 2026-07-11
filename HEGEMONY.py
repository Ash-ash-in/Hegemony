###################################
############# HEGEMONY ############
###################################

# Establish Log
# -------------
import logging
import os
try:
    os.remove("game.log")
except(FileNotFoundError):
    pass
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("game.log"),
        logging.StreamHandler()
    ]
)

# Import Config
import json
from game.data.classes import Config
with open(os.path.join("game","config.json"), 'r', encoding='utf-8') as file:
    config = Config(json.load(file))
    
    
########## Initialise GameState ##########
# ----------------------------------------
from game.engine import Engine

engine = Engine()
gamestate = engine.startup(config)
# Engine.flow(LiveGamestate)

print(gamestate.player_count)




