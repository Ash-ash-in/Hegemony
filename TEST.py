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
from game.engine.save_control import new_game
live_gamestate, filename = new_game(3, "test_save", overwrite=True)

# Setup easy references
logging.debug('Setting up player references')
player_list = live_gamestate.players
print(player_list)
working_class = player_list[0]
state = live_gamestate.players[-1]
capitalists = player_list[-2]
if player_count > 2:
    middle_class = player_list[2]

### Player Testing ###
# --------------------
tests.test_player_functions(live_gamestate)