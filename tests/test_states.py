"""
# tests/test_states.py

    UNIT TESTS for game/states.py - the player objects on their own.

    No GameState is needed: each test builds a single player object, changes it
    through its own methods, and checks the result. Expected values come from the
    rulebook (page numbers in comments), not from reading the implementation.

## Hierarchy
    This file can see builders.py and all game files.
"""
import pytest

from game.states import WorkingClass, MiddleClass, Capitalists, NPCState, PlayerState


# =============================================================================
# Money and loans (all players)
# Rulebook p33 "Loans": taking a Loan gains 50; paying one off costs 50.
# =============================================================================

@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass, NPCState])
def test_taking_a_loan_adds_one_loan_and_fifty_money(player_cls):
    player = player_cls()
    player._take_loan()
    assert player.loans == 1
    assert player.money == 50


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass, NPCState])
def test_repaying_a_loan_removes_one_loan_and_fifty_money(player_cls):
    player = player_cls()
    player._add_money(70)
    player._loans = 1
    player._repay_loan()
    assert player.loans == 0
    assert player.money == 20


def test_victory_points_never_go_below_zero():
    wc = WorkingClass()
    wc._add_victory_points(3)
    wc._add_victory_points(-10)
    assert wc.victory_points == 0


# =============================================================================
# Capitalist money: Revenue and Capital
# Rulebook p14 "General Note: Revenue & Capital" and p33 "Loans".
# =============================================================================

def test_capitalist_money_is_revenue_plus_capital():
    cap = Capitalists()
    cap._revenue, cap._capital = 30, 70
    assert cap.money == 100


def test_capitalist_income_goes_to_revenue():
    # "Whenever you gain money, unless stated otherwise, it goes to your Revenue."
    cap = Capitalists()
    cap._add_money(40)
    assert (cap.revenue, cap.capital) == (40, 0)


def test_capitalist_loan_money_goes_to_capital():
    # "when the Capitalist Class takes out a Loan, the 50 go to its Capital"
    cap = Capitalists()
    cap._take_loan()
    assert (cap.revenue, cap.capital, cap.loans) == (0, 50, 1)


def test_capitalist_loan_repayment_uses_capital_before_revenue():
    # "...when it wants to pay it off, it spends money from its Capital" - and if
    # Capital runs short, "the rest is paid from Revenue".
    cap = Capitalists()
    cap._capital, cap._revenue, cap._loans = 20, 100, 1
    cap._repay_loan()
    assert (cap.capital, cap.revenue, cap.loans) == (0, 70, 0)


# =============================================================================
# Population (Working Class and Middle Class)
# Rulebook p7: the Population track records the number of Workers in the game,
# and "that number determines the player's Population, shown directly beneath it".
# Setup (p10) starts the track at 10 Workers.
# =============================================================================

@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_population_track_counts_added_workers(player_cls):
    player = player_cls()
    for _ in range(12):
        player._add_population()
    assert player.population_track == 12


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_population_grows_as_the_track_grows(player_cls):
    # The exact table is printed on the player board, so this checks the shape
    # rather than exact values: 30 Workers must mean a bigger Population than 10.
    player = player_cls()
    for _ in range(10):
        player._add_population()
    population_at_10 = player.population
    for _ in range(20):
        player._add_population()
    assert player.population > population_at_10


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_population_shrinks_back_when_workers_leave(player_cls):
    player = player_cls()
    for _ in range(10):
        player._add_population()
    population_at_10 = player.population
    for _ in range(20):
        player._add_population()
    for _ in range(20):
        player._remove_population()
    assert player.population == population_at_10


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_population_cannot_go_below_zero_workers(player_cls):
    with pytest.raises(Exception):
        player_cls()._remove_population()


# =============================================================================
# Prosperity
# Rulebook p10: both classes start on the first space of the Prosperity track (0).
# Rulebook p14: dropping Prosperity on the first space does nothing.
# =============================================================================

@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_prosperity_starts_at_zero(player_cls):
    assert player_cls().prosperity == 0


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_prosperity_cannot_drop_below_zero(player_cls):
    player = player_cls()
    player._remove_prosperity()
    assert player.prosperity == 0


@pytest.mark.parametrize("player_cls", [WorkingClass, MiddleClass])
def test_prosperity_never_decreases_as_it_is_gained(player_cls):
    # The Middle Class track repeats some values (p7: "different than the Working
    # Class's track"), so gaining Prosperity may not always raise the number - but
    # it must never lower it, and it must stop at the end of the track.
    player = player_cls()
    seen = [player.prosperity]
    for _ in range(15):
        player._add_prosperity()
        seen.append(player.prosperity)
    assert seen == sorted(seen)
    assert seen[-1] == seen[-2]          # capped at the end of the track
    assert seen[-1] > 0


# =============================================================================
# Storage tiles (Capitalist Class and Middle Class)
# Rulebook p5: Storage tiles "effectively double the storage capacity".
# =============================================================================

@pytest.mark.parametrize("player_cls", [MiddleClass, Capitalists])
@pytest.mark.parametrize("resource", ["Food", "Luxuries", "Healthcare", "Education"])
def test_storage_tile_doubles_capacity(player_cls, resource):
    player = player_cls()
    base = player.storage[resource]
    player._add_storage(resource)
    assert player.storage[resource] == base * 2
    assert player.storages == 1


@pytest.mark.parametrize("player_cls", [MiddleClass, Capitalists])
def test_storage_tile_can_be_removed_again(player_cls):
    player = player_cls()
    base = player.storage["Food"]
    player._add_storage("Food")
    player._remove_storage("Food")
    assert player.storage["Food"] == base
    assert player.storages == 0


@pytest.mark.parametrize("player_cls", [MiddleClass, Capitalists])
def test_cannot_remove_a_storage_tile_you_dont_have(player_cls):
    with pytest.raises(Exception):
        player_cls()._remove_storage("Food")


# =============================================================================
# Faction-specific starting pieces
# Rulebook p3 component list: 7 Strike tokens, 6 Machinery tokens,
# 18 Legitimacy tokens (6 per class). Rulebook p10: Legitimacy markers start on
# the second space of each track.
# =============================================================================

def test_working_class_has_seven_strike_tokens():
    assert WorkingClass().strike_tokens == 7


def test_capitalists_have_six_machinery_tokens():
    assert Capitalists().machinery_tokens == 6


def test_player_state_has_six_legitimacy_tokens_per_class():
    tokens = PlayerState().legitimacy_tokens
    assert tokens == {"Working Class": 6, "Middle Class": 6, "Capitalists": 6}


def test_player_state_tracks_legitimacy_for_each_class():
    # MaskedState reads `.legitimacy` for 4-player games, so it must exist publicly.
    assert set(PlayerState().legitimacy) == {"Working Class", "Middle Class", "Capitalists"}


# =============================================================================
# Independence between objects
# Two players built with default arguments must never share the same dict/list -
# otherwise changing one game's State silently changes another game's State.
# (Python evaluates default arguments once, so `storage: dict = {...}` is shared.)
# =============================================================================

def test_separate_player_states_do_not_share_legitimacy():
    first, second = PlayerState(), PlayerState()
    first.legitimacy["Working Class"] = 99
    assert second.legitimacy["Working Class"] != 99


@pytest.mark.parametrize("state_cls", [NPCState, PlayerState])
def test_separate_states_do_not_share_storage(state_cls):
    first, second = state_cls(), state_cls()
    first.storage["Healthcare"] = 99
    assert second.storage["Healthcare"] != 99
