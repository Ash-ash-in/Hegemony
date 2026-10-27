"""
# tests/test_game_flow.py

    The engine running the game: phases, rounds, turns - and whole games.

    Blocks:
        1. Preparation phase      - interest on loans (fast, no full game)
        2. A whole game           - completes, and the board is still legal at the end
        3. Game structure         - rounds, turns and turn order, read from the log
        4. Decision log contents  - what was recorded, and when
        5. Reproducibility        - same seed, same game

    Blocks 2-5 play complete games with Random agents and are marked `slow`.
    Skip them while working with:   pytest -m "not slow"

## Hierarchy
    This file can see builders.py and all game files.
"""
import os
import random
from collections import Counter, defaultdict

import pytest

import builders as b

DECISIONS = os.path.join("training", "data", "decisions.jsonl")
FACTIONS = ["Working Class", "Middle Class", "Capitalists", "State"]
ALL_SIZES = [2, 3, 4]


def playing_factions(player_count: int) -> list[str]:
    """Rulebook p8: who actually takes turns at each player count, in turn order."""
    return {2: ["Working Class", "Capitalists"],
            3: ["Working Class", "Middle Class", "Capitalists"],
            4: FACTIONS}[player_count]


# =============================================================================
# 1. Preparation phase
# Rulebook p33: "As long as you have a Loan during the Preparation Phase of each
# round, you will have to pay an interest of 5. In case you are unable to pay that
# interest, you will have to take out another Loan to do so."
# =============================================================================

def run_preparation(gamestate):
    from game.engine import Engine
    return Engine().preparation_phase(gamestate)


def test_interest_is_five_per_loan(gs, wc):
    wc._loans, wc._money = 2, 30
    run_preparation(gs)
    assert (wc.loans, wc.money) == (2, 20)


def test_no_loans_means_no_interest(gs, wc):
    wc._money = 30
    run_preparation(gs)
    assert wc.money == 30


def test_unaffordable_interest_forces_another_loan(gs, wc):
    wc._loans, wc._money = 1, 0
    run_preparation(gs)
    assert (wc.loans, wc.money) == (2, 45)       # 0 + 50 (new loan) - 5 (interest)


def test_capitalists_pay_interest_from_capital(gs, cap):
    # p33: "whenever it pays interest ... it spends money from its Capital"
    cap._loans, cap._capital, cap._revenue = 1, 20, 40
    run_preparation(gs)
    assert (cap.capital, cap.revenue) == (15, 40)


# =============================================================================
# Shared setup for whole-game tests
# =============================================================================

def play_full_game(player_count: int, seed: int):
    """
    Plays one complete game the way HEGEMONY.py does, with Random agents.
    Must be run inside `workdir` - it writes decisions.jsonl and game_ids.csv.
    Returns (final gamestate, list of logged decision rows).
    """
    from game.assets.classes import Config
    from game.engine import Engine

    random.seed(seed)
    config = Config({
        "player_count": player_count,
        "agents": {f: "Random" for f in playing_factions(player_count)},
        "expansions": {"historical_events": 0, "crisis_and_control": 0},
    })
    engine = Engine()
    gamestate = engine.engine_startup(config)
    engine.flow(gamestate)
    rows = b.read_jsonl(DECISIONS) if os.path.exists(DECISIONS) else []
    return gamestate, rows


@pytest.fixture
def full_game(workdir, player_count, seed):
    return play_full_game(player_count, seed)


def action_steps(rows, step: int):
    """Only the choose_action decisions for one step (1 or 2) of each turn."""
    return [r for r in rows
            if r["call"]["decision_type"] == "choose_action" and r["call"]["step"][0] == step]


def meta(row):
    return row["call"]["gamestate"]["GameMetaData"]


# =============================================================================
# 2. A whole game
# =============================================================================

@pytest.mark.slow
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_full_game_completes(full_game):
    gamestate, rows = full_game
    assert rows, "a whole game was played but no decisions were saved"


@pytest.mark.slow
@pytest.mark.parametrize("player_count", ALL_SIZES)
@pytest.mark.parametrize("seed", range(5))
def test_board_is_still_legal_after_a_full_game(full_game):
    gamestate, _ = full_game
    assert gamestate.corroborate_worker_count()
    for faction, player in gamestate.players.items():
        assert player.money >= 0, f"{faction} ended with negative money"
        assert player.loans >= 0, faction
        assert player.victory_points >= 0, faction


# =============================================================================
# 3. Game structure (read back from the decision log)
# Rulebook p11: 5 rounds. Each Action Phase is 5 turns; turn order is always
# Working Class, Middle Class, Capitalists, State, skipping roles not playing.
# =============================================================================

@pytest.mark.slow
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_actions_happen_in_rounds_one_to_five(full_game):
    _, rows = full_game
    assert sorted({meta(r)["round"] for r in action_steps(rows, 1)}) == [1, 2, 3, 4, 5]


@pytest.mark.slow
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_every_player_takes_five_turns_per_round(full_game, player_count):
    _, rows = full_game
    turns = Counter((meta(r)["round"], r["call"]["faction"]) for r in action_steps(rows, 1))
    playing = playing_factions(player_count)
    for round_number in range(1, 6):
        for faction in playing:
            assert turns[(round_number, faction)] == 5, (round_number, faction)


@pytest.mark.slow
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_turn_order_within_each_round(full_game, player_count):
    _, rows = full_game
    playing = playing_factions(player_count)
    by_round = defaultdict(list)
    for r in action_steps(rows, 1):
        by_round[meta(r)["round"]].append(r["call"]["faction"])
    for round_number, order in by_round.items():
        assert order == playing * 5, f"round {round_number}"


# =============================================================================
# 4. Decision log contents
# =============================================================================

@pytest.mark.slow
def test_action_decisions_are_logged_in_the_action_phase(full_game):
    _, rows = full_game
    phases = {meta(r)["phase"] for r in action_steps(rows, 1) + action_steps(rows, 2)}
    assert phases == {"Action"}


@pytest.mark.slow
def test_observation_records_whose_turn_it_is(full_game):
    _, rows = full_game
    for r in action_steps(rows, 1):
        assert meta(r)["player_turn"] == r["call"]["faction"]


@pytest.mark.slow
def test_each_turn_logs_two_action_steps(full_game):
    # Step 1 and step 2 of the Free/Main action pair, both recorded.
    _, rows = full_game
    assert len(action_steps(rows, 1)) == len(action_steps(rows, 2))


@pytest.mark.slow
def test_each_decision_is_logged_once(full_game):
    # The same (context, step) appearing twice means a chain was saved twice.
    _, rows = full_game
    keys = Counter((r["call"]["seq"], tuple(r["call"]["step"])) for r in rows)
    duplicates = {k: n for k, n in keys.items() if n > 1}
    assert duplicates == {}


@pytest.mark.slow
def test_step_two_sees_the_effect_of_step_one(full_game):
    # If step 1 actually did something, the observation at step 2 must differ -
    # otherwise the agent decided step 2 looking at an out-of-date board.
    _, rows = full_game
    step_one = {r["call"]["seq"]: r for r in action_steps(rows, 1)}
    checked = 0
    for second in action_steps(rows, 2):
        first = step_one.get(second["call"]["seq"])
        if first is None or first["response"]["answer"].get("action") == "None":
            continue
        checked += 1
        assert second["call"]["gamestate"] != first["call"]["gamestate"], second["call"]["seq"]
    assert checked > 0


@pytest.mark.slow
def test_every_logged_answer_was_one_of_the_options(full_game):
    _, rows = full_game
    for r in rows:
        for key, value in r["response"]["answer"].items():
            assert value in r["call"]["available_choices"][key]


@pytest.mark.slow
def test_logged_rewards_are_numbers(full_game):
    _, rows = full_game
    assert all(isinstance(r["reward"], (int, float)) for r in rows)


# =============================================================================
# 5. Reproducibility
# With the same seed, two games must make exactly the same decisions. Without this
# you can't replay a game that went wrong.
# =============================================================================

@pytest.mark.slow
def test_same_seed_gives_the_same_game(workdir):
    def answers(rows):
        return [(r["call"]["faction"], r["response"]["answer"]) for r in rows]

    _, first = play_full_game(2, seed=7)
    os.remove(DECISIONS)
    _, second = play_full_game(2, seed=7)
    assert answers(first) == answers(second)
