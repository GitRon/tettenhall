# Tettenhall

## MVP

### Dashboard / Generelles

* "Look for trouble" zu Liste von verschieden schweren Quests umbauen, die man annehmen kann (und Warriors zuweisen)
* Savegame-Logik von Sovereignty kopieren
* Gefangen müssen sich auch heilen am Wochenende
* Events, die Einfluss auf Krieger oder sonstiges haben (Max HP ändert etc.)

### Faction

* Geld berechnen
* Umgang mit "pleite" sein
* Items kaufen und verkaufen (per Command im View)
* Sklaven / Gefangene als Sklaven verkaufen oder rekrutieren

### Warrior

* Level & Erfahrungspunkte haben noch keinen Einfluss
* Nicknames, je nachdem wie die Attribute ausfallen (Collum the Weak, Charles the Quick)
* Training: 
  * Wie mach ich das? Trainiert man Dinge, die dann Bonus auf Fähigkeiten geben?
  * Pro Skill (Stärke, Dex, HP, Moral) ein Fortschrittsbalken?
  * Was tut dann XP? Macht es einfach den Kämpfer besser bei den Attacken und Verteidigen?
  * Oder kann man damit nur XP sammeln?
  * Was ist, wenn ich das Training allgemein und nicht pro Krieger definiere? Und jeder, 
    der nicht kämpft und gesund ist, das gleiche macht.

### Skirmish

* Passive/defensiv-stärkende Attack-Action?
* Fliehen als Aktion
* Gegner-KI für Kampfaktionen
* Kampfaktion soll an Item hängen, Warrior bekommt eine Funktion, die entscheidet, was es im Select zu sehen gibt
* Morph swap htmx Fabi damit Formulare sich nicht ändern → gewählte Action springt immer zurück

### Technisches

* Logging der Event-Queue

## Konzeptionelles

* Entity component system (Rustroguelike) -> Tipp von Andi

### Quellen

* Icons: game-icons.net
