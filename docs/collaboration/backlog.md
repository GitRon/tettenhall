# Backlog

Open ideas and unfinished work, kept in German as written.

A line leaves this file the moment it becomes an issue — the issue is the record, and an idea kept in
both places drifts. See [writing an issue](writing-issues.md) for what promoting a line involves.

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
