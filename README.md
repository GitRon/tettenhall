# Tettenhall

## DDD-Fragen

* Wie teile ich Skirmish auf? Ein Handler oder ganz viele Events?
* Loot/Items wäre dann eine eigene App? Nein, weil es ja Verben sein sollen...? Aber "allocation" ist es auch nicht...
* Halte ich Daten wie z.B. wer gestorben ist, Loot etc. im Speicher? Einfach immer weiter die Events rumschicken? Ich
  sollte das ja zu Ende rechnen, bevor ich was persistiere, aber wann weiß ich, dass jetzt der richtige Moment ist?
  Feuer ich Event "alle ko"?
* Wann persistiere ich etwas? zB "Item bekommen"?
* Was genau tut das UoW?
* Was wäre ein gutes Event? "Gegner tot"?
* Wo würde ich die Kampflogik ablegen? Eine Handler-Klasse? Gegner ziehen, wann ist einer "raus", Gegnerlisten
  reduzieren
* Kein Plan, was eine Aggregation wäre in dem Fall... 2 Warrior-Listen und Items als Skirmish?