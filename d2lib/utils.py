import json
from functools import partial, wraps
from io import BytesIO

int_from_lbytes = partial(int.from_bytes, byteorder='little')
int_from_bbytes = partial(int.from_bytes, byteorder='big')


def obj_to_dict(obj, exclude=()):
    """Dumps an object into the dictionary excluding received fields.

    :param obj: An object to dumps with the __dict__ attribute defined
    :type obj: object
    :param exclude: Exclusion fields where each field is a string
    :type exclude: iterable
    :return: Dictionary with excluded fields
    :rtype: dict
    """
    return {k: v for k, v in obj.__dict__.items() if k not in exclude}


def to_dict_list(objects):
    """Makes a list of dictionaries from objects.

    :param objects: List of objects to dump
    :type objects: iterable
    :return: List of dictionaries
    :rtype: dict
    """
    return [obj.to_dict() for obj in objects]


def is_set_bit(byte, position):
    """Checks if n bit is set in byte.

    :param byte: Single-byte integer
    :type byte: int
    :param position: Bit position
    :type position: int
    :return: True if the bit at position is set otherwise False
    :rtype: bool
    """
    return bool((byte >> position) & 0b1)


def calc_bits_to_align(bits):
    """Calculates the number of bits needed to align byte.

    :param bits: Number of bits
    :type bits: int
    :return: Number of bits needed to align byte
    :rtype: int
    """
    remainder = bits % 8
    if remainder > 0:
        return 8 - remainder
    return 0


def read_null_term_bstr(reader):
    """Reads a string from a stream until it encounters a null byte.

    :param reader: Byte stream.
    :type reader: io.BinaryIO
    :return: Byte string
    :rtype: bytes
    """
    buffer = BytesIO()
    while True:
        byte = reader.read(1)
        if byte in (b'\x00', b''):
            return buffer.getvalue()
        buffer.write(byte)


def stripped_string_concat(str1, str2):
    """Concatenates passed strings and truncates spaces in the result.

    :param str1: First string
    :type str1: str
    :param str2: Second string
    :type str2: str
    :return: A string with truncated spaces
    :rtype: str
    """
    return f'{str1} {str2}'.strip()


def _reverse_bits(data, bits):
    """Flips n number of bit.

    :param data: Source integer number
    :type data: int
    :param bits: The number of bits to flip
    :type bits: int
    :return: Integer
    :rtype: int
    """
    if bits == 0:
        return data
    result = 0
    for _ in range(bits):
        result <<= 1
        result |= data & 0b1
        data >>= 1
    return result


def _reverse(func):
    """Decorator for _reverse_bits.

    :param func: Function witch returning an integer
    :type func: function
    :return: Function wrapped _reverse_bits
    :rtype: function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        _, bits = args
        return _reverse_bits(func(*args, **kwargs), bits)

    return wrapper


class _BytesJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for objects with fields of type bytes."""

    def default(self, o):
        if isinstance(o, bytes):
            return [num for num in o]
        return super(_BytesJSONEncoder, self).default(o)


class ReverseBitReader(object):
    """This class is a reversed bit reader from stream."""

    def __init__(self, reader):
        """Initializes an instance.

        :param reader: Byte stream.
        :type reader: io.BinaryIO
        """
        self._data = 0
        self._reader = reader
        self._bits_read = 0
        self.bits_total = 0

    @_reverse
    def read(self, bits):
        """Reads n bits and flips their sequence.

        :param bits: The number of bits to read
        :type bits: int
        :return: Integer
        :rtype: int
        """
        if bits == 0:
            return None
        while self._bits_read < bits:
            byte = _reverse_bits(
                int.from_bytes(self._reader.read(1), byteorder='little'), 8
            )
            self._data <<= 8
            self._data |= byte
            self._bits_read += 8
        result = (self._data >> (self._bits_read - bits)) & ((1 << bits) - 1)
        self._bits_read -= bits
        self.bits_total += bits
        return result

    def read_null_term_bstr(self, bits):
        """Reads a string from a stream until it encounters a null char code.

        This is necessary to read string where the byte has less than 8 bits.

        :param bits: The number of bits to read the character code
        :return: Byte string
        :rtype: bytes
        """
        buffer = BytesIO()
        while True:
            char_code = self.read(bits)
            if char_code == 0:
                break
            buffer.write(char_code.to_bytes(length=1, byteorder='big'))
        return buffer.getvalue()
