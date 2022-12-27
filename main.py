import itertools

from apps.skirmish.domain.model.faction import Faction
from apps.skirmish.domain.model.warrior import Warrior
from apps.skirmish.services.fight import FightService

# Press the green button in the gutter to run the script.
if __name__ == "__main__":

    english_faction = Faction(locale="en_UK")
    danish_faction = Faction(locale="da_DK")

    warrior_list_1 = []
    for _ in itertools.repeat(None, 5):
        warrior_list_1.append(Warrior(faction=english_faction))

    warrior_list_2 = []
    for _ in itertools.repeat(None, 5):
        warrior_list_2.append(Warrior(faction=danish_faction))

    service = FightService(party_1=warrior_list_1, party_2=warrior_list_2)
    service.process()
