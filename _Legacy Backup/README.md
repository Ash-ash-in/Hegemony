# Hegemony
My silly little neural net experiment starting with the hardest game I've ever played

---------------------------------------------------------------------
1) Architecture Blueprint (Designed for Complex Strategy Games)

Your game is complicated, so you need strict modular architecture.
Think of your project as a machine made of independent parts.

project/
│
├── core/
│   ├── state.py
│   ├── actions.py
│   ├── rules.py
│   ├── transitions.py
│
├── engine/
│   ├── turn_manager.py
│   ├── phase_manager.py
│
├── agents/
│   ├── base_agent.py
│   ├── rule_agent.py
│   ├── random_agent.py
│   ├── mcts_agent.py
│
├── simulation/
│   ├── rollout.py
│   ├── evaluator.py
│
├── training/
│   ├── self_play.py
│   ├── dataset.py
│
├── tests/
│
└── docs/

Responsibilities of Each Module:

state.py

Pure immutable data
No logic allowed.
Only definitions like:
  GameState
  PlayerState
  BoardState

actions.py

Defines legal action types
  BuildFactory
  HireWorker
  RaiseTaxes
No rules. Just definitions.

rules.py

Validates moves
  eg. is_action_legal(state, action)

transitions.py

Applies actions
  eg. apply_action(state, action) -> new_state


This is the heart of the engine.

engine/

Controls flow of the game
Handles:

turn order
phases
victory detection

agents/

Decision makers only.
Agents never modify state.
They only:
  choose_action(state)
  simulation/
  Runs hypothetical futures.
Used by AI.

training/

Self-play logic.
Stores results.

tests/

Unit tests for rules.

---------------------------------------------------------------------
2) Development Order (CRITICAL)

Do NOT build randomly. Follow this exact order:

STEP 1 — State Representation
  Build immutable game state.
  No rules. No engine. No AI.
  Just:
  initial_state()

STEP 2 — Action Definitions
Define every possible move.
Even ones you won’t implement yet.

STEP 3 — Rule Validator
Implement:
  is_action_legal()
Test heavily.

STEP 4 — State Transition Engine
Implement:
  apply_action()
This is the hardest part.
Do this before ANY AI.

STEP 5 — Game Loop Engine
while not terminal:
    action = agent.choose_action(state)
    state = apply_action(state, action)

STEP 6 — Random Agent
Simple:
  choose random legal move
If this works → your engine works.

STEP 7 — Rule-Based Agent

Hard-coded logic.

STEP 8 — Simulation Engine
Ability to simulate games fast.

STEP 9 — AI Agent
Now you add ML / search.

---------------------------------------------------------------------
3) What ONE Development Session Should Look Like

Never sit down and “just code”.
Use this ritual:
  Start of Session (5 min)
  Open your NEXT_STEPS.md
  Pick ONE task
  Example:
  Implement worker hiring rule
  During Session
  
Rule:
You are not allowed to start another task until this one is complete or blocked.
End of Session (5 min)

Update file:
DONE
- worker hiring rule
NEXT
- test worker hiring
- implement tax action
BUGS
- worker cost incorrect

This removes the “where was I?” problem forever.

---------------------------------------------------------------------
4) Task Planning System (Used by Engineers)

Use this structure:

Task Levels
Epic - Huge feature: Implement economy system
Task - Specific system: Implement taxation
Subtask - One sitting: Add tax deduction rule

Always work at subtask level.

---------------------------------------------------------------------
5) Version Control Like a Professional

Never code without commits.
Commit Rule
Commit every time you:
  finish a rule
  add a class
  fix a bug
  pass a test

Good Commit Messages
  add worker hiring rule
  fix tax rounding bug
  refactor state structure

Professional Commit Pattern
  git add .
  git commit -m "implement legal move validator"

Branching Strategy (Simple Version)

Use branches:
  main
  dev
  feature-tax-system
  feature-ai-agent

Workflow:
branch → code → test → merge

Never work directly on main.

---------------------------------------------------------------------
6) Golden Development Principles

These separate clean projects from messy ones.

Rule 1 — Pure Functions Only
  Never mutate state.
  Always: new_state = apply_action(old_state)

Rule 2 — Deterministic Logic
  Given same state + action → same result.
  Always.

Rule 3 — No Hidden Side Effects
  Functions should not secretly modify globals.

Rule 4 — Small Functions
  Max 30 lines.

Rule 5 — Tests Before Expansion
  If feature is complex:
  write test first.

---------------------------------------------------------------------
7) Debugging Strategy Used in Industry

When bug appears:
  Reproduce
  Write test that fails
  Fix code
  Confirm test passes
Never fix blindly.

---------------------------------------------------------------------
8) Warning Signs Your Architecture Is Breaking

If you notice:
  you don’t know where logic belongs
  same rule appears twice
  you fear editing code
  debugging takes hours
→ you need refactoring.

This is normal.
