import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("testing.log"),
        logging.StreamHandler()
    ]
)


from tests import save_testing
from game.engine import save_control as save
from dataclasses import asdict
import json

save_testing.test_save_and_load()



# new_gamestate = save.new_game(2, "test_save", overwrite=True)
# save = {
#     "Game": asdict(new_gamestate),
#     "Players": {k: asdict(v) for k, v in new_gamestate.players.items()}
# }
# json_string = json.dumps(save, indent=4)
# print(json_string)

