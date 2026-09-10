# Agent guide

Tettenhall is a Django browser game about Anglo-Saxon factions, built around a CQRS-style message bus.

**[README.md](README.md) indexes every doc.** It is the map — there is deliberately no second list here to
drift out of step with it.

The docs are normative for the areas they cover, not background reading. Read the relevant one *before*
touching that area, and do not infer the conventions from whatever code happens to be nearby: this project
deviates from the Django defaults on purpose in several places.

Five where getting it wrong is both expensive and silent:

| Before you… | Read |
|---|---|
| write or change any test, factory, fixture or test setting | [Testing strategy](docs/patterns/testing-strategy.md) |
| add or edit a message, a handler, or anything dispatched through the bus | [The message bus](docs/patterns/message-bus.md) |
| touch a view that resolves a model object | [Savegame scoping](docs/patterns/savegame-scoping.md) |
| change a game-balance number | [Town buildings](docs/patterns/town-buildings.md) |
| add a model, template, template tag, fixture, admin or management command | [Where code goes](docs/patterns/app-layout.md) |

**There are two Django apps, and neither is a topic.** `apps.warband` is the whole game and
`apps.common` is its one satellite app — `apps.faker_frisian`, `apps.faker_gaelic` and
`apps.faker_old_english` are satellites as well, but plain packages under `apps/` rather than apps. The game's structure lives in topic packages *inside* `warband`
(`apps/warband/faction/`, `apps/warband/skirmish/`, …). Django looks exactly one fixed path into an app
for everything it discovers, so a model, template, template tag, fixture, admin registration or
management command put in a topic package instead of the app root simply never loads — with no error
anywhere. That is what the last row above is for.
