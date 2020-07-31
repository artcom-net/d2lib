import json
from pathlib import Path

import pytest

from d2lib.files import CharacterAttribute, D2SFile, D2XFile, SSSFile
from d2lib.skills import Skill
from pytest_lazyfixture import lazy_fixture

DATA_DIR = 'data'

d2s_files = Path(DATA_DIR).glob('test_d2s*.d2s')
d2x_files = Path(DATA_DIR).glob('test_d2x*.d2x')
sss_files = Path(DATA_DIR).glob('test_sss*.sss')


@pytest.fixture(scope='session', params=(*d2s_files,))
def d2s_file_path(request):
    return request.param


@pytest.fixture(scope='session')
def d2s_file(d2s_file_path):
    return D2SFile.from_file(d2s_file_path)


@pytest.fixture(scope='session')
def d2s_file_expected_dict(d2s_file_path):
    with open(d2s_file_path.with_suffix('.json'), 'r') as file:
        d2s_expected = json.load(file)
        d2s_expected['attributes'] = {
            CharacterAttribute(int(k)): v
            for k, v in d2s_expected['attributes'].items()
        }
        d2s_expected['skills'] = {
            Skill(int(k)): v for k, v in d2s_expected['skills'].items()
        }
        for field in (
            'checksum',
            'hot_keys',
            'char_appearance',
            'difficulty',
            'quests',
            'waypoints',
            'npc_intro',
        ):
            d2s_expected[field] = bytes(bytearray(d2s_expected[field]))
        return d2s_expected


@pytest.fixture(scope='session', params=(*d2x_files,))
def d2x_file_path(request):
    return request.param


@pytest.fixture(scope='session')
def d2x_file(d2x_file_path):
    return D2XFile.from_file(d2x_file_path)


@pytest.fixture(scope='session')
def d2x_file_expected_dict(d2x_file_path):
    with open(d2x_file_path.with_suffix('.json'), 'r') as file:
        return json.load(file)


@pytest.fixture(scope='session', params=(*sss_files,))
def sss_file_path(request):
    return request.param


@pytest.fixture(scope='session')
def sss_file(sss_file_path):
    return SSSFile.from_file(sss_file_path)


@pytest.fixture(scope='session')
def sss_file_expected_dict(sss_file_path):
    with open(sss_file_path.with_suffix('.json'), 'r') as file:
        return json.load(file)


@pytest.fixture(
    scope='session',
    params=(lazy_fixture('d2x_file'), lazy_fixture('sss_file')),
)
def stash_file(request):
    return request.param
