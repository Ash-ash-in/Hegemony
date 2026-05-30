import logging
logger = logging.getLogger(__name__)
logger.debug("Importing save_testing module")

def test_save_and_load():
    logger.info("Starting test_save_and_load")
    from game.engine.game_engine import save
    import os

    # Clear existing test save file if it exists
    logger.debug("Checking for existing test save file")
    test_save_path = os.path.join(save.directory, "test_save.json")
    if os.path.exists(test_save_path):
        os.remove(test_save_path)
        logger.info("Existing test save file removed.")
    else:
        logger.debug("No existing test save file found, proceeding with test.")

    # Create a test gamestate
    logger.debug("TEST Creating test gamestate")
    test_gamestate, filename = save.new_game(2, "test_save", overwrite=False)
    logger.info(f"Test gamestate created")

    # Confirm new file exists
    if os.path.exists(test_save_path):
        logger.debug("Test save file created PASS.")
    else:
        logger.warning("Test save file was not created.")
        assert False, "Test save file was not created."

    # Attempt to save without overwrite permission, should raise FileExistsError
    logger.debug("TEST save without overwrite permission throws exception")
    try:
        save.new_game(2, "test_save", overwrite=False)
    except FileExistsError:
        logger.info("Overwritng without permission throws exception PASS")
    else:   
        logger.warning("File should have existed but didn't.")
        assert False, "File should have existed but didn't."

    # Save the gamestate
    logger.debug("TEST saved gamestate matches file loaded")
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
    # Check if the loaded gamestate matches the original gamestate
    assert loaded_gamestate == test_gamestate, "Loaded gamestate does not match the original gamestate"
    logger.info("Test gamestate loaded matches saved PASS")

    # Test overwrite functionality
    logger.debug("TEST overwrite functionality")
    save.new_game(2, "test_save", overwrite=True)
    logger.info("File overwritten PASS.")

    # Test delete save functionality
    logger.debug("TEST delete save functionality")
    save.delete_save("test_save")
    if not os.path.exists(test_save_path):
        logger.info("Test save file deleted PASS.")
    else:
        logger.warning("Test save file was not deleted.")
        assert False, "Test save file was not deleted."

    # Test setup 3 player game
    logger.debug("TEST 3 player setup")
    save.new_game(3, "test_save", overwrite=True)
    logger.info("3 player game setup PASS.")

    # Test setup 4 player game
    logger.debug("TEST 4 player setup")
    save.new_game(4, "test_save", overwrite=True)
    logger.info("4 player game setup PASS.")
    return

def test_player_functions(gamestate, player_references):
    logger.debug("Starting test_player_functions")
    from game.rules import rules

    ### Money transfer validity process ###
    # Impossible + non-mandatory = forbidden
    result = rules.MoneyTransfer.check(player_references.working_class, player_references.capitalists, 10, False)[0]
    if result:
        raise Exception('Validity check failed to prevent impossible transfer')
    logger.debug("Impossible + non-mandatory: PASS")
    # Impossible + mandatory = allowed
    result = rules.MoneyTransfer.check(player_references.working_class, player_references.capitalists, 10, True)[0]
    if not result:
        raise Exception('Validity check prevented a mandatory transfer')
    logger.debug("Impossible + mandatory: PASS")
    # From bank = allowed
    result = rules.MoneyTransfer.check(None, player_references.capitalists, 10, True)[0]
    if not result:
        raise Exception('Validity check prevented a transfer from the bank')
    logger.debug("From bank: PASS")
    # To bank, impossible, mandatory = allowed
    result = rules.MoneyTransfer.check(player_references.capitalists, None, 10, True)[0]
    if not result:
        raise Exception('Validity check prevented a mandatory transfer to the bank')
    logger.debug("To bank, impossible, mandatory: PASS")
    # To bank, impossible, not mandatory = forbidden
    result = rules.MoneyTransfer.check(player_references.capitalists, None, 10, False)[0]
    if result:
        raise Exception('Validity check allowed a non-mandatory impossible transfer to the bank')
    logger.debug("To bank, impossible, non-mandatory: PASS")
    logger.info("All transfer validity checks passed")

    ### Money transfer action process ###
    # Try impossible action without validity check
    try:
        rules.MoneyTransfer.resolve(player_references.capitalists, None, 10, False)
    except:
        logger.debug('Impossible money transfer prevented with exception raised')
    else:
        raise Exception('Impossible money transfer not prevented')
    
    # Shuffle money around
    logger.debug("TEST Shuffling money and checking final values match expectation")
    rules.MoneyTransfer.resolve(None, player_references.capitalists, 100, False).print()
    logger.debug('Added 100 money to capitalists from bank')
    rules.MoneyTransfer.resolve(player_references.capitalists, player_references.working_class,  200, True).print()
    logger.debug('Sent mandatory payment of 200 to working class from capitalists')
    rules.MoneyTransfer.resolve(player_references.capitalists, None,  100, True).print()
    rules.MoneyTransfer.resolve(player_references.working_class, None,  200, True).print()
    logger.debug('Removed 100 from Working Class and Capitalists')
    if player_references.capitalists.money == 0 and player_references.working_class.money == 0:
        logger.debug('Money shuffle PASS')
    else:
        raise Exception('Unexpected money values during shuffle')

    return

logger.debug("Finished importing tests module")