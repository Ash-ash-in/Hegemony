###################################
############# HEGEMONY ############
###################################

# Establish Log
# -------------
import logging
import os
try:
    os.remove(os.path.join("logs", "game.log"))
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

### Decision Log
from game.agents import decision_log
import orjsonl

# Read in old file
try:
    decisions = orjsonl.load(os.path.join("training","decisions.jsonl"))
except:
    decisions = []

# Add new data from this session
decisions.append(decision_log)

# Save file
orjsonl.save(os.path.join("training","decisions.jsonl"), decisions)


### End-Game Log
print(decisions)