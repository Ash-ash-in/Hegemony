"""
# tests/test_decision_data.py

    Is training data recorded correctly, and at the right moments?

    Blocks:
        1. DecisionLogEntry        - one decision, frozen at the moment it was made
        2. Scoring a decision chain - where the reward goes, and what earns one
        3. Saving to disk          - append-only JSONL, one line per decision
        4. Game IDs                - unique, correctly coded, saved once per game

    Every test that writes files uses the `workdir` fixture, so nothing touches
    your real training/data folder.

## Hierarchy
    This file can see builders.py and all game files.
"""
import os

import orjson
import pytest

import builders as b
from game.assets.messages import AgentAnswer, DecisionLogEntry


def entry_for(gamestate, player, action="TestAction1"):
    """One logged decision: player was offered actions and picked `action`."""
    return DecisionLogEntry(b.make_call(gamestate, player), AgentAnswer({"action": action}))


# =============================================================================
# 1. DecisionLogEntry
# The entry must capture the call and answer AS THEY WERE: later changes to the
# game, or to the call object, must not rewrite the record.
# =============================================================================

def test_entry_records_call_response_and_reward(gs, wc):
    entry = entry_for(gs, wc)
    assert entry.call["faction"] == "Working Class"
    assert entry.response["answer"] == {"action": "TestAction1"}
    assert entry.reward == 0


def test_entry_observation_is_readable_as_a_dict(gs, wc):
    # score_decision reads entry.call["gamestate"]["PlayerData"]... - so the
    # observation must be stored as nested dicts, not as a MaskedState object.
    entry = entry_for(gs, wc)
    assert entry.call["gamestate"]["PlayerData"]["Working Class"]["money"] == 0


def test_entry_is_frozen_when_created(gs, wc):
    call = b.make_call(gs, wc)
    entry = DecisionLogEntry(call, AgentAnswer({"action": "TestAction1"}))
    call.available_choices["action"].append("Tampered")
    wc._add_money(500)
    assert "Tampered" not in entry.call["available_choices"]["action"]
    assert entry.call["gamestate"]["PlayerData"]["Working Class"]["money"] == 0


@pytest.mark.parametrize("player_count", [2, 3, 4])
def test_entry_can_be_written_as_json(started_gs, wc):
    entry = DecisionLogEntry(b.make_call(started_gs, wc), AgentAnswer({"action": "TestAction1"}))
    orjson.dumps(entry.__dict__)        # raises if anything isn't JSON-serialisable


def test_reward_can_be_assigned_later(gs, wc):
    entry = entry_for(gs, wc)
    entry.assign_reward(1.5)
    assert entry.reward == 1.5


# =============================================================================
# 2. Scoring a decision chain
# A chain = every decision made during one action (main decision + sub-decisions).
# The reward compares the player before the chain (first entry's observation)
# with the player after it, and is credited to the LAST decision only - the
# earlier ones get theirs by backfilling in post-processing.
# =============================================================================

def score(chain, gamestate, player):
    from training.postprocessing import score_decision
    return score_decision(chain, gamestate, player)


def test_reward_goes_on_the_last_entry_only(gs, wc):
    chain = [entry_for(gs, wc), entry_for(gs, wc), entry_for(gs, wc)]
    wc._add_money(50)
    score(chain, gs, wc)
    assert [e.reward for e in chain[:-1]] == [0, 0]
    assert chain[-1].reward != 0


def test_nothing_changing_earns_zero_reward(gs, wc):
    wc._influence = 3        # non-zero, so a precedence slip like `post - pre * 0.5` shows up
    chain = [entry_for(gs, wc)]
    score(chain, gs, wc)
    assert chain[-1].reward == 0


@pytest.mark.parametrize("change, direction", [
    (lambda p: p._add_money(50), +1),
    (lambda p: p._add_victory_points(3), +1),
    (lambda p: p.resources.__setitem__("Healthcare", 2), +1),
    (lambda p: p._add_money(-50), -1),
])
def test_reward_moves_in_the_right_direction(gs, wc, change, direction):
    chain = [entry_for(gs, wc)]
    change(wc)
    score(chain, gs, wc)
    assert chain[-1].reward * direction > 0


def test_scoring_returns_the_same_chain(gs, wc):
    chain = [entry_for(gs, wc)]
    assert score(chain, gs, wc) is chain


# =============================================================================
# 3. Saving to disk
# training/data/decisions.jsonl: one JSON object per line, appended - a second
# game must never overwrite the first.
# =============================================================================

DECISIONS = os.path.join("training", "data", "decisions.jsonl")


def save(chain):
    from training.postprocessing import save_decision_log
    save_decision_log(chain)


def test_saving_writes_one_line_per_decision(workdir, gs, wc):
    save([entry_for(gs, wc), entry_for(gs, wc, "TestAction2")])
    rows = b.read_jsonl(DECISIONS)
    assert len(rows) == 2
    assert [r["response"]["answer"]["action"] for r in rows] == ["TestAction1", "TestAction2"]


def test_saving_appends_rather_than_overwrites(workdir, gs, wc):
    save([entry_for(gs, wc)])
    save([entry_for(gs, wc), entry_for(gs, wc)])
    assert len(b.read_jsonl(DECISIONS)) == 3


def test_every_saved_line_has_call_response_and_reward(workdir, gs, wc):
    save([entry_for(gs, wc)])
    row = b.read_jsonl(DECISIONS)[0]
    assert {"call", "response", "reward"} <= set(row)


def test_saved_reward_matches_the_scored_reward(workdir, gs, wc):
    chain = [entry_for(gs, wc)]
    wc._add_money(50)
    score(chain, gs, wc)
    save(chain)
    assert b.read_jsonl(DECISIONS)[0]["reward"] == chain[-1].reward


# =============================================================================
# 4. Game IDs
# Format: <expansion letter>_<player count>_<iterator>, e.g. "G_2_0".
#   G = base game, H = Historical Events, C = Crisis & Control, B = both.
# The iterator counts previous games with the same expansion + player count.
# =============================================================================

def make_config(player_count=2, historical=0, crisis=0):
    from game.assets.classes import Config
    agents = {f: "Random" for f in ["Working Class", "Capitalists", "Middle Class", "State"][:player_count]}
    return Config({"player_count": player_count, "agents": agents,
                   "expansions": {"historical_events": historical, "crisis_and_control": crisis}})


@pytest.mark.parametrize("historical, crisis, letter", [
    (0, 0, "G"), (1, 0, "H"), (0, 1, "C"), (1, 1, "B"),
])
def test_game_id_expansion_letter(workdir, historical, crisis, letter):
    assert make_config(historical=historical, crisis=crisis).game_id.game_id == f"{letter}_2_0"


def test_first_game_id_starts_at_zero(workdir):
    assert make_config(player_count=3).game_id.game_id == "G_3_0"


def test_saving_a_game_id_increments_the_next_one(workdir):
    make_config().game_id.save()
    assert make_config().game_id.game_id == "G_2_1"


def test_iterator_is_counted_per_player_count(workdir):
    make_config(player_count=2).game_id.save()
    assert make_config(player_count=3).game_id.game_id == "G_3_0"


def test_creating_a_config_does_not_save_an_id(workdir):
    # The ID should only be recorded once the game has actually been played.
    make_config()
    make_config()
    assert not os.path.exists(os.path.join("training", "game_ids.csv"))


@pytest.mark.parametrize("bad", [
    {"player_count": "2", "agents": {}, "expansions": {}},
    {"player_count": 2, "agents": [], "expansions": {}},
    {"player_count": 2, "agents": {}, "expansions": []},
])
def test_config_rejects_wrong_types(bad):
    from game.assets.classes import Config
    with pytest.raises(Exception):
        Config(bad)
