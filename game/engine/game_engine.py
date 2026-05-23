import logging
logger = logging.getLogger(__name__)
logger.debug("importing game_engine module")

def startup(player_count=None, filename=None, overwrite=False):
    """
    Process for launching a game.
    Handles validity checks and decides whether to load or start new game
    
    If player_count is None, a game is loaded
    If player_count exists, a new game is created
        New game uses filename if provided, else creates from timestamp
    If both player_count and filename are none, raise exception
    """
    # Validity Checks
    if filename == 'None':
        raise Exception('filename cannot be null')
    if filename:
        if type(filename) != str:
            raise Exception('filename must be a string')
    if player_count:
        if type(player_count) != int:
            raise Exception('player_count must be an integer')
        
    # Load / Create savefile
    logging.debug(f"engine.startup called with player_count: {player_count if player_count else 'None'} and filename: {filename if filename else 'None'}")
    import game.engine.save_control as save
    if player_count is None:
        if filename is None:
            raise Exception('Must provide either filename or player_count when calling setup')
        logging.info(f"Loading game from save file: {filename}")
        gamestate = save.load_game(filename)
        player_count = gamestate.player_count
    else:
        gamestate, filename = save.new_game(player_count, filename=filename, overwrite=overwrite)
        logging.info(f'Created new save file: {filename}')

    from game.data import common
    player_references = common.PlayerReference(
        common.faction_instantiate_order[:player_count],
        common.faction_play_order,
        working_class=gamestate.players['Working Class'],
        middle_class=gamestate.players['Middle Class'] if player_count > 2 else None,
        capitalists = gamestate.players['Capitalists'],
        state=gamestate.players['State']
    )

    return gamestate, player_references



class DecisionContext:
    """
    Decides what the engine gives to an agent when they need to make a decsion
    AI and Humans receive the same information
    """
    def __init__(self, available: list, unavailable: list[tuple]):
        self.available_actions = available # List of actions, which should correspond to a function to call
        self.unavailable_actions = unavailable # List of (action, reason)

    
