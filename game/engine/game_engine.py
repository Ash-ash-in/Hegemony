import logging
logger = logging.getLogger(__name__)
logger.debug("importing game_engine module")

def startup(player_count=None, filename=None):
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
    else:
        gamestate, filename = save.new_game(player_count)
        logging.info(f'Created new save file: {filename}')

    return gamestate

def gen_refs(gamestate):
    """
    Creates the references needed for the rest of the program.

    -   new_game and load_game return the same information,
        but they only store the raw game/player states.
    -   This function creates the variables that allows the engine to work
    """
    logger.debug("Reading save file")
    pc = gamestate.player_count
    from game.data.common import faction_play_order, PlayerReference
    active_factions = faction_play_order[:pc]
    existing_factions = active_factions + ['State']

    # Setup easy references
    logging.debug('Setting up player references')
    player_list = gamestate.players
    working_class = player_list[0]
    state = gamestate.players[-1]
    capitalists = player_list[-2]
    if pc > 2:
        middle_class = player_list[2]
    else:
        middle_class = None

    player_references = PlayerReference(
        active_factions,
        existing_factions,
        {
            'Working Class': working_class,
            'Capitalists': capitalists,
            'Middle Class': middle_class,
            'State': state
        }
    )

    return player_references

class DecisionContext:
    """
    Decides what the engine gives to an agent when they need to make a decsion
    AI and Humans receive the same information
    """
    def __init__(self, available: list, unavailable: list[tuple]):
        self.available_actions = available # List of actions, which should correspond to a function to call
        self.unavailable_actions = unavailable # List of (action, reason)

    
