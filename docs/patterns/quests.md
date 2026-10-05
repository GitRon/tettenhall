# Quests

A quest is an errand the world asks a war band to send men on: carry the king's summons, see a thegn's
daughter to the minster, bring a champion home from the crossroads. It is never a fight. It musters
nobody, stages no skirmish and is not a march, so a quest and an attack on a rival are two different
decisions: the attack spends the month on a rival, the quest spends men on something else.

`apps/warband/quest/` owns the catalogue, the board and the homecoming; what a quest brings home lands in
the topics that own those rows, the way an incident's levers do.

## The month of a quest

```
PlayerMonthPrepared / NewFactionCreated (player)
  └─ OfferQuests → handle_offer_quests            last month's offers off, this month's pinned → QuestsOffered
QuestAcceptView (the board's "Send men")
  └─ AcceptQuest → handle_accept_quest            offer off the board, contract signed → QuestAccepted
PlayerMonthPrepared (the month after)
  └─ BringQuestContractsHome → handle_bring_quest_contracts_home
       ├─ men still on the roster: outcome drawn → QuestContractReturned
       │    ├─ finance: handle_quest_silver   → CreateTransaction
       │    ├─ warrior: handle_quest_renown   → GrantRenown, per man
       │    ├─ item:    handle_quest_item     → CreateItem, into the stores
       │    ├─ faction: handle_quest_warrior  → RecruitWarriorFromQuest
       │    └─ month:   the chronicle line, every time
       └─ nobody left: QuestContractLapsed → the chronicle line
```

- **An offer lives for its month.** The next month's offer deletes whatever was not taken up. Not
  sending men is not an answer, and it leaves nothing behind.
- **The men are away for the month they are sent in.** `QuestContract.accepted_in_month` is the whole
  rule: `filter_sworn_to_a_quest` reads it, so the men are greyed in every picker ("Away on a quest this
  month"), are not mustered as defenders and cannot be dismissed. See
  [warrior availability](warrior-availability.md).
- **They come home on the next month turn, ahead of the salary run.** The renown fade and the training
  run in that same turn and ask about the month that ended, so both leave a man who was away alone: he is
  not idle, and he was not at the drill.
- **Only the men still on the roster share in it.** A man who walked out, was taken or died while away
  is left out; a quest whose men are all gone lapses with a line of its own.
- **Coming home is guarded once.** `QuestContract.objects.mark_resolved` is a conditional `UPDATE`, so a
  second month turn overlapping the first finds the contract resolved and pays nothing. Accepting is
  guarded the same way, by the filtered delete of the offer.

## Adding one

An entry is a class in `apps/warband/quest/quests/` plus a line in `QUESTS`:

| Constant | Says |
|---|---|
| `WEIGHT` | how likely against the other entries on its side of the offer |
| `TITLE`, `BODY` | what the board shows |
| `MIN_MEN`, `MAX_MEN` | the band it takes, both inclusive; the accept form refuses anything else |
| `LEANS_ON` | the warrior attribute the band is weighed on |
| `STAT_YARDSTICK` | the band's summed attribute at which the outcomes are as likely as written |
| `IS_STEADY_WORK` | see below |
| `OUTCOMES` | the ways it can come home, each a `QuestOutcome` |

**Balance numbers live on the class**, the way a building's and an incident's do. Nothing a handler
reads is written anywhere else.

**A magnitude is a constant, never a roll.** The variety is which outcome is drawn. An outcome pays per
man who came home (`silver_per_man`, `renown_per_man`) or once (`item_function` with its generator and
`item_quality_bonus`, `warrior_generator_class`).

## The draw

The band's summed `LEANS_ON` divided by `STAT_YARDSTICK` multiplies every **success**'s weight, capped at
`MAX_SUCCESS_FACTOR`. Failures keep the weight they are written with. So a good band makes a success
likelier and never makes failure impossible; a weak one makes a success rarer and never makes it
certain to fail unless its attribute is nothing at all.

Tests pin the draw (`random.choices`), not the dice.

## The offer

Each month offers `STEADY_WORK_OFFERED` steady-work quests and `ERRANDS_OFFERED` of everything else, drawn
separately and without repeats, from the entries `is_possible` for the faction (it has `MIN_MEN` living
men). Two draws rather than one pool, so steady work is on the board every month whatever else is.

**Steady work is the errand a war band short of silver can always send men on.** Harvest work, a
merchant's road. It pays silver on every outcome, little and reliably, and the pool's tests hold all
steady work to that. It is what a broke month does instead of nothing; it is not meant to cover a wage
bill, which is why it pays a fraction of one man's wage per man.

The board tags it **Steady work**, with a `title` saying it is there every month and pays even when it
goes badly.

The player's alone: a rival is offered nothing, like the incidents.

## What a quest does not do

- **It never injures or kills.** An injury never mends, and a quest that maims a man is a fight's
  business.
- **It pays no experience.** The experience and level-up chain records itself in a fight's battle
  history and report; a quest has neither.
- **It has no fyrd, morale ceiling or lost-gear lever.** No entry of the catalogue needs one, and a lever
  nothing pulls is a field and a handler the coverage gate has no case for. An entry that wants one adds
  the field on `QuestOutcome` and the handler in the owning topic, the way an incident's levers are built.

## What it is worth

At its yardstick a band draws the outcomes as written, so a steady-work quest's silver per man is its weighted
mean: about 29 for the harvest (`(3 × 35 + 1 × 10) / 4`) and 35 for the merchant's road
(`(3 × 45 + 1 × 5) / 4`). Against a Small Hall's 300 a month and a wage of 80–160 a man, one man sent pays
back a fifth to a third of what he costs: steady work softens a lean month, it does not carry one. The
errands pay in kind - renown, a blade above the shelf, a man the pub does not sell - and the man fetched
home draws a wage from the next month, which is what that errand costs.

## Tests that hold the catalogue

`apps/warband/quest/tests/quests/test_pool.py` reads the constants: every entry weighs something, takes
a band it can be sent, leans on a real attribute, can both succeed and fail, and every success brings
something home - no lever is ever negative, so that is what makes a quest's expected value positive.
All steady work pays silver on every outcome and has a positive expected silver per man at its yardstick,
and every title fits the log line.

## The register

The chronicle register of the [month incidents](month-incidents.md#the-register): a title as one
sentence of report, a body as one sentence that quietly undercuts it, no narrator commenting.

## See also

- [Month incidents](month-incidents.md) — the pattern the catalogue follows
- [Warrior availability](warrior-availability.md) — the rule that makes a man away
- [Measuring balance](measuring-balance.md) — the harness sends men on the steady work
