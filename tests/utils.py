import json

from d2lib.files import _D2File


class BytesJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for objects with fields of type bytes."""

    def default(self, o):
        if isinstance(o, bytes):
            return [num for num in o]
        return super(BytesJSONEncoder, self).default(o)


def to_json(d2_file, *args, **kwargs):
    """Dumps d2lib.files._D2File instance to JSON.

    :type d2_file: d2lib.files._D2File
    :param args: Positional arguments for json.dumps
    :param kwargs: Keyword arguments for json.dumps
    :return: JSON string
    :rtype: str
    """
    if not isinstance(d2_file, _D2File):
        raise ValueError('Invalid file type. _D2File is expected')
    kwargs['cls'] = BytesJSONEncoder
    return json.dumps(d2_file.to_dict(), *args, **kwargs)
