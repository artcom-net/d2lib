import pytest


def _get_item_names(items):
    return [item.name for item in items]


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


def test_d2s_item_name(d2s_item_names):
    assert all(d2s_item_names)


def test_stash_item_name(stash_item_names):
    assert all(stash_item_names)
