# **HEGEMONY**


## Description
This a personal project, with the loose aim of finding new ways to play and test strategies for the board game *hegemony*.
The vision is to have three working modules:
- The game - all the rules, objects, and systems that enable someone to play the game.
- The actors - an interface for a human to play the game, and a rule-set to allow the 'automata' to play
- The brain - a machine learning model that is able to play the game, hopefully with some skill. Different models may be build for different play-styles.

The game should serve as the 'core' of the program, with different actors, be them humans, AI, or a rule-set, attached to different factions for the game.

The project serves primarily as an educational and entertainment tool for myself, so it should stay fun for me. I don't want it to get overwhelming, and I want to keep it manageable. That means taking things one step at a time, doing proof-of concept before diving in to the final product, and acheiving managable goals that can pass test or add new features. I reserve the right to make braindead decisions and do things like a fucking moron.

No code is written by AI, but AI is used as a last resort to teach me new concepts.


# How it works

## Code structure
- The game itself is genereally organised into 3 levels: data, rules, engine
- These levels can only see themselves and the levels before it
- Levels never look to anything higher than themselves. This promotes a single source of truth
- This is not strictly true, for example when setting up agent references, but upstream references are only created at the engine level, and not when a class is instantiated
- Agents exist as an outside entitiy, which connect to each part of the game as required
### Data
- This only includes resources - lists of game assets etc
- Classes of this type can only modify themselves (eg. factions, workers)
- These methods will never be called directly, but should instead by called through functions defined in rules
- Rules should always call those methods if they are the result of an agent decision. The engine itself can do it in hard-coded situations
- Any functions affect only one entity. Anything more complex is handled by rules/engine
### Rules
- This is how things happen. It move things around, gets objects to change themselves, adds things to the gamestate
- Rules is where player and gamestate objects are changed
    - Runs transfers of money - instructs players to add/subtract money
    - Plays cards - Removes them from a hand, and activates their effect
    - Votes
    - Proposes laws
    - Instructs players to add points
- Agents cannot trigger these, they follow as a consequence of their decisions
- Rules can make calls to the agents, but usually only for simpler decisions
### Engine
- Controls the setup, save state, and movement of the game
- Controls the flow between stages of the game, movement between rounds
- Makes Action calls to the agents, which causes a cascade of minor decisions made by the rules
### Agents
- They receive packaged context calls
- They have their own processes to make a decision
    - Random
    - Text context to human player
    - Neural Net fine tuning
- They return their answer in a uniform package, which the engine can receive and understand

### Architecture Diagram
![alt text](<images/Hegemony Architecture-File Structure.png>)

## Game States
These store information about the game and players. They are the real-life boards that things sit on.\n
They only contain material things that would be required to recreate the game position.\n
For a ML to train, it may need to make multiple deepcopies of the live gamestate, and simulate outcomes

## Player States
These act a similar way to the gamestate in that they store board information, but they should only be modified through rules, whereas the gamestate is much more flexible

## Action Flow
Actions are called through several layers, which help manage dependencies. As a general rule, validity checks flow upstream, and instructions flow downstream.
See below:
![alt text](<images/Hegemony Architecture-Action Flow.png>)

The impact of every decision is not made directly to the game/player state, it is made to a copy, and the final decision is enacted by overwriting the state with the copy. *This still needs to be implimented with the resolve functions*

## Neural Net 
The AI will need to simulate lots of different outcomes, compare them, and make its decision
This is the only part of the game that needs such comparisons, except to confirm rules such as players having enough money to pay
This means no comparison or easy access to the data needs to built into the game engine itself
The AI will save the current state, and create multiple new ones for comparison
Gamestates should be changable with careful preservation 

# To Do
- Worker assignment action
    - checks - DONE
    - context - In progress
    - resolve - In progress
- Worker Swap free action
    - checks
    - context
    - resolve
- Sell Company action
    - checks
    - context
    - resolve
    - check trade unions
- Found company action
    - checks
    - context
    - add workers too?
    - resolve
---