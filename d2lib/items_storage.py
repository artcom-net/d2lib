import json
from pathlib import Path

from d2lib.utils import stripped_string_concat


class ItemsDataStorage(object):
    """This class is a singleton.

    It is an interface to attributes of items and their properties.
    """

    _ITEMS_DATA_DIR = 'items_data'

    def __new__(cls):
        """Making the singleton class."""
        if not hasattr(cls, '_instance'):
            cls._instance = super(ItemsDataStorage, cls).__new__(cls)
            cls._instance._init_storage()
        return cls._instance

    def _init_storage(self):
        """Reads files with data about items.

        :raises ValueError:
        :return: None
        """
        self._armors = None
        self._shields = None
        self._weapons = None
        self._misc = None
        self._quantitative = None
        self._magic_attrs = None
        self._magic_prefixes = None
        self._magic_suffixes = None
        self._rare = None
        self._set = None
        self._unique = None
        self._runewords = None
        self._armor_sock_attrs = None
        self._shield_sock_attrs = None
        self._weapon_sock_attrs = None

        data_dir = Path(__file__).parent.joinpath(self._ITEMS_DATA_DIR)

        for file_path in data_dir.iterdir():
            file_name = file_path.stem
            attr_name = f'_{file_name}'

            if not hasattr(self, attr_name):
                raise ValueError(f'Unknown data file: {file_name}')

            with file_path.open('r') as data_file:
                data = json.load(data_file)
                _data = None
                if isinstance(data, dict):
                    key, value = data.popitem()
                    if isinstance(key, str) and key.isdecimal():
                        _data = {int(k): v for k, v in data.items()}
                        _data[int(key)] = value
                    else:
                        data[key] = value
                setattr(self, attr_name, _data or data)

    def is_armor(self, code):
        """Checks if the code is an armor code.

        :param code: Armor code
        :type code: str
        :return: True if the code is an armor otherwise False
        :rtype: bool
        """
        return code in self._armors

    def is_shield(self, code):
        """Checks if the code is a shield code.

        :param code: Shield code
        :type code: str
        :return: True if the code is a shield otherwise False
        :rtype: bool
        """
        return code in self._shields

    def is_weapon(self, code):
        """Checks if the code is a weapon code.

        :param code: Weapon code
        :type code: str
        :return: True if the code is a weapon otherwise False
        :rtype: bool
        """
        return code in self._weapons

    def is_misc(self, code):
        """Checks if the code is a misc code.

        :param code: Misc code
        :type code: str
        :return: True if the code is a misc otherwise False
        :rtype: bool
        """
        return code in self._misc

    def is_quantitative(self, code):
        """Checks if the code is a quantitative code.

        :param code: Quantitative code
        :type code: str
        :return: True if the code is a quantitative otherwise False
        :rtype: bool
        """
        return code in self._quantitative

    def get_armor_name(self, code):
        """Gets the name of the armor by code.

        :param code: Armor code
        :type code: str
        :return: Armor name
        :rtype: str
        """
        return self._armors.get(code)

    def get_shield_name(self, code):
        """Gets the name of the shield by code.

        :param code: Shield code
        :type code: str
        :return: Shield name
        :rtype: str
        """
        return self._shields.get(code)

    def get_weapon_name(self, code):
        """Gets the name of the weapon by code.

        :param code: Weapon code
        :type code: str
        :return: Weapon name
        :rtype: str
        """
        return self._weapons.get(code)

    def get_misc_name(self, code):
        """Gets the name of the misc by code.

        :param code: Misc code
        :type code: str
        :return: Misc name
        :rtype: str
        """
        return self._misc.get(code)

    def get_magic_attr(self, attr_id):
        """Gets the magic attribute by id.

        :param attr_id: Magic attribute identifier
        :type attr_id: int
        :return: Dictionary describing attribute
        :rtype: dict
        """
        return self._magic_attrs.get(attr_id)

    def get_magic_name(self, prefix_id, suffix_id):
        """Makes the full magic name consisting of a prefix and a suffix.

        :param prefix_id: Magic prefix identifier
        :type prefix_id: int
        :param suffix_id: Magic suffix identifier
        :type suffix_id: int
        :return: Full magic name if the prefix_id and suffix_id are valid
        otherwise an empty string
        :rtype: str
        """
        return stripped_string_concat(
            self._magic_prefixes.get(prefix_id, ''),
            self._magic_suffixes.get(suffix_id, ''),
        )

    def get_rare_name(self, fname_id, sname_id):
        """Makes the full rare name consisting of a fname and a sname.

        :param fname_id: First rare name identifier
        :type fname_id: int
        :param sname_id: Second rare name identifier
        :type sname_id: int
        :return: Full rare name if the fname_id and sname_id are valid
        otherwise an empty string
        :rtype: str
        """
        return stripped_string_concat(
            self._rare.get(fname_id, ''), self._rare.get(sname_id, '')
        )

    def get_set_name(self, set_id):
        """Gets the set's item name by id.

        :param set_id: Set's item identifier
        :type set_id: int
        :return: Set's name if set_id are valid otherwise None
        :rtype: str or None
        """
        return self._set.get(set_id)

    def get_unique_name(self, unique_id):
        """Gets the unique item name by id.

        :param unique_id: Unique item identifier
        :type unique_id: int
        :return: Unique item name if unique_id are valid otherwise None
        :rtype: str or None
        """
        return self._unique.get(unique_id)

    def get_runeword_name(self, runeword_id):
        """Gets the runeword name by id.

        :param runeword_id: Runeword identifier
        :type runeword_id: int
        :return: Runeword name if runeword_id are valid otherwise None
        :rtype: str or None
        """
        return self._runewords.get(runeword_id)

    def get_armor_sock_attrs(self, code):
        """Gets the attributes of an item inserted in armor.

        :param code: Item code
        :type code: str
        :return: Dictionary if the item is an insertable otherwise None.
        The dictionary consists of the following fields:
        {'id': `int`, 'values': `list`} where `id` is magic attribute id
        :rtype: dict or None
        """
        return self._armor_sock_attrs.get(code)

    def get_shield_sock_attrs(self, code):
        """Gets the attributes of an item inserted in shield.

        :param code: Item code
        :type code: str
        :return: Dictionary if the item is an insertable otherwise None.
        The dictionary consists of the following fields:
        {'id': `int`, 'values': `list`} where `id` is magic attribute id
        :rtype: dict or None
        """
        return self._shield_sock_attrs.get(code)

    def get_weapon_sock_attrs(self, code):
        """Gets the attributes of an item inserted in weapon.

        :param code: Item code
        :type code: str
        :return: Dictionary if the item is an insertable otherwise None.
        The dictionary consists of the following fields:
        {'id': `int`, 'values': `list`} where `id` is magic attribute id
        :rtype: dict or None
        """
        return self._weapon_sock_attrs.get(code)
