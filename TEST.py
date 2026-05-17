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
tests.test_save_and_load()

# Creating gamestate for normal testing
from game.engine.save_control import new_game
test_gamestate = new_game(2, "test_save", overwrite=True)
### Player Testing ###
tests.test_player_functions(test_gamestate)