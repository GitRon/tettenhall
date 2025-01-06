from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


class AssignFighterPairsService:
    """
    This service keeps logic for the handler for assigning fighter pairs at the start of a skirmish.
    """

    @staticmethod
    def determine_larger_group(
        *, skirmish_participants_1: list[SkirmishParticipant], skirmish_participants_2: list[SkirmishParticipant]
    ) -> tuple[list[SkirmishParticipant], list[SkirmishParticipant]]:
        """
        The larger crowd is always starting
        """
        if len(skirmish_participants_1) >= len(skirmish_participants_2):
            larger_group = skirmish_participants_1
            smaller_group = skirmish_participants_2
        else:
            larger_group = skirmish_participants_2
            smaller_group = skirmish_participants_1

        return larger_group, smaller_group
