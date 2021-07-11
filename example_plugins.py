from slackbot.bot import respond_to


@respond_to("^sup$")
def view_ticket(msg):
    msg.reply("SUP ;/")


@respond_to("(^[0-9 ]*)\+([0-9 ]*)")
def plus(msg, first: str, second: str):
    """Calculate a simple Plus equation"""
    if first.isdigit() and second.isdigit():
        result = int(first) + int(second)
        msg.reply(f"that's easy!\n{result}")
        return
    msg.reply("oops! that's not a valid statement")


@respond_to("Nice to meet you, I'm (.*)$")
def self_intro(msg, who):
    """Say hi to the bot"""
    msg.reply(f"Hey {who}, it's a pleasure to meet you. I'm Colo, at your service!")
