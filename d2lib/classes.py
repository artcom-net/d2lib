from enum import IntEnum


class CharacterClass(IntEnum):  # NOQA
    AMAZON = 0
    SORCERESS = 1
    NECROMANCER = 2
    PALADIN = 3
    BARBARIAN = 4
    DRUID = 5
    ASSASSIN = 6

    def __str__(self):
        return self.name.capitalize()
