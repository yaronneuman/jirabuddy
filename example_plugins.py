from datetime import timedelta

from jirabuddy.bot import respond_to, every, PeriodicPlugin, RegexPlugin


@respond_to("^sup$")
def view_ticket(_, msg):
    msg.reply("SUP ;/")


@respond_to("(^[0-9 ]*)\+([0-9 ]*)")
def plus(_, msg, first: str, second: str):
    """Calculate a simple Plus equation"""
    if first.isdigit() and second.isdigit():
        result = int(first) + int(second)
        msg.reply(f"that's easy!\n{result}")
        return
    msg.reply("oops! that's not a valid statement")


@respond_to("Nice to meet you, I'm (.*)$")
def self_intro(_, msg, who):
    """Say hi to the bot"""
    msg.reply(f"Hey {who}, it's a pleasure to meet you. I'm Colo, at your service!")


@respond_to("remember (.*)")
def remember(plugin: RegexPlugin, msg, what_to_remember):
    from datetime import datetime
    msg.reply("I will do my best to remember that!")

    remembered = plugin.restore("what_to_remember")  # get specific value from plugin cache, or None if not cached
    when = plugin.restore("when")
    if remembered and when:
        msg.reply(f'last time, at {when}, you told me to remember: {remembered}')

    stored_dict = plugin.restore()  # get all values from plugin cache as a new dict
    stored_dict["what_to_remember"] = what_to_remember
    stored_dict["when"] = datetime.utcnow()
    plugin.store(stored_dict)  # update plugin cache with dict values


@every(timedelta(minutes=10))
def nag(plugin: PeriodicPlugin, slack_message):
    """
    will be running every 10 minutes
    slack_message: optional magic param to get slack client message dispatcher
    """
    slack_message("@yneuman", "I will ping you every %s seconds" % plugin.frequency.total_seconds())
