def add_victory_points(player, points):
    player.victory_points += points
    # Ensure victory points do not go negative
    if player.victory_points < 0:
        player.victory_points = 0