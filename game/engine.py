import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from game.data.classes import Config

class Engine:
    from game.states import GameState

    def setup_gamestate(self, config: Config):
        logger.debug("Establishing gamestate in engine")
        from game.states import GameState

        # Validity Checks
        if config.player_count < 2 or config.player_count > 4:
            raise Exception('player count must be between 2 and 4')
        if config.player_count != len(config.agents.keys()):
            raise Exception("player_count and agents mismatch")
        
        # Setup Players
        logger.debug("Setting up players within gamestate setup")
        from game.states import WorkingClass, MiddleClass, Capitalists, PlayerState, NPCState
        players = {}
        players["Working Class"] = WorkingClass()
        if config.player_count == 2:
            players["Capitalists"] = Capitalists()
        else:
            players["Middle Class"] = MiddleClass()
            players['Capitalists'] = Capitalists()
        if config.player_count == 4:
            players["State"] = PlayerState()
        else:
            players["State"] = NPCState()
        

        # Setup GameState
        gamestate = GameState(
                players,
                config.player_count,
                config.game_id.game_id
            )

        return gamestate

    def setup_agents(self, faction_agents: dict, gamestate: GameState) -> None:
        """
        Creates the agent instances according to those defined in the dictionary passed.
        Agents can be found in the engine, or in the player objects
        This modifies the engine and players in-place
        """
        logger.debug("Setting up agents")
        from game.agents import agent_refs
        from game.data.references import faction_play_order
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
    
    def engine_startup(self, config) -> GameState:
        """Runs all the engine setup functions"""
        logger.debug("Executing engine startup")
        gamestate = self.setup_gamestate(config)
        self.setup_agents(config.agents, gamestate)
        return gamestate

    @staticmethod
    def start_position(gamestate: GameState): 
        """
        Sets up the board accoring the the rulebook, for a new game
        WARNING this modifies the GameState and Player objects in place!
        Only use this in a brand new game.
        """
        logger.debug('Called Engine.start_position')
        import game.rules as rules

        # Build player refs
        for name, cls in gamestate.players.items():
            if name == "Working Class":
                working_class = cls
            elif name == "Middle Class":
                middle_class = cls
            elif name == "Capitalists":
                capitalists = cls
            elif name == "State":
                state = cls
            else:
                raise Exception("Unrecognised faction")

        ####################################
        ### TEMPORARY give everyone 120 ####
        logger.warning('Using temporary start position money')
        for name, inst in gamestate.players.items():
            rules._MoneyTransfer.resolve(None, inst, 120, True)
        ### TEMPORARY give everyone 120 ####
        ####################################

        logger.debug("Founding starter companies")
        def hire_from_scratch(_companyslot, _faction) -> None:
            """Handy tool to spawn all workers for and staff a company"""
            logger.debug("Hiring 'from scratch'")
            for i in range(len(_companyslot.company.worker_requirements)):
                ref = _companyslot.company.worker_requirements[i]
                if ref['skill'] == 'Any':
                    skill = 'Unskilled'
                else:
                    skill = ref['skill']
                rules._WorkerSpawn.resolve(gamestate, _faction, skill)
                worker = gamestate.unemployed_workers[_faction.faction][-1]
                rules._WorkerHire.resolve(gamestate, worker, _companyslot, i)
            return

        ### Found  Capitalist Companies ###

        founded_companies = [] # Start companies
        checked_companies = [] # Non-starter companies
        slotnum = 0
        for company in gamestate.company_deck['Capitalists']:
            if company.name in ("Supermarket", "Shopping Mall", "College", "Clinic") and company.name not in founded_companies:
                companyslot = gamestate.companies["Capitalists"][slotnum]

                # Add company to market and found
                gamestate.players['Capitalists']._market.append(company)
                rules._CompanyFound.resolve(gamestate.players['Capitalists'], gamestate, company)
                founded_companies.append(company.name)

                # Supermarket - always working class
                if company.name == 'Supermarket':
                    hire_from_scratch(companyslot, working_class)
                
                # Shopping mall - class depends on player count
                elif company.name == "Shopping Mall":
                    if gamestate.player_count == 2:
                        hire_from_scratch(companyslot, working_class)
                    elif gamestate.player_count > 2:
                        hire_from_scratch(companyslot, middle_class)

                # College - only staffed when > 2 players
                elif gamestate.player_count > 2 and company.name == 'College':
                    hire_from_scratch(companyslot, working_class)

                slotnum += 1

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
            slotnum = 0
            for company in gamestate.company_deck['Middle Class']:

                # Found
                if company.name in ("Convenience Store", "Doctor's Office") and company.name not in founded_companies:
                    companyslot = gamestate.companies["Middle Class"][slotnum]
                    gamestate.players['Middle Class']._market.append(company)
                    rules._CompanyFound.resolve(gamestate.players['Middle Class'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire
                    skill = company.worker_requirements[0]["skill"]
                    rules._WorkerSpawn.resolve(gamestate, middle_class, skill)
                    worker = gamestate.unemployed_workers['Middle Class'][-1]
                    rules._WorkerHire.resolve(gamestate, worker, companyslot, 0)
                    slotnum += 1

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
        slotnum = 0
        for company in gamestate.company_deck['State']:

            # Companies to found / ignore
            if gamestate.player_count == 2:

                # Found
                if company.name in ("Regional TV Station", "Public University", "Public Hospital") and company.name not in founded_companies:
                    companyslot = gamestate.companies["State"][slotnum]
                    gamestate.players['State']._market.append(company)
                    rules._CompanyFound.resolve(gamestate.players['State'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire
                    if company.name in ("Public University", "Public Hospital"):
                        hire_from_scratch(companyslot, working_class)

                    slotnum += 1

                # Ignore
                if company.name in ("University Hospital", "Technical University", "National Public Broadcasting"):
                    removed_companies.append(company.name) # Adding it to the list prevents duplicates.
                    # The removal happens when checked_companies replaces the pool in gamestate

            elif gamestate.player_count > 2:

                # Found
                if company.name in ("University Hospital", "Technical University", "National Public Broadcasting"):
                    companyslot = gamestate.companies["State"][slotnum]
                    gamestate.players['State']._market.append(company)
                    rules._CompanyFound.resolve(gamestate.players['State'], gamestate, company)
                    founded_companies.append(company.name)

                    # Hire 
                    if company.name == "University Hospital":
                        hire_from_scratch(companyslot, working_class)
                    if company.name == "Technical University":
                        hire_from_scratch(companyslot, middle_class)

                    slotnum += 1

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
        rules._WorkerSpawn.resolve(gamestate, working_class, 'Unskilled')

        # Working Class immigration cards
        rules.ImmigrationCardDraw.resolve(gamestate, working_class)
        if gamestate.player_count > 2:
            rules.ImmigrationCardDraw.resolve(gamestate, working_class)

            # Middle Class first worker
            from game.context import SpawnedWorkerSkillContext
            SpawnedWorkerSkillContext(gamestate, middle_class, "", 1)
            # Middle Class immigration cards
            rules.ImmigrationCardDraw.resolve(gamestate, middle_class)
            rules.ImmigrationCardDraw.resolve(gamestate, middle_class)

        assert gamestate.corroborate_worker_count()
        logger.debug("All workers spawned and placed successfully")
        
        return gamestate


    def preparation_phase(self, gamestate: GameState):
        """
        Runs the system - driven preparation actions.
        All actions are mandatory.
        """
        logger.debug('Called Engine.preparation_phase')
        from game.rules import _MoneyTransfer

        # Pay interest on loans
        logger.info("Paying interest on any loans")
        for player in gamestate.players.values():
            for i in range(player.loans):
                assert _MoneyTransfer.check(player, None, 5, True).validity == True
                _MoneyTransfer.resolve(player, None, 5, True)

        return gamestate
    

    def action_phase(self, gamestate: GameState):
        """
        Handles the process for calling the DecisionContext and sending commands downstream
        
        WARNING: This modifies GameState's 'turn', 'active_player', and 'free_action_taken' in place. 
        WARNING: This replaces the GameState based on ~decisions taken~
        """
        from game.context import ActionContext
        from game.data.references import faction_play_order
        logger.debug('Called Engine.action_phase')

        ### Start the Action Phase ###

        for turn_num in range(1,6):
            logger.info(f'\n{'#'*20} Starting action phase turn {turn_num} {'#'*20}')
            gamestate.turn = turn_num
            for faction_name in faction_play_order:

                # Update gamestate's temporal data with who's turn it is
                if faction_name == 'State' and gamestate.player_count < 4:
                    continue
                if faction_name == "Middle Class" and gamestate.player_count < 3:
                    continue
                logger.info(f"\n{'#'*10} It's the {faction_name}'s turn {'#'*10}")
                gamestate.active_player = faction_name
                player = gamestate.players[faction_name]

                # Run the action
                ActionContext(gamestate, player)

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
        from game.data.references import phases

        for round in range(0,6):
            logger.info(f'Starting Round {round}')
            gamestate.round = round

            if round == 0:
                self.start_position(gamestate)
                continue

            logger.info(f"\n{'#'*40}\n{'#'*20} ROUND {round} {'#'*20}\n{'#'*40}")

            for phase in phases:

                if phase == phases[0] and round == 1:
                    continue # First round gets no preparation phase

                if phase == phases[0]:
                    logger.info(f"\n{'#'*20} PREPARATION PHASE {'#'*20}")
                    gamestate = self.preparation_phase(gamestate)
                elif phase == phases[1]:
                    logger.info(f"\n{'#'*20} ACTION PHASE {'#'*20}")
                    gamestate = self.action_phase(gamestate)
                elif phase == phases[2]:
                    logger.info(f"\n{'#'*20} PRODUCTION PHASE {'#'*20}")
                    gamestate = self.production_phase(gamestate)
                elif phase == phases[3]:
                    logger.info(f"\n{'#'*20} ELECTIONS PHASE {'#'*20}")
                    gamestate = self.elections_phase(gamestate)
                elif phase == phases[4]:
                    logger.info(f"\n{'#'*20} SCORING PHASE {'#'*20}")
                    gamestate = self.scoring_phase(gamestate)

        gamestate = self.endgame_scoring(gamestate)
