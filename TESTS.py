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
from dataclasses import asdict, replace
import json

save_testing.test_save_and_load()

