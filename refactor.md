# Refactor Plan

So far the call / context process is messy and self-referential
I need to streamline this so that shared assets are kept in a file with dumb objects only, and more complext stuff is kept at a master level

The recursive context loop is the tricky part:
- How do I identify which rules need to activate to complete an action?
- When do I call the agent?
- When do I log them?
- How do I test?
- What format is robust against bugs and easy to maintain/expand

## The decision process
Player, Automa and NN are all different here. Fleshing out there needs here will help me understand the architectural requirements. Final decision at the bottom.

### Human

#### Needs
- Needs to be able to explore options and backtrack
- Only locks in the full chain once a final decision has been made
- Needs lots of feedback on what is or isnt allowed and why
- *All visualisation comes from what the agent receives* - this protects from leaking info to the client through silent bugs

#### Module Roles

Context: Contains enough information for detailed visual feedback

Agent: Information is passed to agent that provides every visual cue for the UI. May also return an undo button to reset the chain and to restore the turn.

Rules: Needs special undo action. *Rules do not change in place.* Either needs to reshuffle revealed cards in this process, or commit to locking in the action before revealing. 

### Automa

#### Needs
- Follows a distinct set of rules based on the context and automa card
- Uses different rulesets - they may need their own Player methods too.

#### Module Roles

Context: provides the same information as usual, but will only need to occur once or twice.

Agent: determines which rules can be triggered based on automa card. *Needs persistent internal trackers* to determine which actions to pick.

Rules: Response actives its unique rules, which exist in rule layer but in their own package

### Neural Net

#### Needs
- Calls an external body to make its decisions
- Information needs to be encoded in a truck that can be manipulated by the training process
- Can act like a human from the game engines perspective, but it doesn't matter if it affects the game engine in place.

#### Module Roles

Context: Only requires the bare minimum information

Agent: Needs to determine model head, encode, run actor model, run critic model, decode. Unsure which parts sit in agents.py and which sit in training.py

Rules: Standard rules, in-place or not.

## How do I append them to the log?
- At the time of call - but missing result
- At the time of response - but missing the resulting state to compare
- At the end of chain - but actions will fall out of order

## Architecture

actions.py:
- Called by game engine, can interect with the three decision modules itself, so variables can easily be shared and logged
- Recursion happens here, where there is little else to manage
- Original gamestate can be preserved here to handle undo actions
- Logging happens here - maybe after each step to keep it clear? 
    - Context records what was seen
    - Agent records response (and log_prob)
    - Post-execution records the new gamestate for analysis
- Testing should be easier as each model is designed to be operated by an external actor
- Explore using yield instead of return to control the decision loop?

context.py
- Is just about capturing and masking the game
- Creates reference dicts
- Checks available options - *must sit above rules*
- Tooltip and visual data needs to be firmly attached, but cleanly seperate. This will allow uniform transmission, consistent visualisation and makes it easy for the NN to discard

messages.py
- Very simple assets
- Ensure uniform structure between communicating modules

agents.py
- Just receives the context and outputs the answer
- All agents recieve a context
- Non humans trim the context down to lose the visual data

rules.py
- Need to keep clear distinction between rules of different complexity - simple reusable ones to the top
- *Cannot reference other decision modules*

postprocessing.py
- Needs to be relatively low level, as it will be called during and after games to evaluate
- Can refer to common assets to ensure data quality, but otherwise does not read from game files
- All other training files need to sit above (unless they have their own shared assets)

unit.py
- Need to build tests for existing components first, so that the refactor is as clean as possible

integration.py
- Leave these tests until refactor is complete, but don't consider refactor done until they pass
