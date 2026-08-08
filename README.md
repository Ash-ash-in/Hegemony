# **HEGEMONY**


## Description
This a personal project, with the loose aim of finding new ways to play and test strategies for the board game *hegemony*.
The vision is to have three working modules:
- The game - all the rules, objects, and systems that enable someone to play the game.
- The actors - an interface for a human to play the game, and a rule-set to allow the 'automata' to play
- The brain - a machine learning model that is able to play the game, hopefully with some skill. Different models may be build for different play-styles.

The game should serve as the 'core' of the program, with different actors, be them humans, AI, or a rule-set, attached to different factions for the game.

The project serves primarily as an educational and entertainment tool for myself, so it should stay fun for me. I don't want it to get overwhelming, and I want to keep it manageable. That means taking things one step at a time, doing proof-of concept before diving in to the final product, and acheiving managable goals that can pass tests or add new features. I reserve the right to make braindead decisions and do things like a fucking moron.

No code is written by AI, but AI is used as a last resort to teach me new concepts.

# How it works

## Summary
![Hegemony Architecture-File Structure](<images/Hegemony - Full Architecture.png>)


- Two branches of code, one for the game engine, one for the NN training
- The game itself is genereally organised into 3 levels:
    - Data - Classes -> References -> Assets
    - Function - Rules -> States -> Context -> Rules ->
    - Game Engine - Engine, Agents, Interface
- Agents sit outside of this hierarchy but are always called from Context objects.
- These levels can only see themselves and the levels before it
- The middle layer can involve recursion, as each Context gathers information to resolve itself.
- Levels never look to anything higher than themselves. This promotes a single source of truth
- The top layer (HEGEMONY.py) controls the whole game superstructure and triggers both branches.

# Game Engine

## Data

- Found in the 'data' folder - references.py and classes.py
- This only includes resources - lists of game assets etc
- Classes of this layer are dumb and cannot be modified
- Functions exists to esablish variables once at startup, and are not triggered at any other point

## Rules & States & Context

### Rules.py
- This is how things happen. It moves things around, gets objects to change themselves, adds things to the gamestate
- Rules is where player and gamestate objects are changed
    - Runs transfers of money - instructs players to add/subtract money
    - Plays cards - Removes them from a hand, and activates their effect
    - Votes
    - Proposes laws
    - Instructs players to add points
- Agents cannot trigger these, but they may follow as a consequence of their decisions
- Rules can make calls to the agents for sub-tasks, such as choosing the location of a worker

### States.py
- Complex classes that contain information about the current game position
- There are 5 types:
    - Company slots, which contain all variable information about a company (workers emplyed, strike status, wage level)
    - One for each of the 4 players. The state's depends on whether an agent is controlling that faction
    - The gamestate, which contains everything else on and off the board, including card decks, worker pools, round number, laws etc.
- States are modified by their own methods, and are not changed by external calls. This allows them to contain their own simple validity checks.
- These methods are called by rules or the engine
- Anything affecting more than one state is instead handled by rules or the engine.

### Context.py
- Build a uniform snapshot of the state of play, passing all information that an agent can legally see
- Memorises all relevent game objects for easy access
- Compiles all options available for the decision required
- Calls the agent for its decision, recursively if necessary
- Unpacks the agent's response and matches it with the references in memory
- Executes that decision by triggering rules, passing the references and states along
- Top level context objects are triggered by the engine. The engine's context is resolved.

## Engine & Agents

### Engine.py
- Controls the setup and progression of the game
- Attaches agent instances to player states at the start of the game, giving them their 'head'
- Triggers the highest-level context windows, which allows the game to play out through a cascade of decisions.
- Records end-game results in memory

### Agents.py
- They receive packaged context calls and return a decision from the options contained in those calls
- Agents fall into several categories
    - Simple/Random Selectors
    - Pre-defined automa rules
    - Text context to human player
    - Neural Net
- One agent spun up per player and attached to the relevent player-state at startup
- They return their answer in a uniform package, which the context instance can receive and understand
- They save the call recevied and their answer to the decision log. This is where the bulk of the raw, unprocessed training data is saved in memory

# Neural Net 

The model will be trained with a PPO algorithm. The full state provided by the context needs to be encoded so that it is represented by a number of input nodes. The output will be interpreted by the model's head, which is determined by the type of action required of it. 

PPO models use an actor-critic function, and compute cost via backpropagation all the way back to the first encoding. The critic head will be used to determine expected cost, which also requires its own head.

None of this development has started, but the architecture of the game engine is designed so that the NN can be attached when ready, and so that training data is recorded throughout.

The reward functions will be recorded by postprocessing.py (not yet implimented), which handle intermittent rewards and the diminishing terminal reward.

The training of the model will be handled by training.py (not yet implimented), which will strip and shuffle decision batches out from recorded, post-processed games, which can be used for training. It will update the weights of the model and save them, which can then be attached to future games. 

# To Do
### Now
- Finish Neural Net Training Data Pipeline
    - Decisions saving  both actions properly - DONE
    - Decisions appends to existing file - DONE
    - Masked gamestate blank in decisions log
    - Fixed length for gamestate attributes
    - End-game file
    - Post-processing script
        - Split per faction
        - Assign rewards
        - Backfill terminal reward
    - Short term rewards
    - Terminal rewards
- Run Neural Net on test actions, based on optimising money, as POC

### Soon
- Bugfixes
    - game.engine INFO log always records player money as 0 - DONE
    - NPC state has its own influence
    - Action phase is only recording one decision in output json - DONE
- Engine
    - Prep Phase
        - Political agenda cards
    - Action Phase
        - Election Test Action (to propose tax law)
    - Elections phase
        - Elections flow
    - Context
        - Election context
        - Law Proposal context
        - Random agent response
- NN
    - Proposal decision
    - Election decision

### Eventually
- Worker assignment action
    - context
    - checks - Paused
    - resolve - Paused
- Worker Swap free action
    - context
    - checks
    - resolve
- Found company action
    - context
    - checks
    - add workers too?
    - resolve
- Sell Company action
    - context
    - checks
    - resolve
    - check trade unions
---