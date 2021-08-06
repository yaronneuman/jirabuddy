import logging
import re

from slackbot.utils import to_utf8

logger = logging.getLogger(__name__)


class PluginsManager(object):
    def __init__(self):
        pass

    commands = {
        'respond_to': {},
        'listen_to': {},
        'default_reply': {}
    }

    def get_plugins(self, category, text):
        has_matching_plugin = False
        if text is None:
            text = ''
        for matcher in self.commands[category]:
            m = matcher.search(text)
            if m:
                has_matching_plugin = True
                yield self.commands[category][matcher], to_utf8(m.groups())

        if not has_matching_plugin:
            yield None, None


def respond_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['respond_to'][
            re.compile(matchstr, flags)] = func
        logger.info('registered respond_to plugin "%s" to "%s"', func.__name__,
                    matchstr)
        return func

    return wrapper


def listen_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['listen_to'][
            re.compile(matchstr, flags)] = func
        logger.info('registered listen_to plugin "%s" to "%s"', func.__name__,
                    matchstr)
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
    matchstr = kwargs.pop('matchstr', r'^.*$')
    flags = kwargs.pop('flags', 0)

    if not invoked:
        func = args[0]

    def wrapper(func):
        PluginsManager.commands['default_reply'][
            re.compile(matchstr, flags)] = func
        logger.info('registered default_reply plugin "%s" to "%s"', func.__name__,
                    matchstr)
        return func

    return wrapper if invoked else wrapper(func)
