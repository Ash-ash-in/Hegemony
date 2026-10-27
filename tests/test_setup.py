"""
# tests/test_setup.py

    Does a new game start exactly as the rulebook's Game Setup (pages 8-10) says?

    Blocks:
        1. Roles per player count          (engine.setup_players / setup_gamestate)
        2. Components on an empty board    (GameState.__init__)
        3. Starting companies              (Engine.start_position)
        4. Starting workers                (Engine.start_position)
        5. Starting resources & cards      (mostly not implemented yet - marked xfail)
        6. Engine startup & agent wiring   (Engine.engine_startup / setup_agents)

    Tests marked @not_implemented(...) are the rulebook backlog: they are EXPECTED
    to fail until the feature exists. See builders.not_implemented for details.

## Hierarchy
    This file can see builders.py and all game files.
"""
import pytest

import builders as b
from builders import not_implemented

ALL_SIZES = [2, 3, 4]


# =============================================================================
# 1. Roles per player count
# Rulebook p8: 2 players = Capitalists + Working Class; 3 adds the Middle Class;
# 4 adds the State. Below 4 players the State still exists on the board as a
# non-player (NPC) - it owns the public companies and the treasury.
# =============================================================================

@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_working_class_exists_at_every_size(gs, wc):
    assert wc.faction == "Working Class"


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_capitalists_exist_at_every_size(gs, cap):
    assert cap.faction == "Capitalists"


@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_exists_at_three_plus(gs, mc):
    assert mc.faction == "Middle Class"


def test_no_middle_class_in_two_player_game(gs):
    assert "Middle Class" not in gs.players


@pytest.mark.parametrize("player_count", [2, 3])
def test_state_is_npc_below_four_players(gs, state):
    from game.states import NPCState, PlayerState
    assert isinstance(state, NPCState)
    assert not isinstance(state, PlayerState)


@pytest.mark.parametrize("player_count", [4])
def test_state_is_a_player_at_four(gs, state):
    from game.states import PlayerState
    assert isinstance(state, PlayerState)


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_players_are_stored_in_turn_order(gs):
    # Rulebook p11: turn order is always Working Class, Middle Class, Capitalists,
    # State. Keeping the dict in this order also keeps the NN's input layout stable.
    turn_order = ["Working Class", "Middle Class", "Capitalists", "State"]
    expected = [f for f in turn_order if f in gs.players]
    assert list(gs.players) == expected


@pytest.mark.parametrize("bad_count", [0, 1, 5])
def test_invalid_player_counts_are_rejected(bad_count):
    with pytest.raises(Exception):
        b.make_gamestate(bad_count)


# =============================================================================
# 2. Components on an empty board
# Rulebook p3 component list and p8 Main Board Setup.
# =============================================================================

def test_worker_supply_matches_component_list(gs):
    # p3: 48 Working Class Workers, 42 Middle Class Workers
    assert len(gs.worker_pool["Working Class"]) == 48
    assert len(gs.worker_pool["Middle Class"]) == 42


def test_immigration_deck_has_25_cards(gs):
    assert len(gs.immigration_cards) == 25            # p3


def test_business_deal_deck_has_20_cards(gs):
    assert len(gs.business_deal_cards) == 20          # p3


def test_one_export_card_is_face_up(gs):
    # p8: "Draw the top card and place it face-up on its corresponding space."
    assert gs.active_export_card is not None
    assert gs.active_export_card in gs.export_cards


def test_one_business_deal_is_face_up(gs):
    # p8: "Draw the top card and place it face up on one of the corresponding spaces."
    assert len(gs.active_business_deals) == 1


def test_each_industry_has_one_empty_union(gs):
    assert set(gs.unions) == {"Agriculture", "Luxury", "Healthcare", "Education", "Media"}
    assert all(union.occupant is None for union in gs.unions.values())


def test_unemployment_area_starts_empty(gs):
    assert gs.unemployed_workers == {"Working Class": [], "Middle Class": []}


def test_each_voting_colour_totals_25_cubes(gs):
    # p3: 75 voting cubes in 3 colours. Cubes in the supply + cubes in the bag
    # must always add up to 25 per colour, wherever they are.
    for faction in ("Working Class", "Middle Class", "Capitalists"):
        in_bag = gs.voting_bag.get(faction, 0)
        assert gs.election_cubes[faction] + in_bag == 25, faction


@not_implemented("8 cubes of each colour start in the voting bag")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_voting_bag_starts_with_eight_of_each_colour(gs):
    # p8: "Take 8 cubes of each color and place them in the cloth bag ... Add cubes
    # of all 3 colors, even in 2-player games where the Middle Class is not playing."
    bag = {f: n for f, n in gs.voting_bag.items() if n}
    assert bag == {"Working Class": 8, "Middle Class": 8, "Capitalists": 8}


@not_implemented("tax multiplier")
def test_tax_multiplier_starts_at_five(gs):
    assert getattr(gs, "tax_multiplier", None) == 5   # p8


@not_implemented("public services area")
@pytest.mark.parametrize("player_count, health, education, influence", [
    (2, 5, 5, 3), (3, 6, 6, 4), (4, 6, 6, 4),
])
def test_public_services_start_stocked(gs, health, education, influence):
    # p8 table: Health / Education / Influence placed in the Public Services area.
    services = getattr(gs, "public_services", None) or {}
    assert services.get("Healthcare") == health
    assert services.get("Education") == education
    assert services.get("Influence") == influence


# =============================================================================
# 3. Starting companies (after Engine.start_position)
# Rulebook p8: Capitalists start with Supermarket, Shopping Mall, College, Clinic.
# Middle Class (3-4p) start with Convenience Store and Doctor's Office.
# 3 starting Public Companies depend on player count (p10 worker setup names them).
# =============================================================================

def founded_names(gamestate, faction: str) -> list[str]:
    return sorted(s.company.name for s in gamestate.companies[faction] if s.company is not None)


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_capitalists_start_with_their_four_companies(started_gs):
    assert founded_names(started_gs, "Capitalists") == ["Clinic", "College", "Shopping Mall", "Supermarket"]


@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_start_with_their_two_companies(started_gs):
    assert founded_names(started_gs, "Middle Class") == ["Convenience Store", "Doctor's Office"]


def test_middle_class_has_no_companies_in_two_player_game(started_gs):
    assert founded_names(started_gs, "Middle Class") == []


@pytest.mark.parametrize("player_count, must_include", [
    (2, {"Public Hospital", "Public University"}),
    (3, {"University Hospital", "Technical University"}),
    (4, {"University Hospital", "Technical University"}),
])
def test_correct_public_companies_for_player_count(started_gs, must_include):
    names = founded_names(started_gs, "State")
    assert len(names) == 3
    assert must_include <= set(names)


@not_implemented("inactive (face-down) public companies on the board")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_all_nine_public_companies_are_on_the_board(started_gs):
    # p8: 3 starting Public Companies in row 1, then 3 face-down in row 2 and the
    # remaining 3 in row 3 - nine cards on the board, three of them active.
    assert len(founded_names(started_gs, "State")) == 9


@not_implemented("starting wage level L2")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_starting_companies_pay_level_two_wages(started_gs):
    # p8: "Place a marker on the L2 Wage spot on each card" (all starting companies).
    for slots in started_gs.companies.values():
        for slot in slots:
            if slot.company is not None and slot.company.wages:
                assert slot.wage == 2, slot.company.name


# =============================================================================
# 4. Starting workers (after Engine.start_position)
# Rulebook p10 lists exactly which meeples go on which company.
# Colours: green=Agriculture, blue=Luxury, white=Healthcare, orange=Education,
# gray=Unskilled.
# =============================================================================

WC, MC = "Working Class", "Middle Class"

STARTING_WORKERS = {
    2: {
        "Supermarket":       [(WC, "Agriculture"), (WC, "Unskilled")],
        "Shopping Mall":     [(WC, "Luxury"), (WC, "Unskilled")],
        "Public Hospital":   [(WC, "Healthcare"), (WC, "Unskilled")],
        "Public University": [(WC, "Education"), (WC, "Unskilled")],
        "College":           [],
        "Clinic":            [],
    },
    3: {
        "Supermarket":          [(WC, "Agriculture"), (WC, "Unskilled")],
        "College":              [(WC, "Education"), (WC, "Unskilled")],
        "University Hospital":  [(WC, "Healthcare"), (WC, "Unskilled"), (WC, "Unskilled")],
        "Technical University": [(MC, "Education"), (MC, "Unskilled"), (MC, "Unskilled")],
        "Shopping Mall":        [(MC, "Luxury"), (MC, "Unskilled")],
        "Convenience Store":    [(MC, "Agriculture")],
        "Doctor's Office":      [(MC, "Healthcare")],
        "Clinic":               [],
    },
}
STARTING_WORKERS[4] = STARTING_WORKERS[3]


@pytest.mark.parametrize("player_count, company", [
    (n, company) for n in ALL_SIZES for company in STARTING_WORKERS[n]
])
def test_starting_company_is_staffed_per_rulebook(started_gs, player_count, company):
    slot = b.find_slot(started_gs, company)
    assert slot is not None, f"{company} was not founded"
    assert b.worker_summary(slot) == sorted(STARTING_WORKERS[player_count][company])


@pytest.mark.parametrize("player_count, expected", [(2, 2), (3, 3), (4, 3)])
def test_working_class_starting_unemployed_workers(started_gs, expected):
    # p10: 1 unskilled Worker, plus 1 Immigration card (2p) or 2 cards (3-4p).
    unemployed = started_gs.unemployed_workers["Working Class"]
    assert len(unemployed) == expected
    assert "Unskilled" in [w.skill for w in unemployed]


@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_starting_unemployed_workers(started_gs):
    # p10: 1 skilled Worker of their choice, plus 2 Immigration cards.
    unemployed = started_gs.unemployed_workers["Middle Class"]
    assert len(unemployed) == 3
    assert any(w.skill != "Unskilled" for w in unemployed)


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_working_class_population_track_starts_at_ten(started_gs):
    # p10: "Place a marker on the Population track, at the indicated starting space
    # (10 Workers)." The workers placed above must add up to exactly that.
    assert started_gs.players["Working Class"].population_track == 10


@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_population_track_starts_at_ten(started_gs):
    assert started_gs.players["Middle Class"].population_track == 10


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_worker_count_reconciles_after_setup(started_gs):
    assert started_gs.corroborate_worker_count()


@pytest.mark.parametrize("player_count, cards_drawn", [(2, 1), (3, 4), (4, 4)])
def test_setup_immigration_cards_go_to_the_bottom(gs, player_count, cards_drawn):
    # p10: drawn cards are returned "to the bottom of the Immigration deck".
    # 2p: Working Class draws 1. 3-4p: Working Class draws 2, Middle Class draws 2.
    from game.engine import Engine
    original_order = list(gs.immigration_cards)
    b.attach_agents(gs)
    Engine.start_position(gs)
    expected = original_order[cards_drawn:] + original_order[:cards_drawn]
    assert gs.immigration_cards == expected


# =============================================================================
# 5. Starting resources and cards
# Rulebook p10 player setups. Almost none of this exists yet: the engine
# currently gives everyone a temporary 120.
# =============================================================================

@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_everyone_starts_on_zero_victory_points(started_gs):
    # p8: "Place each player's scoring marker on the 0 space"
    assert all(p.victory_points == 0 for p in started_gs.players.values())


@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_nobody_starts_with_a_loan(started_gs):
    assert all(p.loans == 0 for p in started_gs.players.values())


@not_implemented("rulebook starting money (engine gives a temporary 120)")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_starting_money(started_gs):
    # p10: WC 30; MC 40; Capitalists 120 in Revenue; p8: State Treasury 120.
    expected = {"Working Class": 30, "Middle Class": 40, "Capitalists": 120, "State": 120}
    for faction, player in started_gs.players.items():
        assert player.money == expected[faction], faction


@not_implemented("rulebook starting money (engine gives a temporary 120)")
def test_capitalist_starting_money_is_revenue_not_capital(started_gs, cap):
    assert (cap.revenue, cap.capital) == (120, 0)


@not_implemented("starting influence")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_every_class_starts_with_one_influence(started_gs):
    # p10: WC, MC and Capitalists each get 1 Influence. (The NPC State has none.)
    for faction in ("Working Class", "Middle Class", "Capitalists"):
        if faction in started_gs.players:
            assert started_gs.players[faction]._influence == 1, faction


@not_implemented("starting influence")
@pytest.mark.parametrize("player_count", [4])
def test_player_state_starts_with_one_influence(started_gs, state):
    assert state.influence == 1                       # p10 State Setup


@not_implemented("starting goods")
def test_capitalists_start_with_goods(started_gs, cap):
    # p10: "1 Food, 2 Luxury, 2 Education and 1 Influence ... in the corresponding
    # Storages". Assumes produced/owned goods live in `resources`.
    assert cap.resources["Food"] == 1
    assert cap.resources["Luxuries"] == 2
    assert cap.resources["Education"] == 2


@not_implemented("starting goods")
@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_start_with_goods(started_gs, mc):
    # p10: "Get 1 Food and 1 Health and place them in the corresponding Storages"
    assert mc.resources["Food"] == 1
    assert mc.resources["Healthcare"] == 1


@not_implemented("company markets")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_capitalists_reveal_four_companies_to_their_market(started_gs):
    # p10: "reveal the first 4 Companies ... These will be your Market"
    assert len(started_gs.players["Capitalists"].market) == 4


@not_implemented("company markets")
@pytest.mark.parametrize("player_count", [3, 4])
def test_middle_class_reveal_three_companies_to_their_market(started_gs):
    assert len(started_gs.players["Middle Class"].market) == 3     # p10


@not_implemented("action cards")
@pytest.mark.parametrize("player_count", ALL_SIZES)
def test_every_player_draws_seven_action_cards(started_gs):
    # p10: each role "Draw 7 of those cards to your hand" (State only in 4p).
    for faction, player in started_gs.players.items():
        if faction == "State" and started_gs.player_count < 4:
            continue
        assert len(player.hand) == 7, faction


# =============================================================================
# 6. Engine startup and agent wiring
# =============================================================================

def make_config(player_count=2, agents=None):
    from game.assets.classes import Config
    agents = agents or {"Working Class": "Random", "Capitalists": "Random"}
    return Config({"player_count": player_count, "agents": agents,
                   "expansions": {"historical_events": 0, "crisis_and_control": 0}})


def test_engine_startup_builds_a_board_from_config(workdir):
    from game.engine import Engine
    engine = Engine()
    gamestate = engine.engine_startup(make_config())
    assert list(gamestate.players) == ["Working Class", "Capitalists", "State"]
    assert gamestate.player_count == 2


def test_engine_startup_creates_one_agent_per_configured_faction(workdir):
    from game.engine import Engine
    engine = Engine()
    engine.engine_startup(make_config())
    assert set(engine.agents) == {"Working Class", "Capitalists"}


def test_engine_rejects_agent_count_that_doesnt_match_players(workdir):
    from game.engine import Engine
    config = make_config(player_count=3)              # 3 players but only 2 agents
    with pytest.raises(Exception):
        Engine().engine_startup(config)


def test_unknown_agent_type_is_rejected(gs):
    from game import engine
    with pytest.raises(Exception):
        engine.setup_agents({"Working Class": "Telepathic"}, gs)


def test_unknown_faction_is_rejected(gs):
    from game import engine
    with pytest.raises(Exception):
        engine.setup_agents({"Aristocrats": "Random"}, gs)
