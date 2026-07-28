# Adding a new flow

1. Define the Command in `apps/<app>/messages/commands/<domain>.py`.
2. Write its command handler in `apps/<app>/handlers/commands/<domain>.py`; do the work, return an Event
   defined in `apps/<app>/messages/events/<domain>.py`.
3. For each reaction, add an event handler — in whichever app owns the reaction — returning further
   Commands.
4. Dispatch the initial Command from the view via `handle_message`.
5. Keep querysets evaluated to lists on messages; keep `context` keyword-only.
6. Unit-test each handler directly, and let the [registry tests](registry-tests.md) prove the chain
   actually connects.

Every command you emit needs a handler — an instruction nobody executes is always a bug, and the registry
tests fail on it with no allowlist. An event without a consumer can be legitimate; add it to
`TERMINAL_MESSAGES`.

## See also

- [The message bus](message-bus.md) — what commands and events mean
- [Writing a handler](handlers.md) — signature and conventions
- [Where code goes](app-layout.md) — the directory layout
