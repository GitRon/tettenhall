# Tettenhall

A Django browser game about Anglo-Saxon factions, built around a CQRS-style message bus.

## Documentation

Each doc is normative for the area it covers. Read the relevant one before working in that area rather than
inferring the conventions from nearby code.

### Getting started

- [Local setup](docs/contributing/setup.md) — stack, dependencies, running the app and the suite
- [Linting](docs/contributing/linting.md) — ruff, boa-restrictor, pre-commit
- [Settings](docs/contributing/settings.md) — application vs test settings, queuebie configuration
- [Commit messages](docs/contributing/commit-messages.md)

### Architecture

- [Where code goes](docs/patterns/app-layout.md) — app layout and which layer holds business logic
- [The message bus](docs/patterns/message-bus.md) — commands vs events, the golden rule, dispatching
- [Writing a handler](docs/patterns/handlers.md) — signature, registration, return values
- [Adding a new flow](docs/patterns/adding-a-flow.md) — the end-to-end checklist
- [Strict mode](docs/patterns/strict-mode.md) — what it enforces, and where it does not
- [Savegame scoping](docs/patterns/savegame-scoping.md) — the scoping mixins and the leaks they prevent
- [Town buildings](docs/patterns/town-buildings.md) — building levels, costs and effects, and where a
  balance number belongs

### Testing

- [Testing strategy](docs/patterns/testing-strategy.md) — what to test, at which level
- [Test conventions](docs/patterns/testing-conventions.md) — layout, naming, assertions
- [Test data](docs/patterns/testing-data.md) — factories and reference data
- [Mocking](docs/patterns/mocking.md) — first-party mocks are a review finding
- [Coverage](docs/patterns/coverage.md) — the 100% branch gate
- [Registry tests](docs/patterns/registry-tests.md) — the four tests covering the message wiring

### Planning

- [Backlog](docs/collaboration/backlog.md) — open ideas and unfinished work
- [Writing an issue](docs/collaboration/writing-issues.md) — labels, anatomy, and the review pass before
  an issue is created

## Credits

Icons: [game-icons.net](https://game-icons.net)
