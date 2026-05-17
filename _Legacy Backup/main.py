from classes import GameState
Game = GameState()

def main(Game):
    import sys
    from pathlib import Path


    # Get the current working directory
    current_dir = Path(__file__).parent.resolve()
    print(f"Current working directory: {current_dir}")

    # Setup logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.debug('Log started')

    ## TEMPORARY ## Remove this when the game is fully implemented
    # Rule variables
    Game.player_count = 4

    # Import custom modules
    import setup

    # Setup
    setup.instantiate_game(Game)
    setup.setup_game(Game)



    

if __name__ == "__main__":

    main(Game)
    Game.players['WC'].receive_money(1000)
    print(Game.players['WC'].money)
    Game.players['WC'].pay_money(500)
    print(Game.players['WC'].money)
    Game.players['CC'].receive_money(500, 'Revenue')
    print(f"Capitalist money = {Game.players['CC'].money}")
    print(f"Capitalist revenue = {Game.players['CC'].money}")
    Game.players['CC'].pay_money(45, 'Revenue')
    print(f"Capitalist money = {Game.players['CC'].money}")
    print(f"Capitalist revenue = {Game.players['CC'].money}")
    Game.players['CC'].pay_money(1000, 'Revenue', 'Yes')
    print(f"Capitalist money = {Game.players['CC'].money}")
    print(f"Capitalist revenue = {Game.players['CC'].money}")
    print(f"Capitalist loans = {Game.players['CC'].loans}")  


