import json
import re
import operator

from collections import OrderedDict
from functools import reduce
from typing import Any, Dict, Tuple, List


def get_path_from_dict(dct: dict, path: str, delimiter: str = ".") -> Any:
    return reduce(operator.getitem, path.split(delimiter), dct)


def to_valid_name(s: str):
    """
    :param s: any string
    :return: valid name for variables
    # Remove invalid characters
    # Remove leading characters until we find a letter or underscore
    http://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
    """
    return re.sub('^([^a-zA-Z_]+)', '_\\1', re.sub('[^0-9a-zA-Z_]', '_', s.strip()))


class TypeWrapper(type):
    def __init__(cls, what, bases=None, _dict=None):
        cls.enum_names = _dict.pop("__enum_names")
        cls.enum_values = _dict.pop("__enum_values")
        cls.enum_orig_dict = json.loads(_dict.pop("__orig"))
        cls.__name__ = what
        super(TypeWrapper, cls).__init__(what, bases, _dict)

    def __getitem__(cls, item):
        return cls.__dict__[item]

    def get(cls, key: str) -> Any:
        return cls.__dict__.get(key, cls.enum_orig_dict.get(key, None))

    def __str__(self):
        return self.__name__


def enum(enum_type: str, reverse_mapping: bool = False, nest: bool = False,
         clean_variables: bool = False, save_original: bool = True,
         *sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)

    enums["__orig"] = json.dumps(enums)

    if clean_variables:
        enums = {to_valid_name(k): v for k, v in enums.items()}

    if reverse_mapping:
        reverse = dict((value, key) for key, value in enums.items())
        enums['__reverse_mapping'] = reverse

    enums['__enum_names'] = enums.keys()
    enums["__enum_values"] = enums.values()

    if nest:
        enums = {var: enum(str(var),
                           reverse_mapping=reverse_mapping,
                           nest=nest,
                           clean_variables=clean_variables,
                           save_original=save_original,
                           **value) if isinstance(value, (dict, OrderedDict)) else value
                 for var, value in enums.items()}

    return TypeWrapper(enum_type, (), enums)


def to_enumable(name: str, key: str, value: Any, iterable: (List, Tuple, Dict, OrderedDict), clean_values: bool = False,
                reverse_mapping: bool = False, nest: bool = False):
    iterable_dict = [item.__dict__ if not isinstance(item, (dict, OrderedDict)) else item for item in iterable]
    tuples = []
    for idx, i in enumerate(iterable_dict):
        k = get_path_from_dict(i, key)
        if value is None:
            v = iterable[idx]
        else:
            v = get_path_from_dict(i, value)
            v = to_valid_name(v) if clean_values else v
        tuples.append((k, v))
    return enum(name, clean_variables=True, reverse_mapping=reverse_mapping, nest=nest, **dict(tuples))
