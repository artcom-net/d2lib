from enum import IntEnum
from io import BufferedReader

from d2lib._utils import (
    ReverseBitReader,
    calc_bits_to_align,
    obj_to_dict,
    to_dict_list,
)
from d2lib.classes import CharacterClass
from d2lib.errors import ItemParseError
from d2lib.items_storage import ItemsDataStorage
from d2lib.skills import SKILLS_TREE_NAMES, SKILLS_TREE_OFFSETS, Skill


class ItemLocation(IntEnum):  # noqa: D101
    STORED = 0
    EQUIPPED = 1
    BELT = 2
    CURSOR = 4
    SOCKETED = 6


class ItemEquippedLocation(IntEnum):  # noqa: D101
    NONE = 0
    HEAD = 1
    NECK = 2
    TORSO = 3
    HAND_RIGHT = 4
    HAND_LEFT = 5
    FINGER_RIGHT = 6
    FINGER_LEFT = 7
    WAIST = 8
    FEET = 9
    HANDS = 10
    ALT_HAND_RIGHT = 11
    ALT_HAND_LEFT = 12


class ItemPanel(IntEnum):  # noqa: D101
    NONE = 0
    INVENTORY = 1
    CUBE = 4
    STASH = 5


class ItemQuality(IntEnum):  # noqa: D101
    LOW = 1
    NORMAL = 2
    HIGH = 3
    MAGIC = 4
    SET = 5
    RARE = 6
    UNIQUE = 7
    CRAFTED = 8


class ItemLowQualityType(IntEnum):  # noqa: D101
    CRUDE = 0
    CRACKED = 1
    DAMAGED = 2
    LOW = 3


class ItemType(IntEnum):  # noqa: D101
    ARMOR = 0
    SHIELD = 1
    WEAPON = 2
    MISC = 3


class ReanimateType(IntEnum):  # noqa: D101
    SKELETON = 0
    RETURNED = 1
    BONEWARIOR = 2
    BURNINGDEAD = 3
    HORROR = 4
    ZOMBIE = 5
    HUNGRYDEAD = 6
    GHOUL = 7

    def __str__(self):
        return self.name.capitalize()


class Item(object):
    """This class represents any item in the game."""

    _HEADER = 0x4D4A
    _SET_EXTRA_COUNTS = {
        0: 0,
        1: 1,
        2: 1,
        3: 2,
        4: 1,
        6: 2,
        7: 3,
        10: 2,
        12: 2,
        15: 4,
        31: 5,
    }

    _items_data = ItemsDataStorage()

    def __init__(self):  # noqa: D107
        # Simple
        self.is_identified = None
        self.is_socketed = None
        self.is_new = None
        self.is_ear = None
        self.is_start_item = None
        self.is_simple = None
        self.is_ethereal = None
        self.is_personalized = None
        self.is_runeword = None
        self.location = None
        self.equipped = None
        self.pos_x = None
        self.pos_y = None
        self.panel = None
        self.ear_char_class = None
        self.ear_char_level = None
        self.ear_char_name = None
        self.inserted_items_count = None
        self.version = None
        self.code = None

        # Advanced
        self.level = None
        self.has_multiple_pic = None
        self.is_class_specific = None
        self.pic_id = None
        self.low_quality_type = None
        self.personalized_name = None
        self.defense_rating = None
        self.max_durability = None
        self.cur_durability = None
        self.quantity = None
        self.socket_count = None
        self.magic_attrs = None
        self.set_extra_attrs = None
        self.set_req_items_count = None
        self.socketed_items = None
        self.iid = None
        self.quality = None
        self.magic_prefix_id = None
        self.magic_suffix_id = None
        self.set_id = None
        self.rare_fname_id = None
        self.rare_sname_id = None
        self.rare_affixes = None
        self.unique_id = None
        self.runeword_id = None
        self.timestamp = None
        self.is_quantitative = None

        # Extra
        self.itype = None
        self.base_name = None

        self._reader = None

    def __str__(self):
        return f'{self.__class__.__name__}({self.code}: {self.name})'

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_stream(cls, stream):
        """Construct an object from a stream.

        :type stream: io.BufferedReader
        :raises:
            ValueError: if the stream is not a BufferedReader.
            ItemParseError: if an error occurred while parsing the structure.
        :rtype: Item
        """
        if not isinstance(stream, BufferedReader):
            raise ValueError(f'Invalid stream type: {type(stream)}')
        instance = cls()
        instance._reader = ReverseBitReader(stream)
        instance._parse_simple()
        if not instance.is_simple:
            instance._parse_advanced()
        instance._align_byte()
        return instance

    @classmethod
    def from_file(cls, file_path):
        """Construct an object from a file.

        :type file_path: str
        :raises:
            FileNotFoundError: file_path doesn't exist.
            PermissionError: no access rights to the file.
            ItemParseError:  if an error occurred while parsing the structure.
        :rtype: Item
        """
        with open(file_path, 'rb') as item_file:
            instance = cls.from_stream(item_file)
            instance._reader = None
            return instance

    @property
    def name(self):
        """Get the special name for the item.

        If the item is not misc or simple then it has a special name otherwise
        only the base name.

        :return: Special name or base name
        :rtype: str
        """
        if self.quality is ItemQuality.MAGIC:
            return self._items_data.get_magic_name(
                self.magic_prefix_id, self.magic_suffix_id
            )
        elif self.quality is ItemQuality.RARE:
            return self._items_data.get_rare_name(
                self.rare_fname_id, self.rare_sname_id
            )
        elif self.quality is ItemQuality.SET:
            return self._items_data.get_set_name(self.set_id)
        elif self.quality is ItemQuality.UNIQUE:
            return self._items_data.get_unique_name(self.unique_id)
        elif self.is_runeword:
            return self._items_data.get_runeword_name(self.runeword_id)
        return self.base_name

    def to_dict(self):
        """Dump self to dictionary.

        :return: A dictionary with excluded private attributes such as _reader.
        :rtype: dict
        """
        item_dict = obj_to_dict(self, exclude=('_reader',))
        if self.socketed_items:
            item_dict['socketed_items'] = to_dict_list(self.socketed_items)
        item_dict['name'] = self.name
        return item_dict

    def _align_byte(self):
        """Align stream by byte boundary.

        :return: None
        """
        self._reader.read(calc_bits_to_align(self._reader.bits_total))

    def _parse_simple(self):
        """Parse attributes that have all items.

        :raises ItemParseError:
        :return: None
        """
        header_id = self._reader.read(16)
        if header_id != self._HEADER:
            raise ItemParseError(f'Invalid item header id: {header_id:04X}')
        self._reader.read(4)
        self.is_identified = bool(self._reader.read(1))
        self._reader.read(6)
        self.is_socketed = bool(self._reader.read(1))
        self._reader.read(1)
        # is_new - picked up since the last time the game was saved.
        self.is_new = bool(self._reader.read(1))
        self._reader.read(2)
        self.is_ear = bool(self._reader.read(1))
        self.is_start_item = bool(self._reader.read(1))
        self._reader.read(3)
        # is_simple - only contains 111 bits of data.
        self.is_simple = bool(self._reader.read(1))
        self.is_ethereal = bool(self._reader.read(1))
        self._reader.read(1)
        self.is_personalized = bool(self._reader.read(1))
        self._reader.read(1)
        self.is_runeword = bool(self._reader.read(1))
        self._reader.read(5)
        self.version = self._reader.read(8)
        self._reader.read(2)
        self.location = ItemLocation(self._reader.read(3))
        self.equipped = ItemEquippedLocation(self._reader.read(4))
        self.pos_x = self._reader.read(4)
        self.pos_y = self._reader.read(3)
        self._reader.read(1)
        self.panel = ItemPanel(self._reader.read(3))

        if self.is_ear:
            self.code = 'ear'
            self.base_name = self._items_data.get_misc_name(self.code)
            self.ear_char_class = CharacterClass(self._reader.read(3))
            self.ear_char_level = self._reader.read(7)
            self.ear_char_name = self._reader.read_null_term_bstr(7).decode()
        else:
            self.code = ''.join(
                chr(self._reader.read(8)) for _ in range(4)
            ).rstrip()

            if self._items_data.is_armor(self.code):
                self.itype = ItemType.ARMOR
                self.base_name = self._items_data.get_armor_name(self.code)
            elif self._items_data.is_shield(self.code):
                self.itype = ItemType.SHIELD
                self.base_name = self._items_data.get_shield_name(self.code)
            elif self._items_data.is_weapon(self.code):
                self.itype = ItemType.WEAPON
                self.base_name = self._items_data.get_weapon_name(self.code)
            else:
                self.itype = ItemType.MISC
                self.base_name = self._items_data.get_misc_name(self.code)

            self.is_quantitative = self._items_data.is_quantitative(self.code)
            self.inserted_items_count = self._reader.read(3)

            if self.inserted_items_count > 0:
                self.socketed_items = []

    @staticmethod
    def _calculate_poison_damage(damage, duration):
        """Calculate the value of poison damage.

        The divisor 10.24 is selected through long tests and there may be
        differences with the values in the game.

        :type damage: int
        :type duration: int
        :rtype: int
        """
        return round((damage / 10.24) * duration)

    def _parse_magic_attrs(self):
        """Parse magic attributes.

        If the attribute does not make sense, then it is ignored, for example:
        the visual effect.

        :raises ItemParseError:
        :return: A list of string
        :rtype: list
        """
        magic_attrs_list = []
        while True:
            magic_attr_id = self._reader.read(9)
            if magic_attr_id == 0x1FF:
                break
            attr_dict = self._items_data.get_magic_attr(magic_attr_id)
            if not attr_dict:
                raise ItemParseError(
                    f'Unknown magic attribute id: {magic_attr_id}'
                )
            bias = attr_dict.get('bias', 0)
            values = [
                self._reader.read(bits) - bias for bits in attr_dict['bits']
            ]

            if attr_dict.get('is_invisible', False):
                continue

            # TODO: refactor me.
            # TODO: maybe need to transfer attribute data to Python code.
            if magic_attr_id == 57:  # x poison damage over y seconds
                tmp_min_damage, tmp_max_damage, duration = values
                duration = round(duration / 25)
                min_damage = self._calculate_poison_damage(
                    tmp_min_damage, duration
                )
                attr_str_value = attr_dict['name']
                if tmp_min_damage != tmp_max_damage:
                    max_damage = self._calculate_poison_damage(
                        tmp_max_damage, duration
                    )
                    attr_str_value = attr_str_value.format(
                        f'Adds {min_damage}-{max_damage}', duration
                    )
                else:
                    attr_str_value = attr_str_value.format(
                        f'+{min_damage}', duration
                    )
                magic_attrs_list.append(attr_str_value)
                continue
            elif magic_attr_id in (83, 84):
                values[0] = str(CharacterClass(values[0]))
            elif magic_attr_id in (97, 107, 109, *range(181, 188)):
                values[0] = str(Skill(values[0]))
            elif magic_attr_id == 155:  # x% reanimate as: y
                values[0] = str(ReanimateType(values[0]))
            elif magic_attr_id == 188:
                char_class = CharacterClass(values[1])
                values[0] = SKILLS_TREE_NAMES.get(
                    SKILLS_TREE_OFFSETS[char_class] + values[0]
                )
                values[1] = str(char_class)
            elif magic_attr_id in range(195, 214):
                values[1] = str(Skill(values[1]))
            # 214-250 - based on char level (value * 0.125)% per level).
            magic_attrs_list.append(attr_dict['name'].format(*values))

        return magic_attrs_list

    # TODO: refactor me
    def _parse_advanced(self):
        """Parse advanced attributes.

        If item is not simple, then it has additional attributes.

        :return: None
        """
        self.iid = self._reader.read(32)
        self.level = self._reader.read(7)
        self.quality = ItemQuality(self._reader.read(4))

        self.has_multiple_pic = bool(self._reader.read(1))
        if self.has_multiple_pic:
            self.pic_id = self._reader.read(3)

        self.is_class_specific = bool(self._reader.read(1))
        if self.is_class_specific:
            self._reader.read(11)

        if self.quality is ItemQuality.LOW:
            self.low_quality_type = ItemLowQualityType(self._reader.read(3))
        elif self.quality is ItemQuality.HIGH:
            self._reader.read(3)
        elif self.quality is ItemQuality.MAGIC:
            self.magic_prefix_id = self._reader.read(11)
            self.magic_suffix_id = self._reader.read(11)
        elif self.quality is ItemQuality.SET:
            self.set_id = self._reader.read(12)
        elif self.quality in (ItemQuality.RARE, ItemQuality.CRAFTED):
            self.rare_fname_id = self._reader.read(8)
            self.rare_sname_id = self._reader.read(8)
            self.rare_affixes = []
            for _ in range(6):
                if self._reader.read(1):
                    self.rare_affixes.append(self._reader.read(11))
        elif self.quality is ItemQuality.UNIQUE:
            self.unique_id = self._reader.read(12)

        if self.is_runeword:
            self.runeword_id = self._reader.read(12)
            self._reader.read(4)

        if self.is_personalized:
            self.personalized_name = self._reader.read_null_term_bstr(7)

        # Item is the Tome of portal/identify.
        if self.code in ('tbk', 'ibk'):
            self._reader.read(5)

        self.timestamp = self._reader.read(1)

        if self.itype in (ItemType.ARMOR, ItemType.SHIELD):
            self.defense_rating = self._reader.read(11) - 10
        if self.itype in (ItemType.ARMOR, ItemType.SHIELD, ItemType.WEAPON):
            self.max_durability = self._reader.read(8)
            if self.max_durability > 0:
                self.cur_durability = self._reader.read(8)
                self._reader.read(1)

        if self.is_quantitative:
            self.quantity = self._reader.read(9)

        if self.is_socketed:
            self.socket_count = self._reader.read(4)

        extra_set_id = None
        set_extra_count = None

        if self.quality is ItemQuality.SET:
            extra_set_id = self._reader.read(5)
            set_extra_count = self._SET_EXTRA_COUNTS.get(extra_set_id)

        self.magic_attrs = self._parse_magic_attrs()

        if set_extra_count:
            self.set_extra_attrs = []
            for _ in range(set_extra_count):
                self.set_extra_attrs.append(self._parse_magic_attrs()[0])

            # Item is not the Civerb's Ward.
            if self.set_id != 0:
                self.set_req_items_count = []
                for offset in range(5):
                    if (extra_set_id & (1 << offset)) == 0:
                        continue
                    self.set_req_items_count.append(offset + 2)

        if self.is_runeword:
            self.magic_attrs.extend(self._parse_magic_attrs())
