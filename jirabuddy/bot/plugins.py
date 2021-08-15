import re
from abc import ABC, abstractmethod
from datetime import timedelta
from types import FunctionType
from typing import Tuple, Any, Optional


class Plugin(ABC):
    def __init__(self, func: FunctionType, name: str = None, plugin_type: str = None, suspend: bool = False):
        self._id: str = func.__code__.co_name
        self._name: str = name or func.__name__
        self._args: Tuple[str] = func.__code__.co_varnames
        self._docs: str = func.__doc__
        self._plugin_type: str = plugin_type
        self._func: FunctionType = func
        self.cache = {}
        self.suspend: bool = suspend

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return self._args

    @property
    def docs(self):
        return self._docs

    @property
    def plugin_type(self):
        return self._plugin_type

    @property
    def func(self):
        return self._func

    @abstractmethod
    def match(self, arg: Any) -> Tuple[bool, Optional[Tuple]]:
        pass

    def run(self, *args, **kwargs):
        if not self.suspend:
            self.func(*args, **kwargs)

    def store(self, store_dict: dict):
        self.cache.update(**store_dict)

    def restore(self, key: [str, None] = None):
        if key is None:
            return self.cache.copy()
        return self.cache.get(key, None)


class RegexPlugin(Plugin):

    def __init__(self,
                 func: FunctionType,
                 re_pattern: str,
                 name: str = None,
                 plugin_type: str = None,
                 re_flags: int = 0,
                 suspend: bool = False):

        super().__init__(func=func, name=name, plugin_type=plugin_type, suspend=suspend)
        self.re_pattern: str = re_pattern
        self.re_flags: int = re_flags
        self.matcher: re.Pattern = re.compile(re_pattern, re_flags)

    def match(self, arg: str) -> Tuple[bool, Optional[Tuple]]:
        m = self.matcher.match(arg)
        if m:
            return True, tuple(m.groups())
        return False, None


class PeriodicPlugin(Plugin):

    def __init__(self,
                 func: FunctionType,
                 frequency: timedelta,
                 name: str = None,
                 plugin_type: str = None,
                 suspend: bool = False):

        super().__init__(func=func, name=name, plugin_type=plugin_type, suspend=suspend)
        self.frequency: timedelta = frequency
        self.last_invoked_time = None

    def match(self, arg: int) -> Tuple[bool, Optional[Tuple]]:
        # first run, or last run was before now - frequency
        if not self.last_invoked_time or self.last_invoked_time + self.frequency.total_seconds() < arg:
            self.last_invoked_time = arg
            return True, tuple()
        return False, None
