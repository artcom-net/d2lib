from pathlib import Path

import pytest

from d2lib.errors import D2SFileParseError, StashFileParseError
from d2lib.files import D2SFile, D2XFile, SSSFile
from d2lib.item import Item
from pytest_lazyfixture import lazy_fixture
from tests.conftest import DATA_DIR


@pytest.mark.parametrize('file_class', (D2SFile, D2XFile, SSSFile))
def test_d2_file_init(file_class):
    file = file_class()
    assert all(attr_value is None for attr_value in file.__dict__.values())


@pytest.mark.parametrize(
    'file_class,file_path,expected_dict',
    (
        (
            D2SFile,
            lazy_fixture('d2s_file_path'),
            lazy_fixture('d2s_file_expected_dict'),
        ),
        (
            D2XFile,
            lazy_fixture('d2x_file_path'),
            lazy_fixture('d2x_file_expected_dict'),
        ),
        (
            SSSFile,
            lazy_fixture('sss_file_path'),
            lazy_fixture('sss_file_expected_dict'),
        ),
    ),
)
def test_d2_file_from_file(file_class, file_path, expected_dict):
    assert file_class.from_file(file_path).to_dict() == expected_dict


@pytest.mark.parametrize(
    'file_class,file_path,error_class,error_message',
    (
        (
            D2SFile,
            Path(DATA_DIR).joinpath('test_error_d2s_header.d2s'),
            D2SFileParseError,
            'Invalid header id: 0x00000000',
        ),
        (
            D2SFile,
            Path(DATA_DIR).joinpath('test_error_d2s_checksum.d2s'),
            D2SFileParseError,
            "Checksum mismatch: b'\\x00\\x00\\x00\\x00' != b'b\\x8c\\xe8\\xbe'",  # noqa : E501
        ),
        (
            D2SFile,
            Path(DATA_DIR).joinpath('test_error_d2s_file_size.d2s'),
            D2SFileParseError,
            'Invalid file size: 764',
        ),
        (
            D2XFile,
            Path(DATA_DIR).joinpath('test_error_d2x_header.d2x'),
            StashFileParseError,
            'Invalid header id: 0x00000000',
        ),
        (
            D2XFile,
            Path(DATA_DIR).joinpath('test_error_d2x_version.d2x'),
            StashFileParseError,
            'Invalid version: 0x0000',
        ),
        (
            D2XFile,
            Path(DATA_DIR).joinpath('test_error_d2x_stash_header.d2x'),
            StashFileParseError,
            'Invalid stash header: 0x00000000',
        ),
        (
            SSSFile,
            Path(DATA_DIR).joinpath('test_error_sss_header.sss'),
            StashFileParseError,
            'Invalid header id: 0x00000000',
        ),
        (
            SSSFile,
            Path(DATA_DIR).joinpath('test_error_sss_version.sss'),
            StashFileParseError,
            'Invalid version: 0x0000',
        ),
        (
            SSSFile,
            Path(DATA_DIR).joinpath('test_error_sss_stash_header.sss'),
            StashFileParseError,
            'Invalid stash header: 0x00000000',
        ),
    ),
)
def test_d2_file_from_file_fail(
    file_class, file_path, error_class, error_message
):
    with pytest.raises(error_class) as error:
        file_class.from_file(file_path)
    assert error.value.message == error_message


def test_d2s_file_to_dict(d2s_file):
    d2s_dict = d2s_file.to_dict()
    assert isinstance(d2s_dict, dict)
    assert all(not key.startswith('_') for key in d2s_dict.keys())
    for items_list in (
        d2s_file.items,
        d2s_file.merc_items,
        d2s_file.corpse_items,
    ):
        assert all(isinstance(item, Item) for item in items_list)


def test_stash_file_to_dict(stash_file):
    stash_file_dict = stash_file.to_dict()
    assert isinstance(stash_file_dict, dict)
    assert all(not key.startswith('_') for key in stash_file_dict.keys())
    for page in stash_file.stash:
        assert all(isinstance(item, Item) for item in page['items'])


def test_d2s_file_calc_checksum(d2s_file, d2s_file_expected_dict):
    assert d2s_file._calc_checksum() == d2s_file_expected_dict['checksum']
