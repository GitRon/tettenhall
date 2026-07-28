# Backlog

Open ideas and unfinished work, kept in German as written.

## MVP

### Dashboard / Generelles

* Gefangen müssen sich auch heilen am Wochenende
* Events, die Einfluss auf Krieger oder sonstiges haben (Max HP ändert etc.)
    * Event-Klasse, die man wie die Notifications registriert und die eine Wahrscheinlichkeit und einen Trigger haben,
      wenn beides passt, wird es ausgeführt. So kann man super fix neue Events dazu bauen

### Faction

* Umgang mit "pleite" sein
* Items kaufen und verkaufen (per Command im View)

### Warrior

* Level & Erfahrungspunkte haben noch keinen Einfluss
* Nicknames, je nachdem wie die Attribute ausfallen (Collum the Weak, Charles the Quick)
* Training:
    * Wie mache ich das? Trainiert man Dinge, die dann Bonus auf Fähigkeiten geben?
    * Pro Skill (Stärke, Dex, HP, Moral) ein Fortschrittsbalken?
    * Was tut dann XP? Macht es einfach den Kämpfer besser bei den Attacken und Verteidigen?
    * Oder kann man damit nur XP sammeln?
    * Was ist, wenn ich das Training allgemein und nicht pro Krieger definiere? Und jeder,
      der nicht kämpft und gesund ist, das gleiche macht.

### Training

* Trainingsart auswählen und im Savegame hinterlegen
* In der Woche Progress für alle Teilnehmer hinterlegen inkl. Punkt-Updates

### Skirmish

* Passive/defensiv-stärkende Attack-Action?
* Fliehen als Aktion
* Gegner-KI für Kampfaktionen
* Kampfaktion soll an Item hängen, Warrior bekommt eine Funktion, die entscheidet, was es im Select zu sehen gibt
* Morph swap htmx Fabi damit Formulare sich nicht ändern → gewählte Action springt immer zurück
* Permanente Verletzungen

### Technisches

* Logging der Event-Queue

## Konzeptionelles

* Entity component system (Rustroguelike) -> Tipp von Andi

## Offene Punkte aus den Building-Effekten

* Rivalen bauen nie — jeder Gebäude-Effekt ist reine Spieler-Progression, siehe
  [town buildings](../patterns/town-buildings.md)
* Marktplatz und Sanctuary haben je nur einen Effekt, der Weaponsmith-Bonus ist die einzige Quelle für
  besseres Gear
* Item-Preise (~30–150 Silber) liegen eine Größenordnung unter den Baukosten, dadurch ist die
  Wiederverkaufsquote des Marktplatzes wirtschaftlich kaum spürbar
* Kriegersold (`recruitment_price * 0.5`, ~150/Monat) ist der größte frühe Kostenblock und wurde beim
  Rebalancing nicht angepasst
