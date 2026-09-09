# Raising

Two kinds of thing go wrong, and they need different exceptions. The question to ask at a `raise` is not
how bad it is — it is **whether anything is allowed to catch it**.

## A state that should be unreachable

Reference data that is missing, an enum value that is not in the enum, a savegame with no player faction.
`RuntimeError`, with a message naming what was not there.

Nobody catches these. They mean the deployment or the code is wrong, and a 500 is the honest answer —
a caught one would be a bug reported as a shrug. Most raises in this project are this kind:

```python
raise RuntimeError(
    f"Culture {context.faction_culture_id} does not exist. "
    f"Load the reference data with 'loaddata culture itemtype questname'."
)
```

If there is something the reader can do about it, the message is the place to say it.

## Input that can reach you

Anything derived from a request. It needs an exception a **caller can catch and answer for**, so it gets
one of its own:

```python
raise UnknownSkirmishActionError(f"Attack action {attack_action} is not a skirmish action.")
```

A bare `RuntimeError` cannot do that job: catching it would swallow the first kind too. So the exception
type chosen at the raise site decides whether the caller can answer bad input with the 400 it deserves or
has to let it out as a 500 nobody meant.

## Where a custom exception lives

In an app-level `exceptions.py` — `apps/warband/skirmish/exceptions.py`. These cross layers: a service raises and
a view catches, so the exception belongs to neither and sits above both.

Name it for what is wrong and end it in `Error`. Subclass `Exception`; there is no project base class,
and two exceptions do not need a hierarchy.

## The message is part of the contract

Every raise carries a message, custom exception or not, because
[test conventions](testing-conventions.md) require `pytest.raises(SomeError, match="...")` — a bare
`pytest.raises` also passes on the wrong error of the right type. An exception raised without a message
cannot be tested that way.

Put the offending value in it. `f"Attack action {attack_action} is not a skirmish action."` says which
action; `"Invalid attack action"` sends the reader back to the logs.

## Catching

A view catching a custom exception answers with a status, not with a message to the player:

```python
try:
    ...
except UnknownSkirmishParticipantError:
    return HttpResponse(status=HTTPStatus.BAD_REQUEST)
```

The better place to refuse bad input is the boundary, before the service is reached at all —
`SkirmishFinishRoundView.post` constructs `SkirmishActionChoices(int(...))` off the request and answers
400 when that fails, so an unknown action never gets as far as `get_service_by_attack_action`. The custom
exception is the guarantee for the *next* caller, which may have no such boundary.

## See also

- [Where code goes](app-layout.md) — the layers an exception crosses
- [Test conventions](testing-conventions.md) — `pytest.raises` and `match`
