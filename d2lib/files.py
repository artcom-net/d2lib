import json
from io import SEEK_CUR

from d2lib.classes import CLASS_NAMES, CLS_NECROMANCER
from d2lib.errors import D2SFileParseError, ItemParseError, StashFileParseError
from d2lib.item import Item
from d2lib.items_storage import ItemsDataStorage
from d2lib.skills import SKILL_NAMES, SKILL_OFFSETS
from d2lib.utils import (
    ReverseBitReader,
    _BytesJSONEncoder,
    int_from_bbytes,
    int_from_lbytes,
    is_set_bit,
    obj_to_dict,
    read_null_term_bstr,
    to_dict_list,
)


class _D2File(object):
    """Base class for all file types."""

    _ITEMS_HEADER = 0x4A4D
    _items_data = ItemsDataStorage()

    def __init__(self, file_path):
        """Initializes an instance.

        :param file_path: Path to d2 file
        """
        self._reader = open(file_path, 'rb')

    def __del__(self):
        """Close fd if something went wrong."""
        if hasattr(self, '_reader') and not self._reader.closed:
            self._reader.close()

    def to_dict(self):
        """Dumps self to dictionary.

        :return: A dictionary with excluded private attributes such as _reader.
        :rtype: dict
        """
        raise NotImplementedError

    def to_json(self, *args, **kwargs):
        """Dumps self to JSON.

        :param args: Positional arguments for json.dumps
        :param kwargs: Keyword arguments for json.dumps
        :return: JSON string
        :rtype: str
        """
        kwargs['cls'] = _BytesJSONEncoder
        return json.dumps(self.to_dict(), *args, **kwargs)

    def _parse_items(self, skip_items_header=False):
        """Parses items.

        If skip_items_header is True then the header is skipped and a list of
        one item will be returned.

        :param skip_items_header: If True skips the header, defaults to False
        :type skip_items_header: bool
        :raises ItemParseError:
        :return: A list of item.Item instances
        :rtype: list
        """
        if skip_items_header:
            items_count = 1
        else:
            items_header = int_from_bbytes(self._reader.read(2))
            if items_header != self._ITEMS_HEADER:
                raise ItemParseError(
                    f'Invalid items header: 0x{items_header:04X}'
                )
            items_count = int_from_lbytes(self._reader.read(2))

        items = []

        while items_count:
            item = Item(self._reader)
            if item.location_id == Item.LOC_SOCKETED:
                socketed_item = items[-1]
                socket_attrs = None

                if socketed_item.itype == Item.T_WEAPON:
                    socket_attrs = self._items_data.get_weapon_sock_attrs(
                        item.code
                    )
                elif socketed_item.itype == Item.T_ARMOR:
                    socket_attrs = self._items_data.get_armor_sock_attrs(
                        item.code
                    )
                elif socketed_item.itype == Item.T_SHIELD:
                    socket_attrs = self._items_data.get_shield_sock_attrs(
                        item.code
                    )

                if socket_attrs is None:
                    # Item is a jewel.
                    if item.code == 'jew':
                        socketed_item.magic_attrs.extend(item.magic_attrs)
                        socketed_item.socketed_items.append(item)
                        continue
                    raise ItemParseError(f'Unknown item: {item.code}')

                for attr in socket_attrs:
                    attr_name = self._items_data.get_magic_attr(attr['id'])[
                        'name'
                    ]
                    socketed_item.magic_attrs.append(
                        attr_name.format(*attr['values'])
                    )
                socketed_item.socketed_items.append(item)

            else:
                if not item.is_simple and item.inserted_items_count:
                    items_count += item.inserted_items_count
                items.append(item)
            items_count -= 1

        return items


class D2SFile(_D2File):
    """Character save file (.d2s)."""

    _HEADER = 0xAA55AA55
    _SKILLS_HEADER = 0x6966
    _MERC_ITEMS_HEADER = 0x6A66
    _GOLEM_ITEM_HEADER = 0x6B66

    _ATTR_STRENGTH = 0
    _ATTR_ENERGY = 1
    _ATTR_DEXTERITY = 2
    _ATTR_VITALITY = 3
    _ATTR_UNUSED_STATS = 4
    _ATTR_UNUSED_SKILLS = 5
    _ATTR_CURRENT_HP = 6
    _ATTR_MAX_HP = 7
    _ATTR_CURRENT_MANA = 8
    _ATTR_MAX_MANA = 9
    _ATTR_CURRENT_STAMINA = 10
    _ATTR_MAX_STAMINA = 11
    _ATTR_LEVEL = 12
    _ATTR_EXPERIENCE = 13
    _ATTR_GOLD = 14
    _ATTR_STASHED_GOLD = 15

    _ATTRIBUTES = {
        _ATTR_STRENGTH: 'strength',
        _ATTR_ENERGY: 'energy',
        _ATTR_DEXTERITY: 'dexterity',
        _ATTR_VITALITY: 'vitality',
        _ATTR_UNUSED_STATS: 'unused_stats',
        _ATTR_UNUSED_SKILLS: 'unused_skills',
        _ATTR_CURRENT_HP: 'current_hp',
        _ATTR_MAX_HP: 'max_hp',
        _ATTR_CURRENT_MANA: 'current_mana',
        _ATTR_MAX_MANA: 'max_mana',
        _ATTR_CURRENT_STAMINA: 'current_stamina',
        _ATTR_MAX_STAMINA: 'max_stamina',
        _ATTR_LEVEL: 'level',
        _ATTR_EXPERIENCE: 'experience',
        _ATTR_GOLD: 'gold',
        _ATTR_STASHED_GOLD: 'stashed_gold',
    }

    _ATTRIBUTE_VALUE_SIZES = {
        _ATTR_STRENGTH: 10,
        _ATTR_ENERGY: 10,
        _ATTR_DEXTERITY: 10,
        _ATTR_VITALITY: 10,
        _ATTR_UNUSED_STATS: 10,
        _ATTR_UNUSED_SKILLS: 8,
        _ATTR_CURRENT_HP: 21,
        _ATTR_MAX_HP: 21,
        _ATTR_CURRENT_MANA: 21,
        _ATTR_MAX_MANA: 21,
        _ATTR_CURRENT_STAMINA: 21,
        _ATTR_MAX_STAMINA: 21,
        _ATTR_LEVEL: 7,
        _ATTR_EXPERIENCE: 32,
        _ATTR_GOLD: 25,
        _ATTR_STASHED_GOLD: 25,
    }

    def __init__(self, d2s_path):
        """Initializes an instance.

        :param d2s_path: Path to .d2s file
        :type d2s_path: str
        """
        self.char_status = None
        self.char_class_id = None
        self.char_name = None
        self.char_level = None
        self.last_played = None
        self.is_dead_merc = None
        self.merc_experience = None
        self.version = None
        self.file_size = None
        self.checksum = None
        self.active_weapon = None
        self.progression = None
        self.hot_keys = None
        self.lm_skill_id = None
        self.rm_skill_id = None
        self.slm_skill_id = None
        self.srm_skill_id = None
        self.char_appearance = None
        self.difficulty = None
        self.map_id = None
        self.merc_id = None
        self.merc_name_id = None
        self.merc_type = None
        self.quests = None
        self.waypoints = None
        self.npc_intro = None

        super(D2SFile, self).__init__(d2s_path)
        self._rbit_reader = ReverseBitReader(self._reader)

        self._parse_header()
        self.attributes = self._parse_attributes()
        self.skills = self._parse_skills()
        self.items = self._parse_items()
        self.corpse_items = self._parse_corpse_items()
        self.merc_items = None
        self.golem_item = None

        if self.is_expansion:
            self.merc_items = self._parse_merc_items()
            if self.char_class_id == CLS_NECROMANCER:
                self.golem_item = self._parse_golem_item()
        self._reader.close()

    @property
    def is_hardcore(self):
        """Checks if a character is in hardcore mode.

        :return: True if character is in hardcore mode otherwise False
        :rtype: bool
        """
        return is_set_bit(self.char_status, 2)

    @property
    def is_died(self):
        """Checks if a character is dead.

        :return: True if character is dead otherwise False
        :rtype: bool
        """
        return is_set_bit(self.char_status, 3)

    @property
    def is_expansion(self):
        """Checks if a character is an expansion character.

        :return: True if character is expansion otherwise False
        :rtype: bool
        """
        return is_set_bit(self.char_status, 5)

    @property
    def is_ladder(self):
        """Checks if a character is a ladder character.

        :return: True if character is ladder otherwise False
        :rtype: bool
        """
        return is_set_bit(self.char_status, 6)

    @property
    def char_class(self):
        """Gets the character class name by identifier.

        :return: Class name if identifier is valid otherwise None
        :rtype: str or None
        """
        return CLASS_NAMES.get(self.char_class_id)

    def to_dict(self):
        """See _D2File.to_dict.__doc__."""
        _dict = obj_to_dict(self, exclude=('_reader', '_rbit_reader'))
        _dict['char_class'] = self.char_class
        _dict['is_hardcore'] = self.is_hardcore
        _dict['is_died'] = self.is_died
        _dict['is_expansion'] = self.is_expansion
        _dict['is_ladder'] = self.is_ladder

        if self.items:
            _dict['items'] = to_dict_list(self.items)
        if self.corpse_items:
            _dict['corpse_items'] = to_dict_list(self.corpse_items)
        if self.merc_items:
            _dict['merc_items'] = to_dict_list(self.merc_items)
        if self.golem_item:
            _dict['golem_item'] = self.golem_item.to_dict()

        return _dict

    def _parse_header(self):
        """Parses a header that consists of 765 bytes.

        :raises D2SFileParseError:
        :return: None
        """
        header_id = int_from_lbytes(self._reader.read(4))
        if header_id != self._HEADER:
            raise D2SFileParseError(f'Invalid header id: 0x{header_id:08X}')
        self.version = int_from_lbytes(self._reader.read(4))
        self.file_size = int_from_lbytes(self._reader.read(4))
        self.checksum = int_from_lbytes(self._reader.read(4))
        self.active_weapon = int_from_lbytes(self._reader.read(4))
        self.char_name = self._reader.read(16).rstrip(b'\x00').decode('ASCII')
        self.char_status = int_from_lbytes(self._reader.read(1))
        self.progression = int_from_lbytes(self._reader.read(1))
        self._reader.seek(2, SEEK_CUR)
        self.char_class_id = int_from_lbytes(self._reader.read(1))
        self._reader.seek(2, SEEK_CUR)
        self.char_level = int_from_lbytes(self._reader.read(1))
        self._reader.seek(4, SEEK_CUR)
        self.last_played = int_from_lbytes(self._reader.read(4))
        self._reader.seek(4, SEEK_CUR)
        self.hot_keys = self._reader.read(64)
        self.lm_skill_id = int_from_lbytes(self._reader.read(4))
        self.rm_skill_id = int_from_lbytes(self._reader.read(4))
        self.slm_skill_id = int_from_lbytes(self._reader.read(4))
        self.srm_skill_id = int_from_lbytes(self._reader.read(4))
        self.char_appearance = self._reader.read(32)
        self.difficulty = self._reader.read(3)
        self.map_id = int_from_lbytes(self._reader.read(4))
        self._reader.seek(2, SEEK_CUR)
        self.is_dead_merc = bool(int_from_lbytes(self._reader.read(2)))
        self.merc_id = int_from_lbytes(self._reader.read(4))
        self.merc_name_id = int_from_lbytes(self._reader.read(2))
        self.merc_type = int_from_lbytes(self._reader.read(2))
        self.merc_experience = int_from_lbytes(self._reader.read(4))
        self._reader.seek(144, SEEK_CUR)
        self.quests = self._reader.read(298)
        self.waypoints = self._reader.read(81)
        self.npc_intro = self._reader.read(51)

    def _parse_attributes(self):
        """Parses character attributes.

        :raises D2SFileParseError:
        :return: Dictionary consisting of D2SFile._ATTRIBUTES
        :rtype: dict
        """
        self._reader.seek(2, SEEK_CUR)
        attributes = dict.fromkeys(self._ATTRIBUTES.values(), 0)
        while True:
            attr_id = self._rbit_reader.read(9)
            if attr_id == 0x1FF:
                break
            attr_value_size = self._ATTRIBUTE_VALUE_SIZES.get(attr_id)
            if attr_value_size is None:
                raise D2SFileParseError(f'Invalid attribute id: {attr_id}')
            value = self._rbit_reader.read(attr_value_size)
            if attr_id in (
                self._ATTR_CURRENT_HP,
                self._ATTR_MAX_HP,
                self._ATTR_CURRENT_MANA,
                self._ATTR_MAX_MANA,
                self._ATTR_CURRENT_STAMINA,
                self._ATTR_MAX_STAMINA,
            ):
                value /= 256
            attributes[self._ATTRIBUTES[attr_id]] = value
        return attributes

    def _parse_skills(self):
        """Parses character skills.

        :raises D2SFileParseError:
        :return: Dictionary consisting of skill_name: skill_points
        :rtype: dict
        """
        skill_header = int_from_bbytes(self._reader.read(2))
        if skill_header != self._SKILLS_HEADER:
            raise D2SFileParseError(
                f'Invalid skill header id: {skill_header:02X}'
            )
        skills = {}
        skill_offset = SKILL_OFFSETS.get(self.char_class_id)
        for index in range(30):
            skill_id = index + skill_offset
            skill_value = int_from_lbytes(self._reader.read(1))
            skills[SKILL_NAMES.get(skill_id)] = skill_value
        return skills

    def _parse_corpse_items(self):
        """Parses corpse items if character is dead.

        :return: A list of item.Item instances if the character is dead
        otherwise an empty list
        :rtype: list
        """
        corpse_items = []
        corpse_header = int_from_bbytes(self._reader.read(2))
        is_dead_char = bool(int_from_lbytes(self._reader.read(2)))
        if is_dead_char and corpse_header == self._ITEMS_HEADER:
            self._reader.seek(12, SEEK_CUR)
            corpse_items = self._parse_items()
        return corpse_items

    def _parse_merc_items(self):
        """Parses mercenary items if it exists.

        :return: A list of item.Item instances If the character has a mercenary
        otherwise an empty list
        :rtype: list
        """
        merc_items = []
        merc_item_header = int_from_bbytes(self._reader.read(2))
        if merc_item_header == self._MERC_ITEMS_HEADER and self.merc_id:
            merc_items = self._parse_items()
        return merc_items

    def _parse_golem_item(self):
        """Parses golem item if it exists.

        :return: An item from which the golem was created if the character is
        Necromancer and he has a golem otherwise None
        :rtype: item.Item or None
        """
        golem_item = None
        golem_header = int_from_bbytes(self._reader.read(2))
        has_golem = bool(int_from_lbytes(self._reader.read(1)))
        if has_golem and golem_header == self._GOLEM_ITEM_HEADER:
            golem_item = self._parse_items(skip_items_header=True)[0]
        return golem_item


class _PlugyStash(_D2File):
    """Base class for the PlugY files."""

    _HEADER = None
    _STASH_HEADER = 0x5453

    def __init__(self, stash_file_path):
        """Initializes an instance.

        :param stash_file_path: Path to stash file
        :type stash_file_path: str
        """
        super(_PlugyStash, self).__init__(stash_file_path)
        self.version = None
        self.page_count = None

        self._parse_header()
        self.stash = self._parse_stash_pages()
        self._reader.close()

    def to_dict(self):
        """See _D2File.to_dict.__doc__."""
        _dict = obj_to_dict(self, exclude=('_reader',))
        if self.stash:
            _dict['stash'] = [page.copy() for page in self.stash]
            for page in _dict['stash']:
                page['items'] = to_dict_list(page['items'])
        return _dict

    def _parse_header(self):
        """Parses the header. It has any type of stash file.

        :raises StashFileParseError:
        :return: None
        """
        header = int_from_lbytes(self._reader.read(4))
        if header != self._HEADER:
            raise StashFileParseError(f'Invalid header id: 0x{header:08X}')
        self.version = int_from_lbytes(self._reader.read(2))

    def _parse_stash_pages(self):
        """Parses page headers and items if page_count > 0.

        :raises StashFileParseError:
        :return: A list of dictionaries where each element is
        {'page': `int`, 'flags': `dict`, 'name': `str`, 'items': `list`} if
        page_count > 0 otherwise an empty list
        :rtype: list
        """
        pages = []
        for page in range(self.page_count):
            stash_header = int_from_lbytes(self._reader.read(2))
            if stash_header != self._STASH_HEADER:
                raise StashFileParseError(
                    f'Invalid stash header: 0x{stash_header:08X}'
                )
            flags = 0
            name = None
            data = int_from_bbytes(self._reader.read(2))
            if data != self._ITEMS_HEADER:
                _flags = data << 16 | int_from_bbytes(self._reader.read(2))
                flags = dict(
                    is_shared=bool((_flags >> 24) & 0b1),
                    is_index=bool((_flags >> 16) & 0b1),
                    is_main_index=bool((_flags >> 8) & 0b1),
                    is_reserved=bool(_flags & 0b1),
                )
                name = read_null_term_bstr(self._reader).decode()
            pages.append(
                dict(
                    page=page + 1,
                    flags=flags,
                    name=name,
                    items=self._parse_items(),
                )
            )
        return pages


class D2XFile(_PlugyStash):
    """PlugY personal stash file (.d2x)."""

    _HEADER = 0x4D545343
    _VERSION = 0x3130

    def _parse_header(self):
        """Parses the header.

        :raises StashFileParseError:
        :return: None
        """
        super(D2XFile, self)._parse_header()
        if self.version != self._VERSION:
            raise StashFileParseError(f'Invalid version: {self.version:04X}')
        self._reader.seek(4, SEEK_CUR)
        self.page_count = int_from_lbytes(self._reader.read(4))


class SSSFile(_PlugyStash):
    """PlugY shared stash file (.sss)."""

    _HEADER = 0x535353
    _VERSION_1 = 0x3130
    _VERSION_2 = 0x3230

    def __init__(self, d2sss_path):
        """Initializes an instance.

        :param d2sss_path: Path to .sss file
        :type d2sss_path: str
        """
        self.shared_gold = None
        super(SSSFile, self).__init__(d2sss_path)

    def _parse_header(self):
        """Parses the header.

        :raises StashFileParseError:
        :return: None
        """
        super(SSSFile, self)._parse_header()
        if self.version == self._VERSION_1:
            self.page_count = int_from_lbytes(self._reader.read(4))
        elif self.version == self._VERSION_2:
            self.shared_gold = int_from_lbytes(self._reader.read(4))
            self.page_count = int_from_lbytes(self._reader.read(4))
        else:
            raise StashFileParseError(f'Invalid version: {self.version:04X}')
