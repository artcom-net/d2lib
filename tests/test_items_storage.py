import pytest

from d2lib.items_storage import ItemsDataStorage


@pytest.fixture(scope='module')
def items_data():
    return ItemsDataStorage()


@pytest.fixture(scope='module')
def items_data2():
    return ItemsDataStorage()


def test_items_data_storage_singletone(items_data, items_data2):
    assert items_data is items_data2


@pytest.mark.parametrize(
    'field,field_type,key_type',
    (
        ('_armors', dict, str),
        ('_shields', dict, str),
        ('_weapons', dict, str),
        ('_misc', dict, str),
        ('_quantitative', list, None),
        ('_magic_attrs', dict, int),
        ('_magic_prefixes', dict, int),
        ('_magic_suffixes', dict, int),
        ('_rare', dict, int),
        ('_set', dict, int),
        ('_unique', dict, int),
        ('_runewords', dict, int),
        ('_armor_sock_attrs', dict, str),
        ('_shield_sock_attrs', dict, str),
        ('_weapon_sock_attrs', dict, str),
    ),
)
def test_items_data_storage(items_data, field, field_type, key_type):
    attr_value = getattr(items_data, field)
    assert attr_value
    assert isinstance(attr_value, field_type)
    if field_type is dict:
        assert all(isinstance(key, key_type) for key in attr_value.keys())


@pytest.mark.parametrize(
    'code,expected', (('', False), ('dr6', True), ('uow', False))
)
def test_items_data_storage_is_armor(items_data, code, expected):
    assert items_data.is_armor(code) is expected


@pytest.mark.parametrize(
    'code,expected', (('', False), ('uow', True), ('dr6', False))
)
def test_items_data_storage_is_shield(items_data, code, expected):
    assert items_data.is_shield(code) is expected


@pytest.mark.parametrize(
    'code,expected', (('', False), ('9gi', True), ('dr6', False))
)
def test_items_data_storage_is_weapon(items_data, code, expected):
    assert items_data.is_weapon(code) is expected


@pytest.mark.parametrize(
    'code,expected', (('', False), ('gsv', True), ('9gi', False))
)
def test_items_data_storage_is_misc(items_data, code, expected):
    assert items_data.is_misc(code) is expected


@pytest.mark.parametrize(
    'code,expected', (('', False), ('tbk', True), ('gsv', False))
)
def test_items_data_storage_is_quantitative(items_data, code, expected):
    assert items_data.is_quantitative(code) is expected


@pytest.mark.parametrize(
    'code,expected', (('', None), ('dr6', 'Alpha Helm'), ('tbk', None))
)
def test_items_data_storage_get_armor_name(items_data, code, expected):
    assert items_data.get_armor_name(code) == expected


@pytest.mark.parametrize(
    'code,expected', (('', None), ('uow', 'Aegis'), ('dr6', None))
)
def test_items_data_storage_get_shield_name(items_data, code, expected):
    assert items_data.get_shield_name(code) == expected


@pytest.mark.parametrize(
    'code,expected', (('', None), ('9gi', 'Ancient Axe'), ('uow', None))
)
def test_items_data_storage_get_weapon_name(items_data, code, expected):
    assert items_data.get_weapon_name(code) == expected


@pytest.mark.parametrize(
    'code,expected', (('', None), ('gsv', 'Amethyst'), ('9gi', None))
)
def test_items_data_storage_get_misc_name(items_data, code, expected):
    assert items_data.get_misc_name(code) == expected


@pytest.mark.parametrize(
    'attr_id,expected',
    (
        (None, None),
        (
            0,
            {
                'bits': [8],
                'bias': 32,
                'name': '+{} to Strength',
                'is_invisible': False,
            },
        ),
        (357, None),
    ),
)
def test_items_data_storage_get_magic_attr(items_data, attr_id, expected):
    assert items_data.get_magic_attr(attr_id) == expected


@pytest.mark.parametrize(
    'prefix_id,suffix_id,expected',
    ((0, 0, ''), (2, 0, 'Sturdy'), (0, 1, 'Health'), (2, 1, 'Sturdy Health')),
)
def test_items_data_storage_get_magic_name(
    items_data, prefix_id, suffix_id, expected
):
    assert items_data.get_magic_name(prefix_id, suffix_id) == expected


@pytest.mark.parametrize(
    'fname_id,sname_id,expected',
    ((0, 0, ''), (1, 0, 'Bite'), (0, 2, 'Scratch'), (1, 2, 'Bite Scratch')),
)
def test_items_data_storage_get_rare_name(
    items_data, fname_id, sname_id, expected
):
    assert items_data.get_rare_name(fname_id, sname_id) == expected


@pytest.mark.parametrize(
    'set_id,expected', ((127, None), (53, 'Angelic Wings'))
)
def test_items_data_storage_get_set_name(items_data, set_id, expected):
    assert items_data.get_set_name(set_id) == expected


@pytest.mark.parametrize(
    'unique_id,expected', (('0', None), (298, 'Tomb Reaver'))
)
def test_items_data_storage_get_unique_name(items_data, unique_id, expected):
    assert items_data.get_unique_name(unique_id) == expected


@pytest.mark.parametrize('runeword_id,expected', ((0, None), (59, 'Enigma')))
def test_items_data_storage_get_runeword_name(
    items_data, runeword_id, expected
):
    assert items_data.get_runeword_name(runeword_id) == expected


@pytest.mark.parametrize(
    'code,expected',
    (
        (0, None),
        ('r01', [{'id': 31, 'values': [15]}, {'id': 89, 'values': [1]}]),
    ),
)
def test_items_data_storage_get_armor_sock_attrs(items_data, code, expected):
    assert items_data.get_armor_sock_attrs(code) == expected


@pytest.mark.parametrize(
    'code,expected', ((0, None), ('r02', [{'id': 20, 'values': [7]}]))
)
def test_items_data_storage_get_shield_sock_attrs(items_data, code, expected):
    assert items_data.get_shield_sock_attrs(code) == expected


@pytest.mark.parametrize(
    'code,expected',
    (
        (0, None),
        ('r01', [{'id': 19, 'values': [50]}, {'id': 89, 'values': [1]}]),
    ),
)
def test_items_data_storage_get_weapon_sock_attrs(items_data, code, expected):
    assert items_data.get_weapon_sock_attrs(code) == expected
