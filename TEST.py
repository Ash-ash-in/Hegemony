import logging
logging.basicConfig(
    level=logging.DEBUG,
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
from game.agents import RandomAgent
player_count = 3
agents = {
    'Working Class': RandomAgent,
    'Middle Class': RandomAgent,
    'Capitalists': RandomAgent
}
engine = Engine(agents)
LiveGamestate, LiveRefs = engine.startup(player_count, "test_save", overwrite=True)

### Player Testing ###
# --------------------
tests.test_player_functions(LiveGamestate, LiveRefs)


### Game Flow Testing ###
# --------------------
engine.flow(LiveGamestate)