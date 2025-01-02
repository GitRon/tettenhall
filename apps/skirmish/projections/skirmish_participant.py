from dataclasses import dataclass


@dataclass(kw_only=True)
class SkirmishParticipant:
    warrior_id: int
    faction_id: int
    skirmish_action_id: int  # TODO: if we go with choices, this will lose the "_id" suffix
