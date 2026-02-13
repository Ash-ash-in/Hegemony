

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add the parent directory to the system path
    sys.path.append(str(Path(__file__).resolve().parent.parent))

    import main
    from main import main as run_main
    from main import Game
  
    run_main(Game)


    print(Game.players['WC'].population)
    Game.players['WC'].add_worker()
    Game.players['WC'].add_worker()
    Game.players['WC'].add_worker()
    print(Game.players['WC'].population)