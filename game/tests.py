import logging
logger = logging.getLogger(__name__)
logger.debug("Importing save_testing module")

def test_save_and_load():
    logger.info("Starting test_save_and_load")
    from game.system import Save
    import os

    # Clear existing test save file if it exists
    logger.debug("Checking for existing test save file")
    test_save_path = os.path.join(Save.directory, "test_save.json")
    if os.path.exists(test_save_path):
        os.remove(test_save_path)
        logger.info("Existing test save file removed.")
    else:
        logger.debug("No existing test save file found, proceeding with test.")

    # Create a test gamestate
    logger.debug("TEST Creating test gamestate")
    test_gamestate, filename = Save.new_game(2, "test_save", overwrite=False)
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
        gamestate, filename = Save.new_game(2, "test_save", overwrite=False)
    except(FileExistsError):
        logger.info("Overwritng without permission throws exception PASS")
    else:   
        logger.warning("File should have existed but didn't.")
        assert False, "File should have existed but didn't."

    # Test delete save functionality
    logger.debug("TEST delete save functionality")
    Save.delete_save("test_save")
    if not os.path.exists(test_save_path):
        logger.info("Test save file deleted PASS.")
    else:
        logger.warning("Test save file was not deleted.")
        assert False, "Test save file was not deleted."

    # Save the gamestate
    logger.debug("TEST saved gamestate matches file loaded")
    logger.debug("Saving test gamestate")
    Save.save_game(test_gamestate, "test_save", overwrite=False)
    logger.info("Test gamestate saved")

    # Load the gamestate
    logger.debug("Loading test gamestate")
    loaded_gamestate = Save.load_game("test_save")
    # Check if the loaded gamestate matches the original gamestate
    test_dict = test_gamestate.to_dict()
    load_dict = loaded_gamestate.to_dict()
    match=True
    for k,v in test_dict.items(): # All gamestate vars
        if k == 'players':
            for k2, v2 in test_dict['players'].items(): # Dict of players
                for k3, v3 in v2.to_dict().items(): # All player vars
                    if v3 != load_dict['players'][k2].to_dict()[k3]:
                        logger.debug(f'player {k2} mismatch on {k3}')
                        match=False
        elif load_dict[k] != v: # Otherwise just compare the vars
            match=False
    if not match:
        logger.debug(f"Original gamestate: {test_gamestate}")
        logger.debug(f"Type of original gamestate: {type(test_gamestate)}")
        logger.debug(f"Loaded gamestate: {loaded_gamestate}")
        logger.debug(f"Type of loaded gamestate: {type(loaded_gamestate)}")
        logger.error('Loaded gamestate does not match')
        print('loaded gamestate:')
        print(loaded_gamestate)
        print('new gamestate:')
        print(test_gamestate)
        raise Exception('Loaded gamestate did not match')
    logger.info("Test gamestate loaded matches saved PASS")

    # Test overwrite functionality
    logger.debug("TEST overwrite functionality")
    Save.new_game(2, "test_save", overwrite=True)
    logger.info("File overwritten PASS.")

    # Test setup 3 player game
    logger.debug("TEST 3 player setup")
    Save.new_game(3, "test_save", overwrite=True)
    logger.info("3 player game setup PASS.")

    # Test setup 4 player game
    logger.debug("TEST 4 player setup")
    Save.new_game(4, "test_save", overwrite=True)
    logger.info("4 player game setup PASS.")
    return

def test_player_functions(gamestate, player_references):
    logger.debug("Starting test_player_functions")
    from game import rules

    ### Victory Points ###

    ### Money transfer validity process ###
    # Impossible + non-mandatory = forbidden
    check = rules.MoneyTransfer.check(player_references.working_class, player_references.capitalists, 10, False)
    if check.validity:
        raise Exception('Validity check failed to prevent impossible transfer')
    logger.info("Impossible + non-mandatory: PASS")
    # Impossible + mandatory = allowed
    check = rules.MoneyTransfer.check(player_references.working_class, player_references.capitalists, 10, True)
    if not check.validity:
        raise Exception('Validity check prevented a mandatory transfer')
    logger.info("Impossible + mandatory: PASS")
    # From bank = allowed
    check = rules.MoneyTransfer.check(None, player_references.capitalists, 10, True)
    if not check.validity:
        raise Exception('Validity check prevented a transfer from the bank')
    logger.info("From bank: PASS")
    # To bank, impossible, mandatory = allowed
    check = rules.MoneyTransfer.check(player_references.capitalists, None, 10, True)
    if not check.validity:
        raise Exception('Validity check prevented a mandatory transfer to the bank')
    logger.info("To bank, impossible, mandatory: PASS")
    # To bank, impossible, not mandatory = forbidden
    check = rules.MoneyTransfer.check(player_references.capitalists, None, 10, False)
    if check.validity:
        raise Exception('Validity check allowed a non-mandatory impossible transfer to the bank')
    logger.info("To bank, impossible, non-mandatory: PASS")
    logger.info("All transfer validity checks passed")

    ### Money transfer action process ###
    # Try impossible action without validity check
    try:
        rules.MoneyTransfer.resolve(player_references.capitalists, None, 10, False)
    except:
        logger.info('Impossible money transfer prevented with exception raised')
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
        logger.info('Money shuffle PASS')
    else:
        raise Exception('Unexpected money values during shuffle')

    return

logger.debug("Finished importing tests module")