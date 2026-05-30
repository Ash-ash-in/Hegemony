# import logging
# logger = logging.getLogger(__name__)
# logger.debug("importing save_control module")

# from pathlib import Path
# from datetime import datetime
# import json
# from dataclasses import asdict, replace, dataclass

# import game.data.factions as factions

# # Point to the saves folder
# directory = Path('saves')
# # Create directory if it doesn't exist
# directory.mkdir(parents=True, exist_ok=True)

# @dataclass
# class save:

#     # Point to and set up save directory
#     directory = Path('saves')
#     directory.mkdir(parents=True, exist_ok=True)

#     ### Methods ###

#     def save(gamestate, filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), overwrite = False):
#         """
#         Saves the json of a gamestate to a file
        
#         :param gamestate: GameState object to be saved
#         :param filename: str - Name of the file to save the gamestate to. 
#         """
#         logger.debug(f"save.save called with filename:{filename}, overwrite:{overwrite}")

#         # Write a new file if not exists, write a new file if exists
#         filepath = directory / filename
#         try:
#             f = open(f"{filepath}.json", "w" if overwrite else "x")
#         except FileExistsError:
#             logger.error(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
#             return
        
#         # Parse various state instances to dicts and write to file
#         players_dict = {}
#         i = 1
#         for player_instance in gamestate.players:
#             players_dict[i] = asdict(player_instance)
#             i += 1
        
#         save = {
#             "Game": asdict(gamestate),
#             "Players": players_dict
#         }
#         f.write(json.dumps(save, indent=4))
#         f.close()

#         logger.info(f"Game saved to {filename}")
#         return



#     def new_game(player_count, filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), overwrite = False):
#         """
#         Sets up a new game with the specified number of players and saves it to a file. Returns the gamestate object.
        
#         :param player_count: int - Number of factions to set up
#         :param filename: str - Name of the save file to create. Defaults to a timestamp.
#         """
#         logger.debug(f"save.new_game called with player_count: {player_count}")
#         from game.data import common

#         # Setup factions
#         active_factions = common.faction_instantiate_order[:player_count]
#         if player_count > 2: # Arrange factions in play order if middle class exists
#             index_order = [0,2,1,3]
#             active_factions = list(map(active_factions.__getitem__,index_order[:player_count]))
#             logger.debug("Reordered factions due to player_count > 2")
#         existing_factions = active_factions.copy()
#         logger.info(f"active_factions: {active_factions}")

#         # Append state if not controlled by a player
#         if player_count < 4:
#             existing_factions.append('State')
#             logger.debug("State added to game due to player_count < 4")
#         logger.info(f"existing_factions: {existing_factions}")

#         # Initialise gamestate
#         gamestate = common.GameState(
#             player_count = player_count,
#             players = {faction_name: factions.Player(faction_name) for faction_name in existing_factions}
#         )
#         logger.debug('Initial gamestate instantiated')

#         # Write a new file
#         filepath = directory / filename
#         try:
#             f = open(f"{filepath}.json", "w" if overwrite else "x")
#         except FileExistsError:
#             logger.error(f"File {filename}.json already exists.")
#             raise FileExistsError(f"File {filename}.json already exists. Use overwrite=True to overwrite the file.")
        
#         # Parse various state instances to dicts and write to file
#         save = {
#             "Game": asdict(gamestate),
#             "Players": {name:asdict(instance) for name, instance in gamestate.players.items()}
#         }
#         f.write(json.dumps(save, indent=4))
#         f.close()

#         logger.info(f"New game set up with player_count: {player_count}")
#         return gamestate, filename


#     def load(filename):
#         """
#         Loads a gamestate from a file and returns the gamestate object.
        
#         :param filename: str - Name of the save file to load
#         """
#         logger.debug(f"game.load called with filename:{filename}")

#         # Read the file
#         from game.data.common import GameState
#         with open(f"saves/{filename}.json", 'r') as f:
#             try:
#                 gamestate_str = f.read()
#             except FileNotFoundError:
#                 logger.error(f"File {filename}.json not found in saves folder.")
#                 return
            
#             # Convert the string back to a GameState object
#             save_dict = json.loads(gamestate_str)
#             gamestate = GameState(**save_dict['Game'])
#             gamestate.players = {k:factions.Player(**v) for k,v in save_dict['Players'].items()}
#             f.close()

#         logger.info(f"Game loaded from saves/{filename}.json")
#         return gamestate


#     def delete(filename):
#         """
#         Deletes a save file.
        
#         :param filename: str - Name of the save file to delete
#         """
#         logger.debug(f"save.delete called with filename:{filename}")
#         filepath = directory / f"{filename}.json"
#         try:
#             filepath.unlink()
#             logger.info(f"Save file {filename}.json deleted successfully.")
#         except FileNotFoundError:
#             logger.error(f"File {filename}.json not found in saves folder.")
#         return


# logger.debug("save_control module imported")