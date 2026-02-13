
import subprocess

subprocess.call(["python", "game/data/states.py"])

import game.data.states as states

GameState = GameState(
    player_count = 4,
    turn = 0,
    round = 0,
    active_player = 0,
    players = []
)

GameState.players.append(

    PlayerState(
    faction = "Working Class"
    )
)

print(GameState.players)
