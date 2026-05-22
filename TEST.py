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
player_count = 3
from game.engine.game_engine import startup
LiveGamestate, PlayerRefs = startup(player_count, "test_save", overwrite=True)

# Setup easy references
logging.debug('Setting up player references')
player_list = list(LiveGamestate.players.keys())
working_class = player_list[0]
state = list(LiveGamestate.players.keys())[-1]
capitalists = player_list[-2]
if player_count > 2:
    middle_class = player_list[2]
### Player Testing ###
# --------------------
tests.test_player_functions(LiveGamestate, PlayerRefs)