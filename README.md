# **HEGEMONY**
---

## Description
This a personal project, with the loose aim of finding new ways to play and test strategies for the board game *hegemony*.
The vision is to have three working modules:
- The game - all the rules, objects, and systems that enable someone to play the game.
- The actors - an interface for a human to play the game, and a rule-set to allow the 'automata' to play
- The brain - a machine learning model that is able to play the game, hopefully with some skill. Different models may be build for different play-styles.
The game should serve as the 'core' of the program, with different actors, be them humans, AI, or a rule-set, attached to different factions for the game.
The project serves primarily as an educational and entertainment tool for myself, so it should stay fun for me. I don't want it to get overwhelming, and I want to keep it manageable. That means taking things one step at a time, doing proof-of concept before diving in to the final product, and acheiving managable goals that can pass test or add new features. I reserve the right to make braindead decisions and do things like a fucking moron.

---

# What I'm up to
- Seting up scoring. Im just getting the basic point methods set up in the player class
- I should test how these appear in setup. I'll need a quick and dirty test to set up some fake factions to do that
- Then I should get some rules working to get points to change
- And finally call these rules in an set up function in the engine
- I should carry on with methods that can be inherited by all classes next.

---

# How it works

## Code structure
- Everything is organised into 3 levels: data, rules, engine
- These levels can only see themselves and the levels before it
- Levels never look to anything higher than themselves. This promotes a single source of truth
### Data
- This only includes resources - lists of game assets etc
- This should not contain any logic, but it may contain classes with methods
- These methods will never be called directly, but should instead by called through functions defined in rules
- Rules should almost always be the only thing calling data. The engine should only orchestrate rules except in very specific circumstances
- Any functions affect only one entity. Anything more complex is handled by rules/engine
### Rules
- This is how things happen. It move things around, gets objects to change themselves, adds things to the gamestate
- Rules is where player and gamestate objects are changed
    - Runs transfers of money - instructs players to add/subtract money
    - Plays cards - Removes them from a hand, and activates their effect
    - Votes
    - Proposes laws
    - Instructs players to add points
### Engine
- Controls the setup, save state, and movement of the game
- Controls the flow between stages of the game, movement between rounds

## Game States
These store information about the game and players. They are the real-life boards that things sit on. 
They only contain material things that would be required to recreate the game position.
They do not contain logic or plans
They should retain limited history to allow 'undo' of actions

## Neural Net 
The AI will need to simulate lots of different outcomes, compare them, and make its decision
This is the only part of the game that needs such comparisons, except to confirm rules such as players having enough money to pay
This means no comparison or easy access to the data needs to built into the game engine itself
The AI will save the current state, and create multiple new ones for comparison
Gamestates should be changable with careful preservation 
