import json
from pathlib import Path

import pytest

from d2lib.files import D2SFile, D2XFile, SSSFile

DATA_DIR = 'data'
DATA_FILE_PREFIX = 'test_'

d2s_files = Path(DATA_DIR).glob('*.d2s')
d2x_files = Path(DATA_DIR).glob('*.d2x')
sss_files = Path(DATA_DIR).glob('*.sss')


@pytest.fixture(scope='session', params=(*d2s_files,))
def d2s_file(request):
    d2s_file_path = request.param
    with open(d2s_file_path.with_suffix('.json'), 'r') as file:
        d2s_expected = json.load(file)
        for field in (
            'hot_keys',
            'char_appearance',
            'difficulty',
            'quests',
            'waypoints',
            'npc_intro',
        ):
            d2s_expected[field] = bytes(bytearray(d2s_expected[field]))
        return D2SFile(d2s_file_path), d2s_expected


@pytest.fixture(scope='session', params=(*d2x_files, *sss_files))
def stash_file(request):
    stash_file_path = request.param
    with open(stash_file_path.with_suffix('.json'), 'r') as file:
        stash_expected = json.load(file)
        stash_class = D2XFile if stash_file_path.suffix == '.d2x' else SSSFile
        return stash_class(stash_file_path), stash_expected
