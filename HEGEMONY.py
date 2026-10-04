###################################
############# HEGEMONY ############
###################################

# Establish Log
# -------------
import logging
import os

try:
    os.remove(os.path.join("logs", "game.log")) # Do we really want to remove every time?
except(FileNotFoundError):
    pass

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", "game.log")),
        logging.StreamHandler()
    ]
)
    
# Import Config
import json
from game.data.classes import Config
with open("config.json", 'r', encoding='utf-8') as file:
    config = Config(json.load(file))

    
########## Initialise GameState ##########
# ----------------------------------------
from game.engine import Engine

engine = Engine()
gamestate = engine.engine_startup(config)
engine.flow(gamestate)

########## Save Training Data ##########

### Game ID
config.game_id.save()
from training.postprocessing import save_decision_log
save_decision_log()


### End-Game Log
