from wocbots.interaction import HistoryStore, ReferenceInteractionPolicy, CertaintyFlipScoringPolicy

class EncounterData:
    def __init__(self,
                 history_store : HistoryStore,
                 interaction_policy : ReferenceInteractionPolicy,
                 scoring_policy : CertaintyFlipScoringPolicy) -> None:
        self.history_store = history_store
        self.interaction_policy = interaction_policy
        self.scoring_policy = scoring_policy