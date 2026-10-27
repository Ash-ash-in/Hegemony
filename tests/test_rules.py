"""
# tests/test_rules.py

    Tests for game/rules.py - every check() and resolve() pair.

    Two kinds of test per rule:
        - check() tests:   "is this move legal?"   -> assert validity True/False
        - resolve() tests: "did the move do exactly what the rulebook says?"

    Boards are arranged directly with builders (found a company, spawn a worker)
    rather than by playing turns - every test here runs in milliseconds.

## Hierarchy
    This file can see builders.py and all game files.
"""
import pytest

import builders as b
import game.rules as rules


# =============================================================================
# _MoneyTransfer - check()
# Basic sanity: no paying yourself, no bank-to-bank, only positive amounts.
# Rulebook p33: optional costs can't be paid with money you don't have.
# =============================================================================

@pytest.mark.parametrize("sender, receiver, amount, why", [
    ("wc", "wc", 10, "cannot pay yourself"),
    (None, None, 10, "bank cannot pay the bank"),
    ("wc", None, 0, "amount must be positive"),
    ("wc", None, -5, "amount must be positive"),
])
def test_transfer_rejects_nonsense(wc, sender, receiver, amount, why):
    lookup = {"wc": wc, None: None}
    check = rules._MoneyTransfer.check(lookup[sender], lookup[receiver], amount, mandatory=False)
    assert check.validity is False, why


def test_optional_transfer_blocked_when_unaffordable(wc):
    # "Taking [a Loan] to increase your money so that you can spend it on something
    #  optional ... is not allowed."
    assert rules._MoneyTransfer.check(wc, None, 10, mandatory=False).validity is False


def test_optional_transfer_allowed_when_affordable(wc):
    wc._add_money(10)
    assert rules._MoneyTransfer.check(wc, None, 10, mandatory=False).validity is True


def test_mandatory_transfer_always_allowed(wc):
    # Mandatory costs are always paid - with Loans if necessary.
    assert rules._MoneyTransfer.check(wc, None, 500, mandatory=True).validity is True


# =============================================================================
# _MoneyTransfer - resolve()
# =============================================================================

def test_bank_payment_adds_money(wc):
    rules._MoneyTransfer.resolve(None, wc, 30, mandatory=False)
    assert wc.money == 30


def test_player_to_player_payment_conserves_money(gs, wc, cap):
    wc._add_money(50)
    total_before = wc.money + cap.money
    rules._MoneyTransfer.resolve(wc, cap, 20, mandatory=False)
    assert (wc.money, cap.money) == (30, 20)
    assert wc.money + cap.money == total_before


def test_payment_to_bank_removes_money(wc):
    wc._add_money(50)
    rules._MoneyTransfer.resolve(wc, None, 20, mandatory=False)
    assert wc.money == 30


@pytest.mark.parametrize("money, cost, loans, money_after", [
    (0, 10, 1, 40),     # short by 10  -> 1 loan:  0 + 50 - 10
    (0, 50, 1, 0),      # short by 50  -> 1 loan:  0 + 50 - 50
    (0, 60, 2, 40),     # short by 60  -> 2 loans: 0 + 100 - 60
    (30, 40, 1, 40),    # short by 10  -> 1 loan:  30 + 50 - 40
])
def test_forced_payment_takes_exactly_enough_loans(wc, money, cost, loans, money_after):
    # Rulebook p33: "if they are unable to pay, they must take a Loan ... and then
    # gain 50". Only as many Loans as needed to cover the cost.
    wc._add_money(money)
    rules._MoneyTransfer.resolve(wc, None, cost, mandatory=True)
    assert wc.loans == loans
    assert wc.money == money_after


def test_capitalist_spends_revenue_before_capital(cap):
    # Rulebook p14 General Note: "When paying for a cost from Revenue, if there is not
    # enough money in it, spend as much as you can and cover the rest from your Capital."
    cap._revenue, cap._capital = 10, 100
    rules._MoneyTransfer.resolve(cap, None, 30, mandatory=False)
    assert (cap.revenue, cap.capital) == (0, 80)


def test_capitalist_forced_loan_goes_to_capital(cap):
    # Rulebook p14: "...you must take a Loan, adding 50 to your Capital"
    rules._MoneyTransfer.resolve(cap, None, 10, mandatory=True)
    assert cap.loans == 1
    assert cap.money == 40
    assert cap.revenue >= 0 and cap.capital >= 0      # no negative piles of money


# =============================================================================
# _LoanRemove and FreeAction.RepayLoan
# Rulebook p17 "Pay Off Loan": spend 50 and discard the Loan.
# =============================================================================

def test_cannot_repay_without_a_loan(wc):
    wc._add_money(100)
    assert rules._LoanRemove.check(wc).validity is False


def test_cannot_repay_without_fifty_money(wc):
    wc._loans, wc._money = 1, 49
    assert rules._LoanRemove.check(wc).validity is False


def test_repaying_costs_fifty_and_removes_the_loan(wc):
    wc._loans, wc._money = 1, 60
    rules._LoanRemove.resolve(wc)
    assert (wc.loans, wc.money) == (0, 10)


def test_repay_loan_free_action_agrees_with_loan_rule(gs, wc):
    # The free action is a thin wrapper - it must give the same answer as the rule.
    wc._loans, wc._money = 1, 60
    assert rules.FreeAction.RepayLoan.check(gs, wc).validity is True
    wc._money = 10
    assert rules.FreeAction.RepayLoan.check(gs, wc).validity is False


def test_capitalist_repays_loan_from_capital(gs, cap):
    # Rulebook p33: when paying a Loan off "it spends money from its Capital".
    cap._loans, cap._capital, cap._revenue = 1, 60, 30
    rules.FreeAction.RepayLoan.resolve(gs, cap)
    assert (cap.loans, cap.capital, cap.revenue) == (0, 10, 30)


# =============================================================================
# _PointAssign
# =============================================================================

def test_points_are_added_to_an_active_player(gs, wc):
    rules._PointAssign.resolve(gs, wc, 4)
    assert wc.victory_points == 4


@pytest.mark.parametrize("player_count", [2, 3])
def test_npc_state_cannot_score_points(gs, state):
    # Below 4 players the State is not a player, so it can't receive VP.
    assert rules._PointAssign.check(gs, state, 4).validity is False


# =============================================================================
# _WorkerSpawn
# Workers move from the supply (worker pool) to the Unemployed Workers area, and the
# Population track moves with them (Rulebook p14: "adjust the marker in your
# Population track ... as many spaces forward as the total number of new Workers").
# =============================================================================

def test_capitalists_have_no_workers_to_spawn(gs, cap):
    assert rules._WorkerSpawn.check(gs, cap, "Unskilled").validity is False


def test_middle_class_cannot_spawn_in_two_player_game(gs):
    from game.states import MiddleClass
    # There is no Middle Class on a 2-player board, so build a stray one to ask with.
    assert rules._WorkerSpawn.check(gs, MiddleClass(), "Unskilled").validity is False


def test_cannot_spawn_a_skill_that_has_run_out(gs, wc):
    gs.worker_pool["Working Class"] = [w for w in gs.worker_pool["Working Class"] if w.skill != "Media"]
    assert rules._WorkerSpawn.check(gs, wc, "Media").validity is False


def test_spawn_moves_one_worker_from_pool_to_unemployed(gs, wc):
    pool_before = len(gs.worker_pool["Working Class"])
    worker = b.spawn_unemployed(gs, "Working Class", "Agriculture")
    assert worker.skill == "Agriculture"
    assert worker not in gs.worker_pool["Working Class"]
    assert len(gs.worker_pool["Working Class"]) == pool_before - 1
    assert gs.unemployed_workers["Working Class"] == [worker]


def test_spawn_moves_the_population_track(gs, wc):
    b.spawn_unemployed(gs, "Working Class", "Unskilled")
    b.spawn_unemployed(gs, "Working Class", "Unskilled")
    assert wc.population_track == 2
    assert gs.corroborate_worker_count()


# =============================================================================
# _CompanyFound
# =============================================================================

def test_cannot_found_a_company_not_in_your_market(gs, cap):
    company = next(c for c in gs.company_deck["Capitalists"] if c.name == "Hotel")
    assert rules._CompanyFound.check(cap, gs, company).validity is False


def test_cannot_found_a_company_when_every_slot_is_full(gs, cap):
    filler = b.take_company(gs, "Capitalists", "Hotel")
    for slot in gs.companies["Capitalists"]:
        slot.company = filler                 # arranged directly: we're testing the check
    new_company = b.take_company(gs, "Capitalists", "Stadium")
    check = rules._CompanyFound.check(cap, gs, new_company)
    assert check.validity is False
    assert "slot" in check.tooltip.lower()    # rejected for the right reason


def test_founding_places_company_in_first_free_slot(gs, cap):
    slot = b.found_company(gs, "Capitalists", "Supermarket")
    assert slot is gs.companies["Capitalists"][0]
    second = b.found_company(gs, "Capitalists", "Hotel")
    assert second is gs.companies["Capitalists"][1]


def test_founding_removes_company_from_market(gs, cap):
    slot = b.found_company(gs, "Capitalists", "Supermarket")
    assert slot.company not in cap.market


def test_founded_company_has_one_empty_place_per_required_worker(gs):
    slot = b.found_company(gs, "Capitalists", "Supermarket")
    assert len(slot.workers) == len(slot.company.worker_requirements)
    assert all(w is None for w in slot.workers)


# =============================================================================
# _WorkerHire
# A worker can fill a slot only if the slot is empty and the worker's class and
# skill match what the card asks for ("Any" accepts anything).
# =============================================================================

@pytest.fixture
def supermarket(gs):
    """A founded, empty Supermarket. Slot 0 needs an Agriculture worker, slot 1 anyone."""
    return b.found_company(gs, "Capitalists", "Supermarket")


def test_hiring_moves_worker_from_unemployed_into_slot(gs, supermarket):
    worker = b.spawn_unemployed(gs, "Working Class", "Agriculture")
    rules._WorkerHire.resolve(gs, worker, supermarket, 0)
    assert supermarket.workers[0] is worker
    assert worker not in gs.unemployed_workers["Working Class"]
    assert gs.corroborate_worker_count()


def test_cannot_hire_into_an_occupied_slot(gs, supermarket):
    first = b.spawn_unemployed(gs, "Working Class", "Agriculture")
    second = b.spawn_unemployed(gs, "Working Class", "Agriculture")
    rules._WorkerHire.resolve(gs, first, supermarket, 0)
    assert rules._WorkerHire.check(gs, second, supermarket, 0).validity is False


def test_cannot_hire_a_worker_with_the_wrong_skill(gs, supermarket):
    worker = b.spawn_unemployed(gs, "Working Class", "Media")
    assert rules._WorkerHire.check(gs, worker, supermarket, 0).validity is False


def test_any_skill_slot_accepts_unskilled_worker(gs, supermarket):
    worker = b.spawn_unemployed(gs, "Working Class", "Unskilled")
    assert rules._WorkerHire.check(gs, worker, supermarket, 1).validity is True


def test_cannot_hire_a_worker_who_is_already_employed(gs, supermarket):
    worker = b.spawn_unemployed(gs, "Working Class", "Agriculture")
    rules._WorkerHire.resolve(gs, worker, supermarket, 0)
    assert rules._WorkerHire.check(gs, worker, supermarket, 1).validity is False


def test_cannot_hire_into_a_slot_with_no_company(gs):
    worker = b.spawn_unemployed(gs, "Working Class", "Unskilled")
    empty_slot = gs.companies["Capitalists"][0]
    assert rules._WorkerHire.check(gs, worker, empty_slot, 0).validity is False


@pytest.mark.parametrize("player_count", [3])
def test_working_class_cannot_take_a_middle_class_only_slot(gs):
    slot = b.found_company(gs, "Middle Class", "Convenience Store")   # one Middle Class slot
    # Give the worker the skill the slot wants, so only their CLASS is wrong.
    wanted = slot.company.worker_requirements[0]["skill"]
    worker = b.spawn_unemployed(gs, "Working Class", "Unskilled" if wanted == "Any" else wanted)
    assert rules._WorkerHire.check(gs, worker, slot, 0).validity is False


# =============================================================================
# ImmigrationCardDraw
# Rulebook p10/p14: reveal a card, add the Worker it shows for your class, then
# "return the card(s) drawn to the bottom of the Immigration deck".
# =============================================================================

def test_capitalists_cannot_draw_immigration_cards(gs, cap):
    assert rules.ImmigrationCardDraw.check(gs, cap).validity is False


def test_immigration_draw_moves_the_card_to_the_bottom(gs, wc):
    top_card = gs.immigration_cards[0]
    rules.ImmigrationCardDraw.resolve(gs, wc)
    assert gs.immigration_cards[-1] is top_card
    assert gs.immigration_cards[0] is not top_card


def test_two_immigration_draws_reveal_two_different_cards(gs, wc):
    first, second = gs.immigration_cards[0], gs.immigration_cards[1]
    rules.ImmigrationCardDraw.resolve(gs, wc)
    rules.ImmigrationCardDraw.resolve(gs, wc)
    assert gs.immigration_cards[-2:] == [first, second]


def test_immigration_spawns_the_worker_shown_on_the_card(gs, wc):
    _, skill_on_card = gs.immigration_cards[0].WorkingClass
    rules.ImmigrationCardDraw.resolve(gs, wc)
    assert [w.skill for w in gs.unemployed_workers["Working Class"]] == [skill_on_card]
    assert wc.population_track == 1


def test_immigration_draw_keeps_deck_size(gs, wc):
    size_before = len(gs.immigration_cards)
    rules.ImmigrationCardDraw.resolve(gs, wc)
    assert len(gs.immigration_cards) == size_before
