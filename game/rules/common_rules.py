from dataclasses import replace

def add_victory_points(game, player, points):

    current_points = game.players[player].victory_points
    new_points = current_points + points
    if new_points < 0:
        new_points = 0
    players_dict = {
        **game.players,
    }
    players_dict[player] = replace(
        game.players[player],
        victory_points = new_points
    )
    new_game = replace(
        game, 
        players = players_dict
    )
    return new_game



