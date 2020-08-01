import json
from pathlib import Path

import pytest

from d2lib.errors import ItemParseError
from d2lib.item import Item
from tests.conftest import DATA_DIR


def _get_item_names(items):
    return [item.name for item in items]


@pytest.fixture(
    scope='module', params=(*Path(DATA_DIR).glob('test_d2i*.d2i'),)
)
def item_file_path(request):
    return request.param


@pytest.yield_fixture
def item_file(item_file_path):
    item_file = open(item_file_path, 'rb')
    yield item_file
    item_file.close()


@pytest.fixture
def item(item_file):
    return Item.from_stream(item_file)


@pytest.fixture(scope='module')
def item_expected_dict(item_file_path):
    with open(item_file_path.with_suffix('.json'), 'r') as file:
        return json.load(file)


@pytest.fixture
def d2s_items(d2s_file):
    return d2s_file.items


@pytest.fixture
def stash_items(stash_file):
    return [item for page in stash_file.stash for item in page['items']]


@pytest.fixture
def d2s_item_names(d2s_items):
    return _get_item_names(d2s_items)


@pytest.fixture
def stash_item_names(stash_items):
    return _get_item_names(stash_items)


def test_item_init():
    assert Item()


def test_item_from_stream(item_file, item_expected_dict):
    item = Item.from_stream(item_file)
    assert isinstance(item, Item)
    assert item.to_dict() == item_expected_dict


@pytest.mark.parametrize(
    'stream,error_class,error_message',
    (
        (None, ValueError, "Invalid stream type: <class 'NoneType'>"),
        (
            Path(DATA_DIR).joinpath('test_error_item_header.d2i').open('rb'),
            ItemParseError,
            'Invalid item header id: 0000',
        ),
    ),
)
def test_item_from_stream_fail(stream, error_class, error_message):
    with pytest.raises(error_class) as error:
        Item.from_stream(stream)
    assert str(error.value) == error_message


def test_item_from_file(item_file_path, item_expected_dict):
    item = Item.from_file(item_file_path)
    assert isinstance(item, Item)
    assert item.to_dict() == item_expected_dict


def test_item_to_dict(item):
    item_dict = item.to_dict()
    assert isinstance(item_dict, dict)
    assert item_dict
    assert all(not key.startswith('_') for key in item_dict.keys())


def test_d2s_item_name(d2s_item_names):
    assert all(d2s_item_names)


def test_stash_item_name(stash_item_names):
    assert all(stash_item_names)
