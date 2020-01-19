import pytest

from d2lib.item import Item


@pytest.fixture(scope='module')
def d2s_json(d2s_file):
    return d2s_file[0].to_json()


@pytest.fixture(scope='module')
def stash_json(stash_file):
    return stash_file[0].to_json()


def test_d2s_file_to_json(d2s_json):
    assert d2s_json and isinstance(d2s_json, str)


def test_stash_file_to_json(stash_json):
    assert stash_json and isinstance(stash_json, str)


def test_d2s_file_to_dict(d2s_file):
    d2s, _ = d2s_file
    d2s_dict = d2s.to_dict()
    assert d2s_dict
    assert isinstance(d2s_dict, dict)
    for items_list in (d2s.items, d2s.merc_items, d2s.corpse_items):
        assert all(isinstance(item, Item) for item in items_list)


def test_stash_file_to_dict(stash_file):
    stash, _ = stash_file
    stash_dict = stash.to_dict()
    assert stash_dict
    assert isinstance(stash_dict, dict)
    for page in stash.stash:
        assert all(isinstance(item, Item) for item in page['items'])


def test_parse_d2s_file(d2s_file):
    d2s, expected = d2s_file
    assert d2s.to_dict() == expected


def test_parse_stash_file(stash_file):
    stash, expected = stash_file
    assert stash.to_dict() == expected
