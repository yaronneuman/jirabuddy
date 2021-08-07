import logging
import pickle
from datetime import timedelta
from typing import List, Any, Generator, Tuple

from slackbot.utils import to_utf8

from .plugins import Plugin, RegexPlugin, PeriodicPlugin

logger = logging.getLogger(__name__)


class PluginsManager(object):
    def __init__(self, plugins_cache_path: [str, None] = None):
        self.__plugins_cache_path = plugins_cache_path
        self._load_plugins_cache()

    _plugins_cache = {}
    _store = {
        'respond_to': [],
        'listen_to': [],
        'periodic': [],
        'default_reply': []
    }

    def _load_plugins_cache(self):
        if self.__plugins_cache_path:
            try:
                PluginsManager._plugins_cache = pickle.load(open(self.__plugins_cache_path, "rb"))
            except Exception:
                pass

    def _save_plugins_cache(self):
        if self.__plugins_cache_path:
            for category in self._store:
                for plugin in self._store[category]:
                    self._plugins_cache[plugin.id] = plugin.cache
            try:
                pickle.dump(self._plugins_cache, open(self.__plugins_cache_path, "wb"))
            except Exception:
                pass

    @classmethod
    def register_plugin(cls, plugin: Plugin):
        if plugin.id in cls._plugins_cache:
            plugin.cache.update(cls._plugins_cache[plugin.id])
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

    def teardown(self):
        self._save_plugins_cache()


def respond_to(regex: str, flags=0, suspend=False):
    def wrapper(func):
        PluginsManager.register_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="respond_to", suspend=suspend))
        logger.info('registered respond_to plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper


def listen_to(regex: str, flags=0, suspend=False):
    def wrapper(func):
        PluginsManager.register_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="listen_to", suspend=suspend))
        logger.info('registered listen_to plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper


def every(period: timedelta, suspend=False):
    def wrapper(func):
        PluginsManager.register_plugin(PeriodicPlugin(func, period, plugin_type="periodic", suspend=suspend))
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
        PluginsManager.register_plugin(RegexPlugin(func, regex, re_flags=flags, plugin_type="default_reply"))
        logger.info('registered default_reply plugin "%s" to "%s"', func.__name__, regex)
        return func

    return wrapper if invoked else wrapper(func)
