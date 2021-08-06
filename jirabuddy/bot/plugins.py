import logging
import re
from abc import ABC, abstractmethod
from types import FunctionType
from typing import Tuple, Any, Optional, Match, Union

from slackbot.utils import to_utf8

logger = logging.getLogger(__name__)


class Plugin(ABC):
    def __init__(self, func: FunctionType, name: str = None, plugin_type: str = None):
        self.id: str = func.__code__.co_name
        self.name: str = name or func.__name__
        self.args: Tuple[str] = func.__code__.co_varnames
        self.docs: str = func.__doc__
        self.plugin_type: str = plugin_type
        self.func: FunctionType = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    @abstractmethod
    def match(self, arg: Any):
        pass


class RegexPlugin(Plugin):

    def __init__(self, func: FunctionType, re_pattern: str, name: str = None, plugin_type: str = None, re_flags: int=0):
        super().__init__(func, name, plugin_type)
        self.re_pattern: str = re_pattern
        self.re_flags: int = re_flags
        self.matcher: re.Pattern = re.compile(re_pattern, re_flags)

    def run(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    def match(self, arg: str) -> Optional[Match[Union[Union[str, bytes], Any]]]:
        return self.matcher.search(arg)


class PluginsManager(object):
    def __init__(self):
        pass

    commands = {
        'respond_to': [],
        'listen_to': [],
        'default_reply': []
    }

    @classmethod
    def add_plugin(cls, plugin: Plugin):
        cls.commands[plugin.plugin_type].append(plugin)

    def get_plugins(self, category, text):
        has_matching_plugin = False
        if text is None:
            text = ''
        for plugin in self.commands[category]:
            m = plugin.match(text)
            if m:
                has_matching_plugin = True
                yield plugin, to_utf8(m.groups())

        if not has_matching_plugin:
            yield None, None


def respond_to(match_str, flags=0):
    def wrapper(func):
        PluginsManager.commands['respond_to'].append(RegexPlugin(func, match_str, re_flags=flags))
        logger.info('registered respond_to plugin "%s" to "%s"', func.__name__, match_str)
        return func

    return wrapper


def listen_to(match_str, flags=0):
    def wrapper(func):
        PluginsManager.commands['listen_to'].append(RegexPlugin(func, match_str, re_flags=flags))
        logger.info('registered listen_to plugin "%s" to "%s"', func.__name__, match_str)
        return func

    return wrapper


# def default_reply(matchstr=r'^.*$', flags=0):
def default_reply(*args, **kwargs):
    """
    Decorator declaring the wrapped function to the default reply hanlder.

    May be invoked as a simple, argument-less decorator (i.e. ``@default_reply``) or
    with arguments customizing its behavior (e.g. ``@default_reply(matchstr='pattern')``).
    """
    invoked = bool(not args or kwargs)
    match_str = kwargs.pop('matchstr', r'^.*$')
    flags = kwargs.pop('flags', 0)

    if not invoked:
        func = args[0]

    def wrapper(func):
        PluginsManager.commands['default_reply'].append(RegexPlugin(func, match_str, re_flags=flags))
        logger.info('registered default_reply plugin "%s" to "%s"', func.__name__, match_str)
        return func

    return wrapper if invoked else wrapper(func)
