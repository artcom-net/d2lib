from io import BytesIO
from random import randint

import pytest
from pytest_lazyfixture import lazy_fixture

from d2lib._utils import (
    ReverseBitReader,
    _calc_total_poison_damage,
    _reverse_bits,
    calc_bits_to_align,
    calc_poison_damage_params,
    get_poison_damage_str,
    obj_to_dict,
    read_null_term_bstr,
    stripped_string_concat,
    to_dict_list,
)
from d2lib.items_storage import ItemsDataStorage

TEST_STRING = b'ReadNullTermStr'
TEST_NUM = b'\x01\xc0'
POISON_DAMAGE_ATTR_ID = 57


@pytest.fixture(
    params=(
        (b'', b'', 0),
        (b'\x00', b'', 0),
        (TEST_STRING, TEST_STRING, 0),
        (TEST_STRING, TEST_STRING, randint(1, 16)),
    )
)
def null_term_str(request):
    string, expected, null_count = request.param
    buffer = BytesIO()
    buffer.write(string)
    for _ in range(null_count):
        buffer.write(b'\x00')
    buffer.seek(0)
    return buffer, expected


@pytest.fixture(
    params=((TEST_NUM, (9, 7), (1, 96)), (TEST_NUM, (8, 8), (1, 192)))
)
def reverse_bit_reader_num(request):
    num, bits_step, expected = request.param
    buffer = BytesIO()
    buffer.write(num)
    buffer.seek(0)
    rb_reader = ReverseBitReader(buffer)
    return rb_reader, bits_step, expected


@pytest.fixture
def reverse_bit_reader_str(null_term_str):
    buffer, expected = null_term_str
    rb_reader = ReverseBitReader(buffer)
    return rb_reader, expected


@pytest.fixture(scope='module')
def poison_damage_attr_template():
    return ItemsDataStorage().get_magic_attr(POISON_DAMAGE_ATTR_ID)['name']


@pytest.mark.parametrize(
    'd2_file,exclude',
    (
        (lazy_fixture('d2s_file'), ('_reader', '_rbit_reader')),
        (lazy_fixture('d2x_file'), ('_reader')),
        (lazy_fixture('sss_file'), ('_reader')),
    ),
)
def test_obj_to_dict(d2_file, exclude):
    file_dict = obj_to_dict(d2_file, exclude=exclude)
    assert isinstance(file_dict, dict)
    assert all(field not in file_dict for field in exclude)


def test_to_dict_list_d2s_file(d2s_file):
    items_dict_list = to_dict_list(d2s_file.items)
    assert isinstance(items_dict_list, list)
    assert all(isinstance(item_dict, dict) for item_dict in items_dict_list)


def test_to_dict_list_stash_file(stash_file):
    for page in stash_file.stash:
        items_dict_list = to_dict_list(page['items'])
        assert isinstance(items_dict_list, list)
        assert all(
            isinstance(item_dict, dict) for item_dict in items_dict_list
        )


@pytest.mark.parametrize(
    'read_bits,expected', ((0, 0), (7, 1), (11, 5), (8, 0))
)
def test_get_bits_to_align(read_bits, expected):
    assert calc_bits_to_align(read_bits) == expected


def test_read_null_term_str(null_term_str):
    buffer, expected = null_term_str
    assert read_null_term_bstr(buffer) == expected


@pytest.mark.parametrize(
    'str1,str2,expected',
    (
        ('', '', ''),
        (' String1 ', '', 'String1'),
        ('', ' String2  ', 'String2'),
        ('String1', 'String2', 'String1 String2'),
    ),
)
def test_items_data_storage_stripped_concat(str1, str2, expected):
    assert stripped_string_concat(str1, str2) == expected


@pytest.mark.parametrize(
    'num,bits,expected', ((0, 0, 0), (192, 8, 3), (192, 7, 1), (255, 0, 255))
)
def test_reverse_bits(num, bits, expected):
    assert _reverse_bits(num, bits) == expected


def test_reverse_bit_reader_read(reverse_bit_reader_num):
    rb_reader, bits_step, expected_values = reverse_bit_reader_num
    bits_read = 0
    for bits, expected in zip(bits_step, expected_values):
        bits_read += bits
        assert rb_reader.read(bits) == expected
        assert rb_reader.bits_total == bits_read


def test_reverse_bit_reader_read_null_term_str(reverse_bit_reader_str):
    rb_reader, expected = reverse_bit_reader_str
    assert rb_reader.read_null_term_bstr(8) == expected


@pytest.mark.parametrize(
    'damage,duration,expected',
    (
        (0, 1, 0),
        (205, 5, 100),
        (125, 2, 24),
        (175, 2, 34),
        (41, 3, 12),
        (52, 3, 15),
        (30, 3, 9),
        (36, 3, 11),
    ),
)
def test_calc_total_poison_damage(damage, duration, expected):
    assert _calc_total_poison_damage(damage, duration) == expected


@pytest.mark.parametrize(
    'min_damage,max_damage,duration,expected',
    (
        (0, 0, 0, (0, 0, 0)),
        (205, 205, 125, (100, 100, 5)),
        (125, 175, 50, (24, 34, 2)),
        (41, 41, 75, (12, 12, 3)),
        (52, 52, 75, (15, 15, 3)),
        (30, 36, 75, (9, 11, 3)),
        (128, 128, 75, (38, 38, 3)),
        (426, 426, 150, (250, 250, 6)),
        (187, 187, 50, (37, 37, 2)),
    ),
)
def test_calc_poison_damage_params(min_damage, max_damage, duration, expected):
    result = calc_poison_damage_params(min_damage, max_damage, duration)
    assert result == expected


@pytest.mark.parametrize(
    'min_damage,max_damage,duration,expected',
    (
        (0, 0, 0, '+0 poison damage over 0 seconds'),
        (100, 100, 5, '+100 poison damage over 5 seconds'),
        (9, 11, 3, 'Adds 9-11 poison damage over 3 seconds'),
    ),
)
def test_get_poison_damage_str(
    min_damage, max_damage, duration, expected, poison_damage_attr_template
):
    result = get_poison_damage_str(
        min_damage, max_damage, duration, poison_damage_attr_template
    )
    assert result == expected
