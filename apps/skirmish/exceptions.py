class UnknownSkirmishParticipantError(Exception):
    """
    Raised when a posted warrior id names somebody who is not fighting this skirmish.

    Deliberately not the "RuntimeError" the rest of the codebase raises: those mark states that should
    be unreachable - an unknown building type, a difficulty that is not a difficulty - while this one is
    ordinary bad input from a request, which the view answers with the 400 it gives every other piece of
    unusable input. A "RuntimeError" here would be the very shape this story fixes, where an action that
    named no action reached the damage services and answered 500.

    It lives here rather than beside the service that raises it because it crosses a layer: the service
    raises it and the view catches it, so it belongs to neither.
    """
