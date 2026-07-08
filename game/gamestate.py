import logging
logger = logging.getLogger(__name__)
logger.debug("Importing data.common")
from dataclasses import dataclass, field



# common variables used across files
@dataclass
class GameState:
    """
    GameState is the master storage location for all game information. 
    It contains everything that you would need to know to recreate the game at this given position
    """
    ### Attributes ###
    player_count: int
    round: int = 1
    phase: str = 'Preparation'
    turn: int = 1
    active_player: str = "Working Class"
    company_deck: dict = field(default_factory=dict)
    companies: dict = field(default_factory=dict)
    worker_pool: dict = field(default_factory=dict)
    unemployed_workers: dict = field(default_factory=dict)
    players: dict = field(default_factory=dict) # players must be the last arg, since it is appended to the dict in load_save

    ### Methods ###
    def to_dict(self) -> dict: # For saving
        return {k.lstrip('_'): v for k, v in vars(self).items()}
    

    # State Display
    def check_founded_companies(self, faction: str):
        count = 0
        for k, v in self.companies[faction].items():
            if v is not None:
                count += 1
        return count
    

    # Safety Checks
    def corroborate_worker_count(self):
        """Checks if the population trackers of WC (and MC) are true to the workers on the board"""
        WC_track = 0
        MC_track = 0

        # Record Players' Understanding
        WC_num = self.players['Working Class'].population_track
        if self.player_count > 2:
            MC_num = self.players['Middle Class'].population_track
            
        # Count Workers in Companies
        for factioncomps in self.companies.values():
            for comp in factioncomps.values():
                if comp is None: # Ignore unfilled company slots
                    continue
                for worker in comp.workers.values():
                    if worker is None: # If there is no worker in the first slot, there are no workers
                        continue
                    if worker.faction == 'Working Class':
                        WC_track += 1
                    if worker.faction == 'Middle Class':
                        MC_track += 1

        # Count Unemployed Workers
        for worker in self.unemployed_workers['Working Class']:
            WC_track += 1
        for worker in self.unemployed_workers['Middle Class']:
            MC_track += 1                
        
        # Compare Values
        acc = True
        if WC_track != WC_num:
            acc = False
        if self.player_count > 2 and MC_track != MC_num:
            acc = False

        # Display Error Messages
        if not acc:
            logger.error(f"Worker counts cannot be reconciled.")
            logger.error(f"Working Class Player tracker believes there are {WC_num}. Checker found {WC_track}.")
            if self.player_count > 2:
                logger.error(f"Middle Class Player tracker believes there are {MC_num}. Checker found {MC_track}")
                     
        return acc
