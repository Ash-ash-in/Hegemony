"""
# tests/builders.py

    Plain helper functions and classes shared by the tests and by conftest.py.
    pytest knows nothing about this file - it is imported like any other module.

    Rule of thumb:
        - "Give every test a fresh X"           -> fixture in conftest.py
        - "Do something with arguments to a board" -> function in here

## Hierarchy
    This file can see all game files and sits below all other files in /tests/

## Note on imports
    Game modules are imported INSIDE the functions that need them, not at the top.
    During a refactor one broken module (e.g. game.context) would otherwise stop
    every single test from loading. Imported lazily, only the tests that actually
    need the broken module fail - and they fail with a clear message.
"""
import json
import pytest


# =============================================================================
# Markers
# =============================================================================

def not_implemented(feature: str):
    """
    Marks a test for a rulebook feature the game doesn't attempt yet.

    The test is reported as 'xfail' (expected failure) instead of 'failed', so the
    red failures in a test run are always real bugs in code that exists.

    strict=True means: the moment you implement the feature and the test starts
    passing, pytest reports it as a FAILURE ("XPASS(strict)"). That's your prompt
    to delete this marker so the test becomes a normal, enforced test.

    raises=AssertionError means only a failed `assert` counts as "expected". If the
    test crashes for another reason (NameError, TypeError...) that's a real bug and
    it is reported as a normal failure rather than hidden in the backlog. Tests
    using this marker read attributes with getattr(..., None) for that reason.
    """
    return pytest.mark.xfail(strict=True, raises=AssertionError,
                             reason=f"Not implemented yet: {feature}")


# =============================================================================
# Board builders - all of these use the game's own setup code
# =============================================================================

def make_gamestate(player_count: int = 2, game_id: str = "TEST"):
    """A fresh, empty board, built by the engine's real setup function."""
    from game import engine
    return engine.setup_gamestate(player_count, game_id)


def attach_agents(gamestate, agent_name: str = "Random") -> dict:
    """Attaches one agent per faction using the engine's real setup_agents()."""
    from game import engine
    factions = {faction: agent_name for faction in gamestate.players}
    return engine.setup_agents(factions, gamestate)


def take_company(gamestate, faction: str, name: str):
    """Pulls a named company out of a faction's deck and puts it in their market."""
    company = next(c for c in gamestate.company_deck[faction] if c.name == name)
    gamestate.company_deck[faction].remove(company)
    gamestate.players[faction]._add_company_to_market(company)
    return company


def found_company(gamestate, faction: str, name: str):
    """Puts a named company on the board via the real rule. Returns its CompanySlot."""
    import game.rules as rules
    company = take_company(gamestate, faction, name)
    rules._CompanyFound.resolve(gamestate.players[faction], gamestate, company)
    return next(slot for slot in gamestate.companies[faction] if slot.company is company)


def spawn_unemployed(gamestate, faction: str, skill: str):
    """Spawns a worker into the unemployment area via the real rule. Returns the worker."""
    import game.rules as rules
    rules._WorkerSpawn.resolve(gamestate, gamestate.players[faction], skill)
    return gamestate.unemployed_workers[faction][-1]


def find_slot(gamestate, company_name: str):
    """Finds the CompanySlot holding a company with this name, on any faction's board."""
    for slots in gamestate.companies.values():
        for slot in slots:
            if slot.company is not None and slot.company.name == company_name:
                return slot
    return None


# =============================================================================
# Agents
# =============================================================================

class ScriptedAgent:
    """
    A stand-in agent for tests: answers from a pre-written script, and records every
    call it receives so the test can inspect exactly what the agent was shown.

    script: a list of answer dicts, used in order. When the script runs out it
            falls back to the first option of every choice (so long games don't crash).
    """
    name = "Scripted"

    def __init__(self, faction: str, script: list | None = None):
        self.faction = faction
        self.script = list(script or [])
        self.calls = []

    def call(self, call):
        from game.assets.messages import AgentAnswer
        self.calls.append(call)
        if self.script:
            return AgentAnswer(self.script.pop(0))
        return AgentAnswer({key: options[0] for key, options in call.available_choices.items()})


def make_call(gamestate, player, choices: dict | None = None, seq: int = 0,
              decision_type: str = "choose_action", agent_type: str = "Scripted"):
    """
    Builds a ContextCall by hand from messages.py, without going through context.py.
    Lets the logging/data tests run even while the context layer is being refactored.
    """
    from game.assets.messages import ContextCall, MaskedState
    return ContextCall(
        gamestate=MaskedState(gamestate, player),
        seq=seq, game_id=gamestate.game_id, parent_seq=seq,
        faction=player.faction, agent_type=agent_type,
        decision_in_progress={}, decision_type=decision_type,
        step=(1, 1), parent_name="",
        available_choices=choices or {"action": ["TestAction1", "TestAction2"]},
    )


# =============================================================================
# Inspection helpers
# =============================================================================

def contains(obj, target, _seen=None) -> bool:
    """
    True if `target` appears anywhere inside `obj` - through dicts, lists, tuples,
    and the attributes of any objects along the way.

    Used for hidden-information tests: plant a unique secret value in the real game
    (e.g. in another player's hand) and prove it never reaches the agent.
    """
    _seen = _seen if _seen is not None else set()
    if obj is target or (isinstance(obj, str) and obj == target):
        return True
    if id(obj) in _seen or isinstance(obj, JSON_LEAF_TYPES):
        return False
    _seen.add(id(obj))
    if isinstance(obj, dict):
        return any(contains(k, target, _seen) or contains(v, target, _seen) for k, v in obj.items())
    if isinstance(obj, (list, tuple, set)):
        return any(contains(v, target, _seen) for v in obj)
    if hasattr(obj, "__dict__"):
        return contains(vars(obj), target, _seen)
    return False


def as_plain_dict(masked_state) -> dict:
    """The four sections of a MaskedState as one dict (works with or without @dataclass)."""
    return {name: getattr(masked_state, name)
            for name in ("GameMetaData", "BoardData", "PlayerData", "Faction")}

JSON_LEAF_TYPES = (str, int, float, bool, type(None))


def non_plain_values(obj, path: str = "root") -> list[str]:
    """
    Walks a nested structure and lists anything that isn't plain JSON-style data.
    Returns a list of human-readable problems (empty list = clean).

    Used to prove that what crosses the engine -> agent boundary is pure data,
    with no live game objects an agent could read from or mutate.
    """
    problems = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                problems.append(f"{path}: non-string key {key!r}")
            problems += non_plain_values(value, f"{path}[{key!r}]")
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            problems += non_plain_values(value, f"{path}[{i}]")
    elif not isinstance(obj, JSON_LEAF_TYPES):
        problems.append(f"{path}: {type(obj).__name__} object")
    return problems


def read_jsonl(path) -> list[dict]:
    """Reads a .jsonl file into a list of dicts, skipping blank lines."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def worker_summary(slot) -> list[tuple[str, str]]:
    """[(faction, skill), ...] for the workers in a slot, sorted - easy to compare."""
    return sorted((w.faction, w.skill) for w in slot.workers if w is not None)
