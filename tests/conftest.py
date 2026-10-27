"""
# tests/conftest.py

    pytest loads this file automatically. Every @pytest.fixture here can be used by
    any test just by naming it as a parameter - never import or call them directly.

    Fixture chain (each one is built from the one before it, once per test):

        seed ──> (random module seeded)
        player_count ──> gs ──> wc / mc / cap / state
                          └──> started_gs  (agents attached + rulebook setup run)

    Override a root fixture with parametrize and everything downstream follows:

        @pytest.mark.parametrize("player_count", [3])
        def test_x(gs, mc): ...      # gs is a 3-player board, mc is ITS Middle Class

## Hierarchy
    This file can see builders.py and all game files, and sits below test_*.py files.
"""
import logging
import os
import random
import sys

import pytest

# Make `import game...` work no matter how pytest is launched (plain `pytest`,
# `python -m pytest`, or from VS Code), by putting the repo root on the path.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import builders as b  # noqa: E402  (must come after the sys.path fix)


# =============================================================================
# pytest configuration
# =============================================================================

def pytest_configure(config):
    """Registers custom markers so pytest doesn't warn about them."""
    config.addinivalue_line("markers", "slow: plays whole games; skip with -m 'not slow'")


@pytest.fixture(autouse=True)
def quiet_logs():
    """Runs for every test: silences the game's logging so test output stays readable."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def seed():
    """Default random seed. Override with @pytest.mark.parametrize("seed", [...])."""
    return 0


@pytest.fixture(autouse=True)
def seeded_random(seed):
    """Runs for every test: seeds Python's global random, so shuffles are repeatable."""
    random.seed(seed)


# =============================================================================
# Boards
# =============================================================================

@pytest.fixture
def player_count():
    """Default board size. Override with @pytest.mark.parametrize("player_count", [...])."""
    return 2


@pytest.fixture
def gs(player_count):
    """A fresh, empty board (no companies founded, no workers placed)."""
    return b.make_gamestate(player_count)


@pytest.fixture
def started_gs(gs):
    """
    A board after the rulebook's Game Setup has been run by Engine.start_position.
    Random agents are attached because setup can ask a player to make a choice
    (the Middle Class picks its first skilled worker).
    """
    from game.engine import Engine
    b.attach_agents(gs)
    Engine.start_position(gs)
    return gs


# =============================================================================
# Players - always taken FROM the board, so they can never belong to another game
# =============================================================================

@pytest.fixture
def wc(gs):
    return gs.players["Working Class"]


@pytest.fixture
def mc(gs):
    return gs.players["Middle Class"]   # KeyError on a 2-player board, which is correct


@pytest.fixture
def cap(gs):
    return gs.players["Capitalists"]


@pytest.fixture
def state(gs):
    return gs.players["State"]


# =============================================================================
# Files
# =============================================================================

@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """
    Runs the test inside an empty temporary folder laid out like the repo.
    Anything the game saves with a relative path (decisions.jsonl, game_ids.csv)
    lands here instead of polluting your real training data.
    """
    # references.py reads companies.csv relative to the current directory when it is
    # first imported, so make sure that has already happened before we move away.
    import game.assets.references  # noqa: F401

    (tmp_path / "training" / "data").mkdir(parents=True)
    (tmp_path / "logs").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path
