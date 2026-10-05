from collections.abc import Callable


def passes_first_time(real: Callable) -> Callable:
    """
    A side effect for a patched refusal check: the first call lets the request through, every later one
    is the real check.

    How a view test stages the request that loses a race. In production the losing request reads the state
    before the winning one writes, so its refusal passes and its command handler then turns it down. One
    thread cannot interleave two requests like that - the second request's refusal would simply catch it -
    so the test lets the first check through over a state that refuses, which is the one thing the race
    does. It is a mock of first-party code, and this is the stated reason docs/patterns/mocking.md asks for.
    """
    calls: list[None] = []

    def side_effect(**kwargs) -> str | None:
        if not calls:
            calls.append(None)
            return None

        return real(**kwargs)

    return side_effect
