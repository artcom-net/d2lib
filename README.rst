=====
D2lib
=====

d2lib is a tool for retrieving information from Diablo 2 data files.
These files contain info about the character, items and their properties.

Supported files:


- .d2s - Diablo 2 save files;
- .d2x - PlugY personal stash files;
- .sss - PlugY shared stash files.

------------
Installation
------------
~~~~~~~~~~~~~
Prerequisites
~~~~~~~~~~~~~

- Python 3.6+

You can install d2lib using pip:

::

    pip install d2lib

-----
Usage
-----

.. code-block:: python

    from d2lib.files import D2SFile, D2XFile, SSSFile

    d2s_file = D2SFile('tests/data/test_d2s.d2s')
    d2x_file = D2XFile('tests/data/test_d2x.d2x')
    sss_file = SSSFile('tests/data/test_sss.sss')

    # Character attributes.
    print(d2s_file.char_class)
    print(d2s_file.char_name)
    print(d2s_file.char_level)
    print(d2s_file.is_died)
    print(d2s_file.last_played)
    print(d2s_file.attributes)
    print(d2s_file.skills)

    # Get all unique items.
    for item in d2s_file.items:
        if item.is_unique:
            print(item.level)
            print(item.name)
            print(item.base_name)
            print(item.magic_attrs)

    # or for stash files
    for page in d2x_file.stash:  # there may also be a SSSFile instance
        for item in page['items']:
            if item.is_unique:
                print(item.level)
                print(item.name)
                print(item.base_name)
                print(item.magic_attrs)

---------------
Acknowledgments
---------------
- `nokka/d2s <https://github.com/nokka/d2s>`_
- `squeek502/d2itemreader <https://github.com/squeek502/d2itemreader>`_
