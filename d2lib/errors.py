class _BaseParseException(Exception):
    def __init__(self, message):
        self.message = message


class D2SFileParseError(_BaseParseException):
    """Used to parse .d2s files when something went wrong."""

    pass


class StashFileParseError(_BaseParseException):
    """Used to parse .d2x and .sss files when something went wrong."""

    pass


class ItemParseError(_BaseParseException):
    """Used to parse item structure when something went wrong."""

    pass
