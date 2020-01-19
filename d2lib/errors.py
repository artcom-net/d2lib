class D2SFileParseError(Exception):
    """Used to parse .d2s files when something went wrong."""

    pass


class StashFileParseError(Exception):
    """Used to parse .d2x and .sss files when something went wrong."""

    pass


class ItemParseError(Exception):
    """Used to parse item structure when something went wrong."""

    pass
