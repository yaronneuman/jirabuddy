import os

import confuse

from jirabuddy.clients import JiraClient
from jirabuddy.bot import SlackBot
from jirabuddy.clients import GitLabClient
from jirabuddy.common import enum

APP_NAME = "colo"


# This is disgusting, but the easiest way to allow dynamic plugins without messing with impotlib
# Will fix this later.
def init_slackbot_plugins(config):
    exec(open(config.bot.plugins_path).read())


def main():
    config = enum("config", nest=True, **confuse.Configuration(APP_NAME).flatten())
    slackbot = SlackBot(config.slack.token,
                        debug=bool(int(os.environ.get("DEBUG", 0))),
                        plugins_cache_path=config.bot.plugins_cache_path)

    if "jira" in config.names:
        jira_client = JiraClient(config.jira.server,
                                 config.jira.username,
                                 config.jira.password,
                                 lazy=True,
                                 default_project=config.jira.default_project)
        slackbot.register("jira", jira_client)

    if "gitlab" in config.names:
        gitlab_client = GitLabClient(config.gitlab.server,
                                     config.gitlab.token)
        slackbot.register("gitlab", gitlab_client)

    init_slackbot_plugins(config)
    slackbot.run()


if __name__ == "__main__":
    main()
