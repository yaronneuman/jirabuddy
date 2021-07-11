import json
import re
from collections import OrderedDict
from typing import Any, Iterable


def to_valid_name(s: str):
    """
    :param s: any string
    :return: valid name for variables
    # Remove invalid characters
    # Remove leading characters until we find a letter or underscore
    http://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
    """
    return re.sub('^[^a-zA-Z_]+', '_', re.sub('[^0-9a-zA-Z_]', '_', s.strip()))


class TypeWrapper(type):
    def __init__(cls, what, bases=None, _dict=None):
        cls.__name__ = what
        super(TypeWrapper, cls).__init__(what, bases, _dict)

    def __getitem__(cls, item):
        return cls.__dict__[item]

    def __str__(self):
        return self.__name__


def enum(enum_type: str, reverse_mapping: bool = False, nest: bool = False,
         clean_variables: bool = False, save_original: bool = False,
         *sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    if clean_variables:
        enums = {to_valid_name(k): v for k, v in enums.items()}

    if reverse_mapping:
        reverse = dict((value, key) for key, value in enums.items())
        enums['__reverse_mapping'] = reverse

    enums['names'] = enums.keys()
    enums["name_values"] = enums.values()
    if save_original:
        enums["__json"] = json.dumps(enums)

    if nest:
        enums = {var: enum(str(var),
                           reverse_mapping=reverse_mapping,
                           nest=nest,
                           clean_variables=clean_variables,
                           save_original=save_original,
                           **value) if isinstance(value, (dict, OrderedDict)) else value
                 for var, value in enums.items()}

    return TypeWrapper(enum_type, (), enums)


def to_enumable(name: str, key: str, value: Any, iterable: Iterable, clean_values: bool = False,
                reverse_mapping: bool = False, nest: bool = False):
    iterable = [item.__dict__ if not isinstance(item, (dict, OrderedDict)) else item for item in iterable]
    tuples = []
    for i in iterable:
        k = to_valid_name(i.__getitem__(key))
        if value is None:
            v = i
        else:
            v = to_valid_name(i.__getitem__(value)) if clean_values else i.__getitem__(value)
        tuples.append((k, v))
    return enum(name, reverse_mapping=reverse_mapping, nest=nest, **dict(tuples))
