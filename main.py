import confuse

from jirabuddy.clients import JiraClient, SlackBot
from jirabuddy.common import enum


APP_NAME = "colo"


# This is disgusting, but the easiest way to allow dynamic plugins without messing with impotlib
# Will fix this later.
def init_slackbot_plugins(config):
    exec(open(config.bot.plugins_path).read())


def main():
    config = enum("config", nest=True, **confuse.Configuration(APP_NAME).flatten())

    jira_client = JiraClient(config.jira.server,
                             config.jira.username,
                             config.jira.password,
                             project=config.jira.default_project)

    slackbot = SlackBot(config.slack.token)
    slackbot.register("jira", jira_client)

    init_slackbot_plugins(config)
    slackbot.run()


if __name__ == "__main__":
    main()
