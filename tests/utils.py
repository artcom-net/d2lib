import json
from pathlib import Path

from d2lib.files import D2SFile, D2XFile, SSSFile, _D2File
from d2lib.item import Item


class BytesJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for objects with fields of type bytes."""

    def default(self, o):
        if isinstance(o, bytes):
            return [num for num in o]
        return super(BytesJSONEncoder, self).default(o)


def to_json(obj, *args, **kwargs):
    """Dump obj to JSON.

    :type obj: d2lib.files._D2File, d2lib.item.Item
    :param args: Positional arguments for json.dumps
    :param kwargs: Keyword arguments for json.dumps
    :return: JSON string
    :rtype: str
    """
    if not isinstance(obj, (_D2File, Item)):
        raise ValueError('Invalid file type. _D2File is expected')
    kwargs['cls'] = BytesJSONEncoder
    return json.dumps(obj.to_dict(), *args, **kwargs)


def recreate_json_files(dir_path):
    """Re-creates JSON files for testing.

    :param dir_path: path to the test data directory
    :rtype: None
    """
    for obj_class, extension in (
        (D2SFile, 'd2s'),
        (D2XFile, 'd2x'),
        (SSSFile, 'sss'),
        (Item, 'd2i'),
    ):
        file_paths = Path(dir_path).glob(f'**/test_{extension}*.{extension}')
        for path in file_paths:
            json_file_path = path.with_suffix('.json')
            obj = obj_class.from_file(path)
            with json_file_path.open('w') as json_file:
                json_file.write(to_json(obj, indent=4))
