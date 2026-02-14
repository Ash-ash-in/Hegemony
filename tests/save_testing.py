import logging
logger = logging.getLogger(__name__)
logger.debug("Importing save_testing module")

def test_save_and_load():
    logger.info("Starting test_save_and_load")
    from game.engine import save_control as save
    from game.data import states

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
    test_gamestate = save.new_game(2, "test_save", overwrite=False)
    logger.debug(f"Test gamestate created")

    # Attempt to save without overwrite permission, should raise FileExistsError
    logger.debug("Testing save without overwrite permission")
    try:
        save.new_game(2, "test_save", overwrite=False)
    except FileExistsError:
        logger.debug("File already exists, as expected.")
    else:   
        logger.warning("File should have existed but didn't.")
        assert False, "File should have existed but didn't."

    # Save the gamestate
    logger.debug("Saving test gamestate")
    save.save_game(test_gamestate, "test_save", overwrite=False)
    logger.debug("Test gamestate saved")

    # Load the gamestate
    logger.debug("Loading test gamestate")
    loaded_gamestate = save.load_game("test_save")
    print(f"Original gamestate: {test_gamestate}")
    print(f"Type of original gamestate: {type(test_gamestate)}")
    print(f"Loaded gamestate: {loaded_gamestate}")
    print(f"Type of loaded gamestate: {type(loaded_gamestate)}")
    logger.debug("Test gamestate loaded")

    # Check if the loaded gamestate matches the original gamestate
    logger.debug("Comparing original and loaded gamestate")
    assert loaded_gamestate == test_gamestate, "Loaded gamestate does not match the original gamestate"

    save.new_game(2, "test_save", overwrite=True)
    logger.info("File overwritten successfully.")

    return

logger.debug("save_testing module imported")