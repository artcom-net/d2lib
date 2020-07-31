from d2lib.item import Item


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


def test_d2s_file_calc_checksum(d2s_file):
    d2s, expected = d2s_file
    assert d2s._calc_checksum() == expected['checksum']
