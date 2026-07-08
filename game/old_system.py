from dataclasses import asdict, dataclass
import logging
from typing import Any
logger = logging.getLogger(__name__)

@dataclass
class Engine:
    from game.data.classes import GameState
    from game.old_agents import Agent, AgentAnswer
    from game.old_factions import Player
    logger.debug("Calling engine class")
    agents = {}

    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances, according to those defined in the dictionary passed.
        Agents can be found in the engine, or in the player objects
        This modifies the engine and players in place
        """
        logger.debug("Setting up agents")
        from game.old_agents import agent_refs
        from game.data.classes import faction_play_order
        agent_references = {}
        for faction, agent_name in faction_agents.items():
            if faction not in faction_play_order:
                raise Exception(f"{faction} not recognised")
            if agent_name not in agent_refs.keys():
                raise Exception(f"{agent_name} not recognised")
            faction_instance = gamestate.players[faction]
            agent_references[faction] = agent_refs[agent_name](faction_instance)
            faction_instance.agent = agent_references[faction]
        self.agents = agent_references
        return

    @staticmethod
    def startup(settings_dict: dict):
        """
        Process for launching a game.
        Handles validity checks and decides whether to load or start new game
        
        If player_count is None, a game is loaded
        If player_count exists, a new game is created
            New game uses filename if provided, else creates from timestamp
        If both player_count and filename are none, raise exception
        """
        ######################
        #### NOTE TO SELF ####
        ######################

        # New game should load a game from a default template
        # Setup should read a settings file

        ################################
        from game.old_system import Save

        # Unpack settings
        player_count = settings_dict['player_count']
        faction_agents = settings_dict['agents']
        save_mode = settings_dict['save_mode']
        filename = settings_dict['save_name']
        overwrite = settings_dict['overwrite_file']

        # Validity Checks
        if filename == 'None':
            raise Exception('filename cannot be "None"')
        if filename:
            if type(filename) != str:
                raise Exception('filename must be a string')
        if player_count:
            if type(player_count) != int:
                raise Exception('player_count must be an integer')
            if player_count > 4 or player_count < 2:
                raise Exception('player count must be between 2 and 4')
        if len(faction_agents) != player_count:
            raise Exception('Number of agents passed does not match player_count')  
        if save_mode.lower() not in ('new','load'):
            raise Exception("save_mode not recognised. Must be 'new' or 'load'.")  

        # Load / Create savefile
        logging.debug(f"engine.startup called with player_count: {player_count if player_count else 'None'} and filename: {filename if filename else 'None'}")
        if save_mode == 'load':
            if filename is None:
                raise Exception('Must pass filename when loading game')
            logging.info(f"Loading game from save file: {filename}")
            gamestate = Save.load_game(filename)
            player_count = gamestate.player_count
        else:
            if player_count is None:
                raise Exception('Must pass player_count when starting new game')
            gamestate, filename = Save.new_game(player_count, filename=filename, overwrite=overwrite)
            logging.info(f'Created new save file: {filename}')

        # Load in easy player references
        from game.data import classes
        logger.debug("Setting up player references")
        player_references = classes.PlayerReference(
            classes.faction_instantiate_order[:player_count],
            classes.faction_play_order,
            working_class=gamestate.players['Working Class'],
            middle_class=gamestate.players['Middle Class'] if player_count > 2 else None,
            capitalists = gamestate.players['Capitalists'],
            state=gamestate.players['State']
        )

        return gamestate, player_references


    @staticmethod
    def start_position(gamestate: GameState):
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a brand new game.
        """
        logger.debug('Called Engine.start_position')
        import game.old_rules as old_rules
        from game.old_context import SimpleContext

        # Build player refs
        working_class, middle_class, capitalists, state  = gamestate.players.values()

        ####################################
        ### TEMPORARY give everyone 120 ####
        for name, inst in gamestate.players.items():
            if old_rules.MoneyTransfer.check(None, inst, 120, True).validity:
                old_rules.MoneyTransfer.resolve(None, inst, 120, True)
        logger.debug('Temporary start position money complete')
        ### TEMPORARY give everyone 120 ####
        ####################################

        ### Prepare gamestate attributes ###

        # Build empty card decks and worker pools
        gamestate.company_deck = {'Capitalists': [], 'State': [], 'Working Class': [], 'Middle Class': []}
        gamestate.companies = { # Company slots on board
            'Capitalists': {'C'+str(i+1): None for i in range(12)}, 
            'Working Class': {'C1': None, 'C2':None},
            'Middle Class': {'C'+str(i+1): None for i in range(8)},
            'State': {'C'+str(i+1): None for i in range(9)}
            }
        gamestate.unemployed_workers = {'Working Class': [], 'Middle Class': []}
        gamestate.build_company_decks()
        gamestate.build_worker_pool()
        gamestate.build_immigration_cards()
        logger.debug('Gamestate card and worker deck framework complete')

        def hire_from_scratch(_company, _faction):
            """Handy tool to spawn all workers for and staff a company"""
            for slotname, ref in _company.worker_slots.items():
                if ref.skill == 'Any':
                    skill = 'Unskilled'
                else:
                    skill = ref.skill
                old_rules.WorkerSpawn.resolve(gamestate, _faction, skill)
                worker = gamestate.unemployed_workers[_faction.faction][-1]
                old_rules.WorkerHire.resolve(gamestate, worker, _company, slotname)

        ### Found  Capitalist Companies ###

        founded_companies = [] 
        checked_companies = [] # Non-starter companies
        for company in gamestate.company_deck['Capitalists']:
            if company.name in ("Supermarket", "Shopping Mall", "College", "Clinic") and company.name not in founded_companies:
                gamestate.players['Capitalists']._company_hand.append(company)
                old_rules.CompanyFound.resolve(gamestate.players['Capitalists'], gamestate, company)
                founded_companies.append(company.name)

                # Supermarket - always working class
                if company.name == 'Supermarket':
                    hire_from_scratch(company, working_class)
                
                # Shopping mall - class depends on player count
                elif company.name == "Shopping Mall":
                    if gamestate.player_count == 2:
                        hire_from_scratch(company, working_class)
                    elif gamestate.player_count > 2:
                        hire_from_scratch(company, middle_class)

                # College - only staffed when > 2 players
                elif gamestate.player_count > 2 and company.name == 'College':
                    hire_from_scratch(company, working_class)

            # Non-Starter companies
            else:
                checked_companies.append(company)
        gamestate.company_deck['Capitalists'] = checked_companies
        # Final Validity Checks
        if gamestate.check_founded_companies('Capitalists') != 4:
            raise Exception(f'Incorrect number of capitalist companies at startup ({gamestate.check_founded_companies('Capitalists')})')

        ### Found Middle Class Companies ### 

        if gamestate.player_count > 2:
            founded_companies = []
            checked_companies = [] # Non-starter companies
            for company in gamestate.company_deck['Middle Class']:

                # Found
                if company.name in ("Convenience Store", "Doctor's Office") and company.name not in founded_companies:
                    gamestate.players['Middle Class']._company_hand.append(company)
                    old_rules.CompanyFound.resolve(gamestate.players['Middle Class'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire
                    if company.worker_slots[1].skill == 'Any':
                        skill = 'Unskilled'
                    else:
                        skill = company.worker_slots[1].skill
                    old_rules.WorkerSpawn.resolve(gamestate, middle_class, skill)
                    worker = gamestate.unemployed_workers['Middle Class'][-1]
                    old_rules.WorkerHire.resolve(gamestate, worker, company, 1)

                # Ignore
                else:
                    checked_companies.append(company)
            gamestate.company_deck['Middle Class'] = checked_companies
            # Final Validity Checks
            if gamestate.check_founded_companies('Middle Class') != 2:
                raise Exception(f'Incorrect number of middle class companies at startup ({gamestate.check_founded_companies('Middle Class')})')

        ### Found State Companies ### 

        founded_companies = []
        removed_companies = [] # Clear 3 companies for state
        checked_companies = [] # Non-starter companies
        for company in gamestate.company_deck['State']:

            # Companies to found / ignore
            if gamestate.player_count == 2:

                # Found
                if company.name in ("Regional TV Station", "Public University", "Public Hospital") and company.name not in founded_companies:
                    gamestate.players['State']._company_hand.append(company)
                    old_rules.CompanyFound.resolve(gamestate.players['State'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire
                    if company.name in ("Public University", "Public Hospital"):
                        hire_from_scratch(company, working_class)

                # Ignore
                if company.name in ("University Hospital", "Technical University", "National Public Broadcasting"):
                    removed_companies.append(company.name) # Adding it to the list prevents duplicates.
                    # The removal happens when checked_companies replaces the pool in gamestate

            elif gamestate.player_count > 2:

                # Found
                if company.name in ("University Hospital", "Technical University", "National Public Broadcasting"):
                    gamestate.players['State']._company_hand.append(company)
                    old_rules.CompanyFound.resolve(gamestate.players['State'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire 
                    if company.name == "University Hospital":
                        hire_from_scratch(company, working_class)
                    if company.name == "Technical University":
                        hire_from_scratch(company, middle_class)

                # Ignore
                if company.name in ("Regional TV Station", "Public University", "Public Hospital") and company.name not in removed_companies:
                    removed_companies.append(company.name) # Adding it to the list prevents duplicates.
                    # The removal happens when checked_companies replaces the pool in gamestate

            # Companies for the State's "Market"
            else:
                checked_companies.append(company)
        gamestate.company_deck['State'] = checked_companies
        # Final Validity Checks
        if gamestate.check_founded_companies('State') != 3:
            raise Exception(f'Incorrect number of state companies at startup ({gamestate.check_founded_companies('State')})')
        if len(removed_companies) != 3:
            raise Exception(f"Incorrent number of state companies removed ({len(removed_companies)})")
        
        logger.debug('All starter companies founded successfully')

        ### Unemployed Worker Spawning ###

        # Working Class first worker
        old_rules.WorkerSpawn.resolve(gamestate, working_class, 'Unskilled')

        # Working Class immigration cards
        old_rules.ImmigrationCardDraw.resolve(gamestate, working_class)
        if gamestate.player_count > 2:
            old_rules.ImmigrationCardDraw.resolve(gamestate, working_class)

            # Middle Class first worker
            answer = SimpleContext.spawn_worker_call( # Call agent for a decision to start
                gamestate, 
                middle_class, 
                middle_class.agent
                )
            old_rules.WorkerSpawn.resolve(gamestate, middle_class, answer.name)
            
            # Middle Class immigration cards
            old_rules.ImmigrationCardDraw.resolve(gamestate, middle_class)
            old_rules.ImmigrationCardDraw.resolve(gamestate, middle_class)

        assert gamestate.corroborate_worker_count()
        logger.debug("All workers spawned and placed successfully")
        
        return gamestate

    def preparation_phase(self, gamestate: GameState):
        """
        Runs the system - driven preparation actions.
        All actions are mandatory.
        """
        logger.debug('Called Engine.preparation_phase')
        return gamestate
    

    def action_phase(self, gamestate: GameState):
        """
        Handles the process for calling the DecisionContext and sending commands downstream
        
        WARNING: This modifies GameState's 'turn', 'active_player', and 'free_action_taken' in place.
        WARNING: This replaces the GameState based on ~decisions taken~
        """
        from game.old_context import ActionContext
        logger.debug('Called Engine.action_phase')

        ### Start the Action Phase ###

        for turn_num in range(1,6):
            logger.info(f'Starting action phase turn {turn_num}')
            gamestate.turn = turn_num # Update for save file
            for faction_name, player_instance in gamestate.players.items():
                if faction_name == 'State' and gamestate.player_count < 4:
                    continue
                if faction_name == "Middle Class" and gamestate.player_count < 3:
                    continue
                logger.info(f"It's the {faction_name}'s turn")
                gamestate.active_player = faction_name # Update for save file

                # Call the agent
                agent = self.agents[player_instance.faction]
                answer = ActionContext.action_call(agent, True, True, gamestate, player_instance)
                logger.debug(f"Agent answer: {answer}")

                # Enact the response
                if answer.order is None:
                    raise Exception('Order "None" response given before any action taken')
                args = [player_instance] + answer.args
                mini_log = f"Enacting {answer.name}."
                if len(answer.args) > 0:
                    mini_log += f" Args = {answer.args}"
                logger.info(mini_log)
                answer.order.resolve(*args)         

                # Check for a free action following a main
                if answer.primary_response == True:
                    answer = ActionContext.action_call(agent, False, True, gamestate, player_instance)
                    if answer.order is None:
                        continue
                    args = [player_instance] + answer.args
                    mini_log = f"Enacting {answer.name}."
                    if len(answer.args) > 0:
                        mini_log += f" Args = {answer.args}"
                    logger.info(mini_log)
                    answer.order.resolve(*args)      
                
                # Otherwise demand a main action response
                elif answer.primary_response == False:
                    answer = ActionContext.action_call(agent, True, False, gamestate, player_instance)
                    if answer.order is None:
                        raise Exception('Main action required, None cannot be passed')
                    else:
                        args = [player_instance] + answer.args
                        mini_log = f"Enacting {answer.name}."
                        if len(answer.args) > 0:
                            mini_log += f" Args = {answer.args}"
                        logger.info(mini_log)
                        answer.order.resolve(*args) 

        return gamestate

    @staticmethod
    def production_phase(gamestate: GameState):
        logger.debug('Called Engine.production_phase')
        return gamestate

    @staticmethod
    def elections_phase(gamestate: GameState):
        logger.debug('Called Engine.elections_phase')
        return gamestate

    @staticmethod
    def scoring_phase(gamestate: GameState):
        logger.debug('Called Engine.scoring_phase')
        return gamestate

    @staticmethod
    def endgame_scoring(gamestate: GameState):
        logger.debug('Called Engine.endgame_scoring')
        return gamestate

    def flow(self, gamestate: GameState):
        """
        Main Execution of game. Runs constantly during play.

        WARNING: This modifies GameState's 'round' and 'phase' in place.
        """
        logger.debug('Called Engine.flow')
        from game.data.classes import phases

        for round in range(0,6):
            logger.info(f'Starting Round {round}')
            gamestate.round = round

            if round == 0:
                self.start_position(gamestate)
                continue

            for phase in phases:

                if phase == phases[0] and round == 1:
                    continue # First round gets no preparation phase
                
                logger.info(f'Begining phase: {phase}')

                if phase == phases[0]:
                    gamestate = self.preparation_phase(gamestate)
                elif phase == phases[1]:
                    gamestate = self.action_phase(gamestate)
                elif phase == phases[2]:
                    gamestate = self.production_phase(gamestate)
                elif phase == phases[3]:
                    gamestate = self.elections_phase(gamestate)
                elif phase == phases[4]:
                    gamestate = self.scoring_phase(gamestate)

        gamestate = self.endgame_scoring(gamestate)

