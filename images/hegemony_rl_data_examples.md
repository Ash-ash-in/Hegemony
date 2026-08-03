# Hegemony RL — Decision Data Examples

A worked example tracing one decision — the second worker placement inside a Working Class "Assign Workers" action — from what the agent receives through to the record actually used for training. Field names and values are illustrative; adjust to match your engine.

## Sequence context

This decision is `seq 16`, the third of four calls made to resolve one "Assign Workers" main action:

| seq | decision_type | what happens |
|---|---|---|
| 14 | `main_action` | Working Class chooses "Assign Workers" |
| 15 | `assign_workers_placement` | places `w3` → `union_labour_2` |
| **16** | `assign_workers_placement` | **traced in full below** |
| 17 | `assign_workers_placement` | places `w2` → `union_labour_1` |

All four belong to the same faction and run back to back — nothing else happens between them, so there's no "other faction's turn" gap here, unlike between separate main-action decisions later in the game.

`opponents` below lists only the capitalist faction for brevity — a real record would include every other faction in play.

## 1. What the agent receives

The `ContextCall` payload passed to `Agent` for seq 16. Note `action_in_progress`, which carries forward what this same activation of "Assign Workers" has already committed — this is the piece that gives the model memory across its own sub-decisions.

```json
{
  "decision_type": "assign_workers_placement",
  "faction": "working_class",
  "round": 2,
  "phase": "action",

  "state": {
    "self": {
      "money": 12,
      "points": 8,
      "workers": {
        "unplaced": ["w1", "w2"],
        "placed": ["w3", "w4", "w5", "w6"]
      },
      "companies_owned": ["factory_a"]
    },
    "opponents": [
      { "faction": "capitalist", "money": 20, "points": 12, "companies_owned": ["mine_b", "farm_c"] }
    ],
    "board": {
      "available_companies": ["press_d", "hospital_e"],
      "policies": { "labour": 2, "taxation": 1, "welfare": 3 },
      "unemployment": 4
    }
  },

  "action_in_progress": {
    "action": "assign_workers",
    "placements_so_far": [
      { "worker": "w3", "slot": "union_labour_2" }
    ],
    "placements_remaining": 2
  },

  "available_actions": {
    "workers": ["w1", "w2"],
    "slots": ["factory_a_slot_1", "factory_a_slot_2", "union_labour_1"]
  }
}
```

`available_actions` is split into two small lists rather than a flat cross-product of every (worker, slot) pair — this is the hierarchical-head pattern from earlier: the network picks a worker, then a slot conditioned on that worker, as two small softmaxes instead of one that grows combinatorially as the roster and board scale up.

## 2. What the agent returns

The `AgentAnswer` — one pick from each list:

```json
{
  "worker": "w1",
  "slot": "factory_a_slot_1"
}
```

## 3. What gets saved (decisions.jsonl)

Written once, after the answer comes back. State and action combine with metadata; `reward` and `game_outcome` stay `null` at write time — this file is never edited after the fact.

```json
{
  "game_id": "g_0042",
  "seq": 16,
  "faction": "working_class",
  "agent_type": "automa",
  "decision_type": "assign_workers_placement",
  "parent_decision_id": 14,
  "step": "2 of 3",
  "round": 2,
  "phase": "action",

  "state": {
    "self": {
      "money": 12,
      "points": 8,
      "workers": { "unplaced": ["w1", "w2"], "placed": ["w3", "w4", "w5", "w6"] },
      "companies_owned": ["factory_a"]
    },
    "opponents": [
      { "faction": "capitalist", "money": 20, "points": 12, "companies_owned": ["mine_b", "farm_c"] }
    ],
    "board": {
      "available_companies": ["press_d", "hospital_e"],
      "policies": { "labour": 2, "taxation": 1, "welfare": 3 },
      "unemployment": 4
    }
  },
  "action_in_progress": {
    "action": "assign_workers",
    "placements_so_far": [{ "worker": "w3", "slot": "union_labour_2" }],
    "placements_remaining": 2
  },
  "available_actions": {
    "workers": ["w1", "w2"],
    "slots": ["factory_a_slot_1", "factory_a_slot_2", "union_labour_1"]
  },
  "action_taken": { "worker": "w1", "slot": "factory_a_slot_1" },

  "reward": null,
  "game_outcome": null
}
```

For context, `seq 14` (the parent) is the same shape as any `main_action` record you're already logging:

```json
{
  "game_id": "g_0042",
  "seq": 14,
  "faction": "working_class",
  "agent_type": "automa",
  "decision_type": "main_action",
  "round": 2,
  "phase": "action",
  "state": { "...": "same shape as above, omitted here" },
  "available_actions": ["play_card", "sell_company", "assign_workers", "strike"],
  "action_taken": { "type": "assign_workers" },
  "reward": null,
  "game_outcome": null
}
```

## 4. outcomes.jsonl

One line per completed game, written when `g_0042` finishes:

```json
{
  "game_id": "g_0042",
  "winner": "capitalist",
  "scores": { "working_class": 31, "capitalist": 47, "state": 38 },
  "final_money": { "working_class": 8, "capitalist": 34, "state": 15 },
  "total_decisions": 94
}
```

## 5. The final training tuple (post-processed)

What `post_process.py` produces for `seq 16` — written to a new file, separate from the raw log. `next_state` is pulled from this same faction's *next* record, `seq 17`, not the next line in the raw file.

```json
{
  "game_id": "g_0042",
  "faction": "working_class",
  "seq": 16,

  "state": {
    "self": {
      "money": 12,
      "points": 8,
      "workers": { "unplaced": ["w1", "w2"], "placed": ["w3", "w4", "w5", "w6"] },
      "companies_owned": ["factory_a"]
    },
    "opponents": [
      { "faction": "capitalist", "money": 20, "points": 12, "companies_owned": ["mine_b", "farm_c"] }
    ],
    "board": {
      "available_companies": ["press_d", "hospital_e"],
      "policies": { "labour": 2, "taxation": 1, "welfare": 3 },
      "unemployment": 4
    }
  },
  "action": { "worker": "w1", "slot": "factory_a_slot_1" },

  "reward": 0.2,
  "reward_breakdown": { "money_delta": 0.0, "points_delta": 0.0, "worker_placed": 0.2 },

  "next_state": {
    "self": {
      "money": 12,
      "points": 8,
      "workers": { "unplaced": ["w2"], "placed": ["w1", "w3", "w4", "w5", "w6"] },
      "companies_owned": ["factory_a"]
    },
    "opponents": [
      { "faction": "capitalist", "money": 20, "points": 12, "companies_owned": ["mine_b", "farm_c"] }
    ],
    "board": {
      "available_companies": ["press_d", "hospital_e"],
      "policies": { "labour": 2, "taxation": 1, "welfare": 3 },
      "unemployment": 4
    }
  },

  "done": false,
  "game_outcome": {
    "winner": "capitalist",
    "scores": { "working_class": 31, "capitalist": 47, "state": 38 }
  }
}
```

Two things worth noticing. `opponents` and `board` are identical between `state` and `next_state` — nothing happens for anyone else between two sub-calls of the same compound action, so nothing should change there. And `game_outcome` is attached even though this isn't the game-ending decision — it's backfilled onto every record from that game, not just the last one, so you can use it as context or as a Monte-Carlo-style label independent of the step-by-step reward.

Field names shift slightly toward standard RL notation here (`action_taken` → `action`, plus new `next_state`/`done`) — that's convention, not a requirement. Keep whatever your training code expects.

## Notes

**The terminal record.** Working Class's actual last decision of the game (say `seq 93`) produces a tuple in the same shape, but with `done: true`, and `reward` includes a terminal component on top of the dense shaping — e.g. `reward: 0.2 + (-5.0)` if the game ended in a loss for this faction. Scale the terminal bonus well outside the range of your dense rewards so it dominates the return without swamping earlier gradient signal.

**Behavioural cloning pairs.** For Phase 1 pre-training you don't need any tuple construction at all — just pull `state` (+ `action_in_progress` if present) and `action_taken` straight from the raw decision log. No reward, no `next_state`, no post-processing required.

**The seq gap.** Within one compound action, `next_state` sits right next door (`seq 17` follows `seq 16` directly, same faction, nothing between them). Across separate main-action decisions later in the game, other factions' turns fall in between, so the gap in `seq` is real — `next_state` might be a dozen or more records further down the file.
