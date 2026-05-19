import logging
logger = logging.getLogger(__name__)
logger.debug("Importing save_testing module")

def test_save_and_load():
    logger.info("Starting test_save_and_load")
    from game.engine import save_control as save

    # Clear existing test save file if it exists
    logger.debug("Checking for existing test save file")
    import os
    test_save_path = save.directory / "test_save.json"
    if test_save_path.exists():
        os.remove(test_save_path)
        logger.info("Existing test save file removed.")
    else:
        logger.debug("No existing test save file found, proceeding with test.")

    # Create a test gamestate
    logger.debug("Creating test gamestate")
    test_gamestate, filename = save.new_game(2, "test_save", overwrite=False)
    logger.info(f"Test gamestate created")

    # Confirm new file exists
    if test_save_path.exists():
        logger.debug("Test save file created successfully.")
    else:
        logger.warning("Test save file was not created.")
        assert False, "Test save file was not created."

    # Attempt to save without overwrite permission, should raise FileExistsError
    logger.debug("Testing save without overwrite permission")
    try:
        save.new_game(2, "test_save", overwrite=False)
    except FileExistsError:
        logger.info("File already exists, as expected.")
    else:   
        logger.warning("File should have existed but didn't.")
        assert False, "File should have existed but didn't."

    # Save the gamestate
    logger.debug("Saving test gamestate")
    save.save_game(test_gamestate, "test_save", overwrite=False)
    logger.info("Test gamestate saved")

    # Load the gamestate
    logger.debug("Loading test gamestate")
    loaded_gamestate = save.load_game("test_save")
    logger.debug(f"Original gamestate: {test_gamestate}")
    logger.debug(f"Type of original gamestate: {type(test_gamestate)}")
    logger.debug(f"Loaded gamestate: {loaded_gamestate}")
    logger.debug(f"Type of loaded gamestate: {type(loaded_gamestate)}")
    logger.info("Test gamestate loaded")

    # Check if the loaded gamestate matches the original gamestate
    logger.debug("Comparing original and loaded gamestate")
    assert loaded_gamestate == test_gamestate, "Loaded gamestate does not match the original gamestate"

    # Test overwrite functionality
    logger.debug("Testing overwrite functionality")
    save.new_game(2, "test_save", overwrite=True)
    logger.info("File overwritten successfully.")

    # Test delete save functionality
    logger.debug("Testing delete save functionality")
    save.delete_save("test_save")
    if not test_save_path.exists():
        logger.info("Test save file deleted successfully.")
    else:
        logger.warning("Test save file was not deleted.")
        assert False, "Test save file was not deleted."

    # Test setup 3 player game
    logger.debug("Testing 3 player setup")
    save.new_game(3, "test_save", overwrite=True)
    logger.info("3 player game setup successfully.")

    # Test setup 4 player game
    logger.debug("Testing 4 player setup")
    save.new_game(4, "test_save", overwrite=True)
    logger.info("4 player game setup successfully.")
    return

def test_player_functions(gamestate):
    logger.debug("Starting test_player_functions")
    from game.rules import rules

    ### Money transfer validity process ###
    # Impossible + non-mandatory = prevented
    logger.debug("Testing validity of non-mandatory transfers")
    result = rules.MoneyTransfer.can_transfer(working_class, capitalists, 10, False)[0]
    if result:
        raise Exception('Validity check failed to prevent impossible transfer')
    logger.debug("Impossible + non-mandatory: passed")
    # Impossible + non-mandatory = allowed
    result = rules.MoneyTransfer.can_transfer(working_class, capitalists, 10, True)[0]
    if not result:
        raise Exception('Validity check prevented a mandatory transfer')
    logger.debug("Impossible + mandatory: passed")
    logger.info("Transfer validity check works")
    
    return

logger.debug("Finished importing tests module")