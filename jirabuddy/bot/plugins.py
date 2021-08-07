import logging
import re
from abc import ABC, abstractmethod
from datetime import timedelta
from types import FunctionType
from typing import Tuple, Any, Optional, List, Generator

from slackbot.utils import to_utf8

logger = logging.getLogger(__name__)


class Plugin(ABC):
    def __init__(self, func: FunctionType, name: str = None, plugin_type: str = None, suspend: bool = False):
        self._id: str = func.__code__.co_name
        self._name: str = name or func.__name__
        self._args: Tuple[str] = func.__code__.co_varnames
        self._docs: str = func.__doc__
        self._plugin_type: str = plugin_type
        self._func: FunctionType = func
        self._plugin_cache = {}
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
        self._plugin_cache.update(**store_dict)

    def restore(self, key: [str, None] = None):
        if key is None:
            return self._plugin_cache.copy()
        return self._plugin_cache.get(key, None)


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
        m = self.matcher.search(arg)
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


class PluginsManager(object):
    def __init__(self):
        pass

    _store = {
        'respond_to': [],
        'listen_to': [],
        'periodic': [],
        'default_reply': []
    }

    @classmethod
    def add_plugin(cls, plugin: Plugin):
        cls._store[plugin.plugin_type].append(plugin)

    def get_plugins_category(self, category: str) -> List[Plugin]:
        return self._store[category]

    def get_plugins(self, category: str, arg: Any) -> Generator[Tuple[Plugin, List[str]], None, None]:
        has_matching_plugin = False
        if arg is None:
            arg = ''
        for plugin in self.get_plugins_category(category=category):
            match, args = plugin.match(arg)
            if match:
                has_matching_plugin = True
                yield plugin, to_utf8(args)

        if not has_matching_plugin:
            yield None, None


def respond_to(regex: str, flags=0, suspend=False):
    def wrapper(func):
        PluginsManager.add_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="respond_to", suspend=suspend))
        logger.info('registered respond_to plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper


def listen_to(regex: str, flags=0, suspend=False):
    def wrapper(func):
        PluginsManager.add_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="listen_to", suspend=suspend))
        logger.info('registered listen_to plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper


def every(period: timedelta, suspend=False):
    def wrapper(func):
        PluginsManager.add_plugin(PeriodicPlugin(func, period, plugin_type="periodic", suspend=suspend))
        logger.info('registered periodic plugin "%s" every "%d" seconds', func.__name__, period.total_seconds())
        return func

    return wrapper


# def default_reply(regex=r'^.*$', flags=0):
def default_reply(*args, **kwargs):
    """
    Decorator declaring the wrapped function to the default reply hanlder.

    May be invoked as a simple, argument-less decorator (i.e. ``@default_reply``) or
    with arguments customizing its behavior (e.g. ``@default_reply(regex='pattern')``).
    """
    invoked = bool(not args or kwargs)
    regex = kwargs.pop('regex', r'^.*$')
    flags = kwargs.pop('flags', 0)

    if not invoked:
        func = args[0]

    def wrapper(func):
        PluginsManager.add_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="default_reply"))
        logger.info('registered default_reply plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper if invoked else wrapper(func)
