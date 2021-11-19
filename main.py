import os

from jirabuddy.clients import JiraClient
from jirabuddy.bot import SlackBot
from jirabuddy.clients import GitLabClient
from jirabuddy.common import enum, FreeTextParser, Configuration

APP_NAME = "colo"


# This is disgusting, but the easiest way to allow dynamic plugins without messing with impotlib
# Will fix this later.
def init_slackbot_plugins(config):
    exec(open(config.bot.plugins_path).read())


def main():
    config = enum("config", nest=True, **Configuration(APP_NAME).parse())
    ftxtp = FreeTextParser()
    ftxtp.ignore("on", "for", "to", "in")

    slackbot = SlackBot(config.slack.token,
                        debug=bool(int(os.environ.get("DEBUG", 0))),
                        plugins_cache_path=config.bot.plugins_cache_path)

    if "jira" in config.enum_names:
        jira_client = JiraClient(config.jira.server,
                                 config.jira.username,
                                 config.jira.password,
                                 default_project=config.jira.default_project)
        slackbot.register("jira", jira_client)
        ftxtp.register("jira_project", jira_client.Projects.get)
        ftxtp.register("jira_component", jira_client.Components.get)
        ftxtp.register("jira_ticket_type", jira_client.TicketTypes.get)
        ftxtp.register("jira_priority", jira_client.Priorities.get)
        ftxtp.register("jira_fix_version", jira_client.FixVersions.get)

    if "gitlab" in config.enum_names and config.gitlab.server:
        gitlab_client = GitLabClient(config.gitlab.server,
                                     config.gitlab.token)
        slackbot.register("gitlab", gitlab_client)

    ftxtp.register("slack_user", slackbot.find_user)
    slackbot.register("text_parser", ftxtp)

    init_slackbot_plugins(config)
    print("Starting!")
    slackbot.run()


if __name__ == "__main__":
    main()
