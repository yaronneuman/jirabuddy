import os
from collections import OrderedDict

from confuse import Configuration as ConfSuper


class Configuration(ConfSuper):
    def __init__(self, appname: str):
        super().__init__(appname)

    def _recursive_parse(self, node: OrderedDict, dynasty: list = None):
        dynasty = dynasty or []
        import pdb; pdb.set_trace()
        for key, value in node.copy().items():
            if isinstance(value, OrderedDict):
                node[key] = self._recursive_parse(value, dynasty + [key])
            else:
                node[key] = os.environ.get(("_".join(dynasty + [key]).upper()), value)
        return node

    def parse(self):
        flat = self.flatten()
        return self._recursive_parse(flat)
