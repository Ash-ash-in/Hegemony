"""
# tests/test_agent_boundary.py

    Sanitation between the engine and the agents.

    The principle (from your refactor plan): "All visualisation comes from what the
    agent receives". An agent must only ever see the ContextCall - a personalised,
    plain-data snapshot - and must hand back plain strings chosen from its options.

    Blocks:
        1. MaskedState: plain data only        (no live objects cross the boundary)
        2. MaskedState: hidden information     (hands and deck orders stay secret)
        3. MaskedState: a true snapshot        (later moves don't rewrite the past)
        4. ContextCall: identity and freshness (who it's for, built from current state)
        5. ContextCall: legal options only     (offered = passes check; Free/Main rule)
        6. Agents: answers and validation      (strings, from the options, right faction)
        7. Agents: isolation                   (no route back into the live game)

## Hierarchy
    This file can see builders.py and all game files.
"""
import copy
from dataclasses import asdict

import pytest

import builders as b
from game.assets.messages import MaskedState

ALL_SIZES = [2, 3, 4]


# =============================================================================
# 1. MaskedState: plain data only
# If a live Worker, Company or CompanySlot object reaches an agent, the agent can
# read things it shouldn't or even change the game - and the decision log can't be
# saved as JSON. Everything inside must be str / int / float / bool / None, in
# dicts (with string keys) and lists.
# =============================================================================

@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_masked_state_contains_only_plain_data(started_gs, wc):
    masked = MaskedState(started_gs, wc)
    problems = b.non_plain_values(b.as_plain_dict(masked))
    assert problems == [], "\n".join(problems[:15])


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_masked_state_lists_every_player(gs, wc):
    masked = MaskedState(gs, wc)
    assert set(masked.PlayerData) == set(gs.players)


def test_masked_state_is_personalised(gs, wc, cap):
    assert MaskedState(gs, wc).Faction["faction"] == "Working Class"
    assert MaskedState(gs, cap).Faction["faction"] == "Capitalists"


# =============================================================================
# 2. MaskedState: hidden information
# Hegemony is mostly open information, except: other players' hands, everyone's
# own draw pile, and the order of every shuffled deck. A unique "secret" value is
# planted in each hidden place, and must not appear anywhere in the snapshot.
# =============================================================================

SECRET = "SECRET-DO-NOT-LEAK"


def test_other_players_hands_are_hidden(gs, wc, cap):
    cap._hand.append(SECRET)
    assert not b.contains(b.as_plain_dict(MaskedState(gs, wc)), SECRET)


def test_own_hand_is_visible(gs, wc):
    wc._hand.append(SECRET)
    assert MaskedState(gs, wc).Faction["hand"] == [SECRET]


@pytest.mark.parametrize("owner", ["Working Class", "Capitalists"])
def test_action_card_draw_piles_are_hidden(gs, wc, owner):
    # Nobody - not even the owner - knows the order of their face-down pile.
    gs.players[owner]._deck.append(SECRET)
    assert not b.contains(b.as_plain_dict(MaskedState(gs, wc)), SECRET)


@pytest.mark.parametrize("deck", [
    "immigration_cards", "export_cards", "business_deal_cards", "political_agenda_cards",
])
def test_shuffled_deck_order_is_hidden(gs, wc, deck):
    getattr(gs, deck).append(SECRET)
    assert not b.contains(b.as_plain_dict(MaskedState(gs, wc)), SECRET)


@pytest.mark.parametrize("faction", ["Capitalists", "State"])
def test_face_down_company_decks_are_hidden(gs, wc, faction):
    gs.company_deck[faction].append(SECRET)
    assert not b.contains(b.as_plain_dict(MaskedState(gs, wc)), SECRET)


# =============================================================================
# 3. MaskedState: a true snapshot
# The snapshot is what the agent saw when it decided. If it holds references to
# the live board, it silently changes as the game moves on - and the training
# data records a world the agent never saw.
# =============================================================================

def test_snapshot_ignores_later_worker_changes(gs, wc):
    masked = MaskedState(gs, wc)
    before = copy.deepcopy(b.as_plain_dict(masked)["BoardData"]["unemployed_workers"])
    b.spawn_unemployed(gs, "Working Class", "Agriculture")
    assert b.as_plain_dict(masked)["BoardData"]["unemployed_workers"] == before


def test_snapshot_ignores_later_company_changes(gs, wc):
    masked = MaskedState(gs, wc)
    before = copy.deepcopy(b.as_plain_dict(masked)["BoardData"]["companies"])
    b.found_company(gs, "Capitalists", "Supermarket")
    assert b.as_plain_dict(masked)["BoardData"]["companies"] == before


def test_snapshot_ignores_later_resource_changes(gs, wc):
    masked = MaskedState(gs, wc)
    wc.resources["Food"] += 5
    assert masked.PlayerData["Working Class"]["resources"]["Food"] == 0


# =============================================================================
# 4. ContextCall: identity and freshness
# =============================================================================

@pytest.fixture
def scripted(wc):
    return b.ScriptedAgent("Working Class")


@pytest.fixture
def action_context(gs, wc, scripted):
    from game.context import ActionContext
    return ActionContext(gs, wc, scripted)


def test_call_is_addressed_to_the_acting_player(gs, wc, scripted, action_context):
    call = action_context.build_call(gs, wc)
    assert call.faction == "Working Class"
    assert call.agent_type == scripted.name
    assert call.game_id == gs.game_id
    assert call.decision_type == "choose_action"


def test_each_context_gets_a_unique_sequence_number(gs, wc, scripted):
    from game.context import ActionContext
    first, second = ActionContext(gs, wc, scripted), ActionContext(gs, wc, scripted)
    assert first.seq != second.seq


def test_top_level_context_is_its_own_parent(action_context):
    assert action_context.parent_seq == action_context.seq


def test_each_call_is_built_from_the_current_state(gs, wc, action_context):
    # The second step of a turn must see the effects of the first step.
    first = action_context.build_call(gs, wc)
    wc._add_money(30)
    action_context.update_decision_in_progress({"1": "None"})
    action_context.next_step()
    second = action_context.build_call(gs, wc)
    assert first.gamestate.PlayerData["Working Class"]["money"] == 0
    assert second.gamestate.PlayerData["Working Class"]["money"] == 30


def test_whole_call_is_plain_data(started_gs, wc, scripted):
    from game.context import ActionContext
    call = ActionContext(started_gs, wc, scripted).build_call(started_gs, wc)
    problems = b.non_plain_values(asdict(call))
    assert problems == [], "\n".join(problems[:15])


# =============================================================================
# 5. ContextCall: legal options only
# Rulebook p11: on your turn you take one Main Action, and may take one Free Action
# "either before or after" it. Every option offered must pass its rule check, and
# nothing that fails its check may be offered.
# =============================================================================

def offered(call) -> list[str]:
    return call.available_choices["action"]


def test_every_offered_action_passes_its_check(gs, wc, action_context):
    import game.rules as rules
    call = action_context.build_call(gs, wc)
    for name in offered(call):
        if name == "None":
            continue
        action = getattr(rules.FreeAction, name, None) or getattr(rules.MainAction, name)
        assert action.check(gs, wc).validity, f"{name} offered but its check fails"


def test_failing_action_is_not_offered(gs, wc, action_context):
    # No loans -> Pay Off Loan is not a legal Free Action.
    assert wc.loans == 0
    assert "RepayLoan" not in offered(action_context.build_call(gs, wc))


def test_passing_action_is_offered(gs, wc, action_context):
    wc._loans, wc._money = 1, 60
    assert "RepayLoan" in offered(action_context.build_call(gs, wc))


def test_options_are_plain_strings(gs, wc, action_context):
    call = action_context.build_call(gs, wc)
    for options in call.available_choices.values():
        assert all(isinstance(option, str) for option in options)


def test_after_a_free_action_only_main_actions_remain(gs, wc, action_context):
    import game.rules as rules
    wc._loans, wc._money = 1, 60
    action_context.build_call(gs, wc)
    action_context.update_decision_in_progress({"1": "RepayLoan"})
    action_context.next_step()
    step_two = offered(action_context.build_call(gs, wc))
    assert "RepayLoan" not in step_two and "None" not in step_two
    assert all(hasattr(rules.MainAction, name) for name in step_two)


def test_after_a_main_action_only_free_actions_or_none_remain(gs, wc, action_context):
    import game.rules as rules
    wc._loans, wc._money = 1, 60
    action_context.build_call(gs, wc)
    action_context.update_decision_in_progress({"1": "TestAction1"})
    action_context.next_step()
    step_two = offered(action_context.build_call(gs, wc))
    assert "None" in step_two                         # the free action is optional
    assert all(name == "None" or hasattr(rules.FreeAction, name) for name in step_two)


# =============================================================================
# 6. Agents: answers and validation
# AgentAnswer rule (messages.py): values must be strings, so the NN can read them,
# and each must be one of the options the agent was offered.
# =============================================================================

@pytest.fixture
def random_agent(gs):
    return b.attach_agents(gs, "Random")["Working Class"]


def test_agent_answers_every_requested_choice_from_its_options(gs, wc, random_agent):
    choices = {"action": ["TestAction1", "TestAction2"], "worker_skill": ["Media", "Unskilled"]}
    answer = random_agent.call(b.make_call(gs, wc, choices))
    assert set(answer.answer) == set(choices)
    for key, value in answer.answer.items():
        assert isinstance(value, str)
        assert value in choices[key]


def test_agent_rejects_a_call_meant_for_another_faction(gs, cap, random_agent):
    with pytest.raises(Exception):
        random_agent.call(b.make_call(gs, cap))


def test_agent_rejects_a_call_with_nothing_to_decide(gs, wc, random_agent):
    with pytest.raises(Exception):
        random_agent.call(b.make_call(gs, wc, {"action": []}))


# =============================================================================
# 7. Agents: isolation
# An agent that holds a live Player or GameState can read unmasked information or
# change the game directly, bypassing every check. This encodes the design point
# we discussed: agents should know their faction, not hold the player object.
# DELETE THIS BLOCK if you decide to keep agents attached to players.
# =============================================================================

def test_agents_hold_no_live_game_objects(gs):
    from game.states import GameState, Player
    for faction, agent in b.attach_agents(gs, "Random").items():
        for attr, value in vars(agent).items():
            assert not isinstance(value, (GameState, Player)), \
                f"{faction} agent holds a live {type(value).__name__} in .{attr}"


def test_players_hold_no_agents(gs):
    # The reverse link: a Player carrying its agent drags the agent (and, one day,
    # NN weights) into every deepcopy/undo snapshot of the game state.
    b.attach_agents(gs, "Random")
    for faction, player in gs.players.items():
        assert not hasattr(player, "agent"), f"{faction} player holds its agent"
