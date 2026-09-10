# Adding a new flow

1. Define the Command in `apps/warband/<topic>/messages/commands/<domain>.py`.
2. Write its command handler in `apps/warband/<topic>/handlers/commands/<domain>.py`; do the work, return
   an Event defined in `apps/warband/<topic>/messages/events/<domain>.py`. The handler has to sit in the
   **same topic** as its command — [strict mode](strict-mode.md) refuses it otherwise.
3. For each reaction, add an event handler — in whichever topic owns the reaction — returning further
   Commands. Events deliberately cross topics; commands do not.
4. Dispatch the initial Command from the view via `handle_message`.
5. Keep querysets evaluated to lists on messages; keep `context` keyword-only.
6. Unit-test each handler directly, and let the [registry tests](registry-tests.md) prove the chain
   actually connects.

`<domain>` is not free-form — [where code goes](app-layout.md#messages-and-handlers) says which module
each of these lands in, and a test enforces it for the command/handler pair.

Every command you emit needs a handler — an instruction nobody executes is always a bug, and the registry
tests fail on it with no allowlist. An event without a consumer can be legitimate; add it to
`TERMINAL_MESSAGES`.

## See also

- [The message bus](message-bus.md) — what commands and events mean
- [Writing a handler](handlers.md) — signature and conventions
- [Where code goes](app-layout.md) — the directory layout, and what has to sit at the app root instead
  of in a topic package
- [Strict mode](strict-mode.md) — the scope a command handler has to share with its command
