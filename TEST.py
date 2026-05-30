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
# tests.test_save_and_load()

### Creating gamestate for normal testing ###
# -------------------------------------------
player_count = 3
from game.engine.game_engine import startup
LiveGamestate, LiveRefs = startup(player_count, "test_save", overwrite=True)

### Player Testing ###
# --------------------
tests.test_player_functions(LiveGamestate, LiveRefs)
