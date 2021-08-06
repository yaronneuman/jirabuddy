from jirabuddy.bot import respond_to


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


@respond_to("remember (.*)")
def remember(msg, what_to_remember):
    from datetime import datetime
    msg.reply("I will do my best to remember that!")

    remembered = msg.restore("what_to_remember")  # get specific value from plugin cache, or None if not cached
    when = msg.restore("when")
    if remembered and when:
        msg.reply(f'last time, at {when}, you told me to remember: {remembered}')

    stored_dict = msg.restore()  # get all values from plugin cache as a new dict
    stored_dict["what_to_remember"] = what_to_remember
    stored_dict["when"] = datetime.utcnow()
    msg.store(stored_dict)  # update plugin cache with dict values
