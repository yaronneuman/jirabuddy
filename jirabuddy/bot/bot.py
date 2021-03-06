import logging
import re
import time

from six.moves import _thread
from slackbot.slackclient import SlackClient

from .dispatcher import Dispatcher
from .plugins_manager import PluginsManager

logger = logging.getLogger(__name__)

TIMEOUT = 100


class SlackBot(object):
    def __init__(self, token: str, debug: bool = False, plugins_cache_path: str = None):
        self._client = SlackClient(token, timeout=TIMEOUT)
        self._plugins = PluginsManager(plugins_cache_path=plugins_cache_path)
        self._dispatcher = Dispatcher(slack_client=self._client,
                                      plugins=self._plugins,
                                      errors_channel="test-colo",
                                      debug=debug)
        self.register("slack_users", self.find_user)
        self.register("slack_message", self._client.send_message)

    def find_user(self, user: str):
        by_id = self._client.get_user(re.sub("<@(.*?)>", "\\1", user))
        if by_id:
            return by_id

        by_name = self._client.find_user_by_name(user)
        if by_name:
            return self._client.get_user(by_name)

    def register(self, keyword: str, value):
        self._dispatcher.register(keyword, value)

    def run(self):
        self._dispatcher.start()
        if not self._client.connected:
            self._client.rtm_connect()

        _thread.start_new_thread(self._keep_active, tuple())
        logger.info('connected to slack RTM api')
        self._dispatcher.loop()

    def _keep_active(self):
        logger.info('keep active thread started')
        while True:
            time.sleep(30 * 60)
            self._client.ping()
