from faker import Faker


class Faction:
    name: str
    locale: str

    def __init__(self, locale: str) -> None:
        self.locale = locale
        self.name = self.generate_name()

    def __str__(self):
        return self.name

    def generate_name(self):
        faker = Faker(locale=self.locale)
        return faker.city()
