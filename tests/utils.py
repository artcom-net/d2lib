import json

from d2lib.files import _D2File
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
