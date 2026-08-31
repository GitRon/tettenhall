# Backlog

Open ideas and unfinished work, kept in German as written.

A line leaves this file the moment it becomes an issue — the issue is the record, and an idea kept in
both places drifts. See [writing an issue](writing-issues.md) for what promoting a line involves.

## MVP

### Warrior

* Training:
    * Wie mache ich das? Trainiert man Dinge, die dann Bonus auf Fähigkeiten geben?
    * Pro Skill (Stärke, Dex, HP, Moral) ein Fortschrittsbalken?
    * Was tut dann XP? Macht es einfach den Kämpfer besser bei den Attacken und Verteidigen?
    * Oder kann man damit nur XP sammeln?
    * Was ist, wenn ich das Training allgemein und nicht pro Krieger definiere? Und jeder,
      der nicht kämpft und gesund ist, das gleiche macht.

### Technisches

* Logging der Event-Queue

## V1

### Skirmish

* Attacke, die den Gegner eher kampfunfähig schlägt als ihn zu töten
    * Also gezielt auf `CONDITION_UNCONSCIOUS` statt `CONDITION_DEAD` — ein bewusstloser Gegner ist
      Beute, ein toter nicht
* Soll der Verteidiger zurückschlagen dürfen, nachdem der Angreifer getroffen hat?
    * Evtl. als eigene Aktion für höhere Level, wie in Battle Brothers
    * Beides wären neue Einträge in `SkirmishActionChoices` samt eigenem Action-Service. #52 regelt
      nur, welche Aktionen ein Krieger davon *hat*, nicht welche es gibt

### Town

* Trainingsplatz als Gebäude -> schnelleres Lernen
    * Wäre der fünfte Hebel neben Halle, Weaponsmith, Marktplatz und Sanctuary, und der erste, der
      auf das Training wirkt

## Konzeptionelles

* Entity component system (Rustroguelike) -> Tipp von Andi

## Offene Punkte aus den Building-Effekten

* Marktplatz und Sanctuary haben je nur einen Effekt, der Weaponsmith-Bonus ist die einzige Quelle für
  besseres Gear
* Item-Preise (~30–150 Silber) liegen eine Größenordnung unter den Baukosten, dadurch ist die
  Wiederverkaufsquote des Marktplatzes wirtschaftlich kaum spürbar
* Kriegersold (`recruitment_price * 0.5`, ~150/Monat) ist der größte frühe Kostenblock und wurde beim
  Rebalancing nicht angepasst
