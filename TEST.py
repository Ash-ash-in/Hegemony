import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("testing.log"),
        logging.StreamHandler()
    ]
)

from game import tests
### Save Game Testing ###
# -----------------------
# tests.test_save_and_load()

### Creating gamestate for normal testing ###
# -------------------------------------------
from game.system import Engine
player_count = 3
agents = {
    'Working Class': 'Random',
    'Middle Class': 'Random',
    'Capitalists': 'Random'
}



settings = {
    'player_count': player_count,
    'agents': agents,
    'save_mode': 'new',
    'save_name': "test_save",
    'overwrite_file': True
}

engine = Engine()
LiveGamestate, LivePlayerRefs = engine.startup(settings)
engine.setup_agents(agents, LiveGamestate)

### Player Testing ###
# --------------------
# tests.test_player_functions(LiveGamestate, LivePlayerRefs)


### Game Flow Testing ###
# --------------------
engine.flow(LiveGamestate)