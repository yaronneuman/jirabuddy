import slackbot
from slackbot.bot import Bot

from .dispatcher import MessageDispatcherWrapper


class SlackBot(Bot):
    def __init__(self, token: str, debug: bool = False, plugins_cache_path: str = None):
        slackbot.bot.settings.API_TOKEN = token
        slackbot.bot.settings.PLUGINS = []
        super(SlackBot, self).__init__()
        self._dispatcher = MessageDispatcherWrapper(slack_client=self._client,
                                                    plugins=self._plugins,
                                                    errors_channel="test-colo",
                                                    plugins_cache_path=plugins_cache_path,
                                                    debug=debug)
        self.register("slack_users", self._client.get_user)

    def register(self, keyword: str, value):
        self._dispatcher.register(keyword, value)
