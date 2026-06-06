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
tests.test_save_and_load()

### Creating gamestate for normal testing ###
# -------------------------------------------
from game.system import Engine
player_count = 3
agents = {
    'Working Class': 'Random',
    'Middle Class': 'Random',
    'Capitalists': 'Random'
}
engine = Engine()
LiveGamestate, LivePlayerRefs = engine.startup(agents, player_count, "test_save", overwrite=True)
engine.setup_agents(agents, LiveGamestate)

### Player Testing ###
# --------------------
tests.test_player_functions(LiveGamestate, LivePlayerRefs)


### Game Flow Testing ###
# --------------------
engine.flow(LiveGamestate)