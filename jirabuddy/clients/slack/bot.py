import slackbot
from slackbot.bot import Bot

from .message import MessageDispatcherWrapper


class SlackBot(Bot):
    def __init__(self, token: str, debug=False):

        slackbot.bot.settings.API_TOKEN = token
        slackbot.bot.settings.PLUGINS = []
        super(SlackBot, self).__init__()
        self._dispatcher = MessageDispatcherWrapper(self._client, self._plugins, "test-colo", debug=debug)

    def register(self, keyword: str, value):
        self._dispatcher.register(keyword, value)
