from io import BytesIO
from random import randint

import pytest

from d2lib.utils import (
    ReverseBitReader,
    _BytesJSONEncoder,
    _reverse_bits,
    calc_bits_to_align,
    is_set_bit,
    obj_to_dict,
    read_null_term_bstr,
    stripped_string_concat,
    to_dict_list,
)

TEST_STRING = b'ReadNullTermStr'
TEST_NUM = b'\x01\xc0'


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


@pytest.fixture(scope='module')
def bytes_json_encoder():
    return _BytesJSONEncoder()


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


@pytest.mark.parametrize(
    'exclude', ((), ('_reader',), ('_reader', '_rbit_reader'))
)
def test_obj_to_dict_d2s_file(d2s_file, exclude):
    d2s, _ = d2s_file
    d2s_dict = obj_to_dict(d2s, exclude=exclude)
    assert isinstance(d2s_dict, dict)
    assert all(field not in d2s_dict for field in exclude)


@pytest.mark.parametrize('exclude', ((), ('_reader',), ('_reader', 'stash')))
def test_obj_to_dict_stash_file(stash_file, exclude):
    stash, _ = stash_file
    stash_dict = obj_to_dict(stash, exclude=exclude)
    assert isinstance(stash_dict, dict)
    assert all(field not in stash_dict for field in exclude)


def test_to_dict_list_d2s_file(d2s_file):
    d2s, _ = d2s_file
    items_dict_list = to_dict_list(d2s.items)
    assert isinstance(items_dict_list, list)
    assert all(isinstance(item_dict, dict) for item_dict in items_dict_list)


def test_to_dict_list_stash_file(stash_file):
    stash_file_, _ = stash_file
    for page in stash_file_.stash:
        items_dict_list = to_dict_list(page['items'])
        assert isinstance(items_dict_list, list)
        assert all(
            isinstance(item_dict, dict) for item_dict in items_dict_list
        )


@pytest.mark.parametrize(
    'num,bit_pos,expected',
    ((0, 0, False), (128, 7, True), (1, 0, True), (255, 8, False)),
)
def test_is_set_bit(num, bit_pos, expected):
    assert is_set_bit(num, bit_pos) is expected


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
    '_bytes,expected',
    (
        (b'', []),
        (b'\x00', [0]),
        (b'TestString', [84, 101, 115, 116, 83, 116, 114, 105, 110, 103]),
    ),
)
def test_bytes_json_encoder(bytes_json_encoder, _bytes, expected):
    assert bytes_json_encoder.default(_bytes) == expected
