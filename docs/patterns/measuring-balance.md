# Measuring balance

**A balance change is judged against a measurement, not against one savegame played by hand.**
`scripts/playtest` plays seeded savegames forward through the real message bus, with no browser, and
writes down what happened in each one. It reports; the issue the change belongs to decides whether the
result is good.

## Running it

It runs on the smoke settings and a database of its own, so a run never touches the development
savegames. The database needs the migrations and the reference data first, just like a smoke server's:

```bash
export SMOKE_DB_PATH=/tmp/playtest.sqlite3
export DJANGO_SETTINGS_MODULE=apps.config.settings_smoke
uv run python manage.py migrate --noinput
uv run python manage.py loaddata $(find apps -path '*/fixtures/*.json' -exec basename {} .json \; | sort)

uv run python -m scripts.playtest --games 50 --seed 1 --policy even --months 24 --output even.json
```

It prints one line per game and a count by outcome at the end. The JSON is rewritten after every game, so
a crash keeps what already ran. A crash is not caught: an exception inside a game is a bug in the game,
and it is not a data point.

- **Speed:** about a third of a second per month on SQLite, so a 24-month game that runs to the cap takes
  about 8 seconds.
- **Running side by side:** a process per database file. Give each batch its own `SMOKE_DB_PATH` and its
  own range of seeds.
- **Reproducibility:** a seed replays exactly, on a fresh database or in one that already holds other
  games. The game draws everything from the module-level `random`, which the harness seeds per game. The
  harness's own choices come off a generator of their own, seeded alike, so they never shift the game's
  draws. **A change that makes the game draw from its own `random.Random` breaks this silently.**

## What a game plays

A month of the player's sends what the views send, in the order a player meets them and behind the
refusal each view asks first (`scripts/playtest/player.py`):

1. every captive is taken into the band;
2. the whole fyrd reserve is drafted;
3. the pub is hired from, cheapest first, while 150 silver stays back;
4. the shop is bought from by the rule a rival buys by (`RivalPolicy`), while the 150 stays back;
5. the gear the faction holds - bought or looted - is handed out the way a rival's is, the best to the
   best men (`plan_gear_handout`);
6. one building is raised: the first of hall, sanctuary, weaponsmith and marketplace that may be upgraded
   and still leaves the 150;
7. the month's odd job is sent the fewest men it takes, the weakest at its attribute first and never
   the leader;
8. the band marches on the rival with the fewest men on their feet, if the policy says so, and shrinks
   until the march is affordable;
9. the fight is played out round by round;
10. every town with nobody left to hold it is ridden into;
11. the month is finished.

The player's men fight, shop and arm the way a rival's do: each one takes the action the game's own
decision service picks for him, and the faction buys and hands out by the rivals' rules. The harness brings
no judgement of its own to either, so a change to how the AI fights or spends moves both sides. It sends men
on no quest but the odd job, uses no Rally or Assault by choice and throws no feasts. A question that turns on one of those needs a policy
that uses it.

**Policies** differ only in when the band marches:

| Policy | Marches when |
|---|---|
| `aggressive` | every month it can |
| `even` | the band is at least as large as the target's healthy men |
| `prudent` | the band is at least two larger |

A game ends when it is won or lost, when it reaches `--months`, or when the harness cannot go on. In that
last case the reason goes into `stop_reason` instead of the loop:
- a fight that cannot be played out, because one side has nobody to field or the fight runs past 300 rounds;
- a month the game refuses to finish, because a skirmish is still open.

## What a report holds

Each game in the JSON has its seed, its policy, its outcome and the number of months played. It also has:

- fights won and lost, and marches held back by the policy or by the purse;
- how many men were drafted, hired, taken in from the cells and sent on a quest, and how many towns were
  occupied;
- how many items the player bought, and how many equips the hand-out made;
- successions on either side, and apart from them the leaders the fyrd raised when nobody was left on the
  roster;
- the months rivals were knocked out, and for each of them how many months it lasted after its first
  leader fell;
- what was built, as `[month, building, level]`;
- how many items the rivals bought, read off their ledgers;
- a `timeline` with one row per month: the player's living men, his silver, and each rival's living men,
  silver and hall level, each sorted on its own.

The counts of what the player did are there on purpose. A step that never fires across a whole batch is
how the harness shows it has fallen out of step with the views. The suite guards the same thing: it plays
five games to their end and fails if any step fired in none of them.

## Where the rules live

The view sequence is **copied** into `PlayerTurn`, not shared with the views. It stays safe to copy for
two reasons:

- **The command handlers re-check the guards that matter.** Every guard protecting silver, men or the month
  is asked a second time in the command handler ([the message bus](message-bus.md), *Dispatching*). So a
  refusal the harness forgot to ask would dispatch into a no-op. It would not play a game nobody can
  play.
- **The one rule that lives only in a form comes from the same source.** That rule is who may march, and
  the harness takes the band from the same `assess_roster(...).available_ids` that the attack form
  validates against.

A new guard that lives only in a view is the case this does not cover. Add the same guard to `PlayerTurn`
in the same change.
