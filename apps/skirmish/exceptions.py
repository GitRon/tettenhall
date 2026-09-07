class UnknownSkirmishParticipantError(Exception):
    """
    Raised when a posted warrior id names somebody who is not fighting this skirmish.

    Ordinary bad input from a request rather than an unreachable state, so it is a custom exception the
    view catches and answers with the 400 it gives every other piece of unusable input - see
    docs/patterns/exceptions.md.
    """


class UnknownSkirmishActionError(Exception):
    """
    Raised when a number that is not a skirmish action is asked for its attack service.

    Same kind as "UnknownSkirmishParticipantError": the number arrives in a request, so whoever asks has
    to be able to catch this and refuse the input rather than let a 500 out. "SkirmishActionView.post"
    already refuses an unknown action at the boundary; this is the guarantee for the next caller, which
    may have no such boundary.
    """
