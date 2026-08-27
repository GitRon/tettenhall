# Content review: playing the story

The gates prove the code agrees with itself. The review lenses prove it reads correctly. Neither of them
ever loaded a page. This is the phase where the game runs and somebody looks at it.

## What this phase catches, and what it does not

Worth the wall-clock: a flow the player cannot finish, a control wired to nothing, a screen that renders
empty or 500s, a number on the page that contradicts the rule the story implemented, a feature no
navigation ever links to, a month log that reports something other than what happened.

Not worth it: spacing and colour judgement, anything that needs a dozen months of play to show up,
timing races, and any state you had to hand-edit the database into. Those are either somebody else's
phase or nobody's.

## Getting the app up

```bash
bash .claude/skills/implement-story/scripts/content-server.sh fresh   .claude/runs/<slug>
bash .claude/skills/implement-story/scripts/content-server.sh restart .claude/runs/<slug>
bash .claude/skills/implement-story/scripts/content-server.sh stop    .claude/runs/<slug>
```

`fresh` deletes the smoke database and starts from an empty world. `restart` keeps it. **Use `restart`
after every code change** - the server runs with `--noreload`, so until you do, the browser is still
testing the code you just replaced. This is the mistake that turns a fixed bug into a second fix round.

The script prints the base URL, the login and the log path. It runs on a throwaway SQLite file inside the
run directory, so nothing here can touch the development savegames. The login is by **email address**,
not username - that is what the form asks for.

Creating a savegame through the form leaves you with one faction, one warrior, 1000 silver and month #1.
Those numbers come from the `CreateNewSavegame` handler; read it rather than trusting this paragraph if
the story turns on them.

## The habits of this app, which decide how you drive it

1. **Everything is behind login.** `LoginRequiredMiddleware` is on. A redirect to `/account/login/` means
   your session is gone, not that the feature is broken.
2. **Three failed logins lock the account out for fifteen minutes.** Do not guess the password - the
   script prints it, and every `start` clears stale lockouts from the smoke database.
3. **Most of the game needs an active savegame.** Without one the nav is nearly empty and half the URLs
   have nothing to resolve. A savegame with no player faction is a legal state, so an empty nav is not
   automatically a defect.
4. **The interactive parts are htmx.** `hx-post` sits on `<a>` elements with no `href`, which reach the
   accessibility tree as a generic element with a pointer cursor rather than a link - click them by their
   text. After a mutating click the URL often does not change; snapshot again to see what swapped.
5. **A failing htmx request does not look like a failure.** `base.html` turns any 5xx into a UIkit toast
   reading "An error has occurred." that disappears after one second, and htmx does not swap on error, so
   the page just sits there looking fine. **Check `browser_network_requests` after every mutating
   interaction.** This is the single most missable failure in this codebase.
6. **Django messages are toasts too**, on the same one-second timeout. If you need to read one, snapshot
   immediately after the click.
7. **`DEBUG` is on**, so a full-page 500 arrives as the yellow traceback page - the exception is right
   there in the snapshot, and the full traceback is in `content/server.log`.
8. **Static files come from `node_modules/`.** The script installs them if they are missing and refuses to
   start otherwise, because without htmx and UIkit every control on every page is dead and the whole
   review is false negatives.

## Write the journey before you click

Put it in `content/journey.md` first, as numbered steps with an expected outcome each. A journey written
afterwards is just a description of whatever happened.

The baseline journey runs every time, whatever the story was. It is six steps and it catches the damage a
story does somewhere other than where it was aimed:

1. Log in.
2. `/savegame/create/` - fill it, submit, land on the dashboard.
3. The dashboard renders, and the nav shows the faction and the town.
4. Every nav entry loads: faction detail, town square, town upgrades, training, skirmishes, finance.
5. **Finish month** - month logs appear and the silver in the nav moves.
6. Every page the diff touched, whether or not the story mentions it.

Then the story journey: the steps a player takes to reach and use the new behaviour, straight out of
`spec.md`, with the expected outcome of each written down before you start. Include the failure paths the
story specifies - refusing an upgrade you cannot afford is behaviour too.

## Reaching the state the story needs

Play to it where playing is cheap. Finishing a month is one click; a month log, a salary payment and a
building income all come for free with it.

Where playing is not cheap, seed the precondition through the shell:

```bash
SMOKE_DB_PATH=.claude/runs/<slug>/content/smoke.sqlite3 \
  DJANGO_SETTINGS_MODULE=apps.config.settings_smoke \
  uv run python manage.py shell -c "<python>"
```

**Seed preconditions, never the effect you are checking.** Granting the faction the silver an upgrade
costs is a precondition. Setting the building level that the upgrade is supposed to produce means you
tested nothing and will report a pass. If a state cannot be reached by playing and cannot be seeded
without faking the outcome, say so in the journey and leave the step unverified rather than pretending.

The smoke user is a superuser, so `/admin/` is available for reading the resulting state when a page does
not show enough of it.

## Observing

- `browser_snapshot` is the default. It is the accessibility tree, it is cheap, and you can quote it.
- `browser_take_screenshot` only when the finding is visual, saved next to the journey in `content/`.
- `browser_network_requests` after every mutating interaction - see habit 5.
- `browser_console_messages` at the end of each leg of the journey.
- `tail` the server log when anything returned 500.

One browser, one tab, driven from this session. Do not hand this phase to parallel agents: there is a
single browser behind the Playwright tools and two drivers would fight over it.

## The browser is shared with every other checkout on this machine

`@playwright/mcp` does not launch a browser per server. Unless it was started with `--isolated`, it asks
a machine-wide daemon for the *unnamed* browser, and every other unnamed server gets the same one. Two
content reviews running at once therefore share one Chrome: one of them finds the other's tabs in its
snapshot, and the other loses its page mid-navigation to

```
Error: async initializeServer: Target page, context or browser has been closed
```

That error is not your story and no amount of restarting the smoke server fixes it. When you see it, or
when a snapshot shows a tab you never opened, check whether another checkout is in Phase 6
(`git worktree list`, then look for a live `content/.pid` in each).

Two ways out, in order of preference:

1. **Isolate the server**, once, in the `playwright` entry of `~/.claude.json` - add `"--isolated"` to
   its `args`. Concurrent servers then each get their own browser, verified up to three at a time. The
   cost is that the profile lives in memory, so nothing survives an MCP restart - which for this phase is
   no cost at all, because every round logs in from scratch anyway.
2. **Serialise the phase.** Wait for the other checkout's content review to finish, or record this one as
   `blocked` with the reason and ship without it, the same as any other phase that could not run.

Either way, never `browser_close` your way out of a collision: on a shared daemon browser that is the
other run's browser too.

Budget: the baseline journey, the story journey, and **at most ten exploratory interactions beyond them.**
Past that, write down what you have and stop. A browser is an excellent place to lose an hour.

## Recording what you found

Each step in `journey.md` gets a `result:` line - `pass`, or `fail` and the finding it produced. Findings
go in `content/findings.md`:

```content-finding
claim: One sentence stating what a player sees that is wrong.
severity: blocker | high | medium | low
where: URL, and the control you clicked
steps: the shortest path from a fresh savegame that reproduces it
expected: what the story says should happen
actual: what happened
evidence: the failing request, the console error, the traceback line, or the screenshot path
story-caused: yes | no
```

`story-caused: no` goes to the out-of-scope list, same as in the code review - name it, do not fix it.

## Not a finding

- Styling and spacing, unless the page is unusable.
- The warrior/silver/skirmish counters in the nav going stale after an htmx swap. `base.html` carries a
  todo saying so; it is older than your story.
- Behaviour `spec.md` explicitly put out of scope.
- Anything reproducible only from a database state the game cannot produce.
- Slowness on a first request, which is Django importing itself, not the story.

## When it will not run

- **The server will not start.** The script says why: no virtualenv, no `settings_smoke`, no frontend
  dependencies. Fix the environment; if you cannot, the phase is blocked, and that goes in the report.
- **You cannot reach the story's screen at all.** That is not a blocked phase, that is the finding -
  an unreachable feature, severity high.
- **Playwright is not connected.** Record the phase as skipped with the reason. Never report a pass you
  did not see.
- **Another checkout is already driving the browser.** `Target page, context or browser has been closed`,
  or tabs you never opened. Isolate the MCP server or wait - see above - and record the phase as
  `blocked` if you do neither.

## Teardown

Stop the server and close the browser, pass or fail. A server left running holds the port and will serve
pre-fix code to the next run, which is a lie that costs a whole round to notice.
