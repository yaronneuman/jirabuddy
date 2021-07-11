import re
import traceback

from six import iteritems
from slackbot import dispatcher
from slackbot.utils import to_utf8
from slackbot.dispatcher import MessageDispatcher, logger, Message

dispatcher.AT_MESSAGE_MATCHER = re.compile(r'^\<@(\w+)\>:? (.*)$', re.S)


class MessageDispatcherWrapper(MessageDispatcher):
    def __init__(self, *args, **kwargs):
        self._registered_keywords = {}
        debug = kwargs.pop("debug", False)
        super(MessageDispatcherWrapper, self).__init__(*args, **kwargs)
        self.debug: bool = debug

    def _get_plugins_help(self, verbose: bool = True) -> str:
        helps = [u"You can ask me one of the following questions:"]
        for p, v in sorted(iteritems(self._plugins.commands['respond_to']), key=lambda x: x[0].pattern):
            doc = "\n```%s```\n" % v.__doc__ if verbose and v.__doc__ else ""
            pattern = p.pattern if not v.__doc__ else re.findall(".*?Command: (.*?)\n", v.__doc__, re.MULTILINE)[0]
            helps += [u' \u2022 {0}{1}'.format("`%s`" % pattern, doc)]
        return '\n'.join(to_utf8(helps))

    def _help_reply(self, msg) -> None:
        default_reply = u"Hi there, I'm %s." % self._client.login_data['self']['name']
        txt = '\n'.join(to_utf8([default_reply, self._get_plugins_help()]))
        self._client.rtm_send_message(msg['channel'], txt)

    def _get_default_answer(self, msg) -> str:
        default_reply = u'Bad command "%s".' % msg['text']
        help_explanation = u"For more information, feel free to ask me for `help`"
        parts = [default_reply, self._get_plugins_help(verbose=False), help_explanation]
        return '\n'.join(to_utf8(parts))

    def _default_reply(self, msg) -> None:
        self._client.rtm_send_message(msg['channel'], self._get_default_answer(msg))

    def dispatch_msg(self, msg) -> None:
        category = msg[0]
        msg = msg[1]
        text = msg['text']

        if (not self.debug and text.startswith("test|")) or (self.debug and not text.startswith("test|")):
            return
        if self.debug and text.startswith("test|"):
            text = text[len("test|"):]

        if text.lower() == "help":
            self._help_reply(msg)
            return

        responded = False
        for func, args in self._plugins.get_plugins(category, text):
            if func:
                responded = True
                try:
                    func(MessageWrapper(self._client, msg), *args, **self._registered_keywords)
                except Exception as ex:
                    logger.exception('failed to handle message %s with plugin "%s"', text, func.__name__)
                    reply = '[%s] I have problem when handling "%s"\n' % (func.__name__, text)
                    if self.debug:
                        reply += '```\n%s\n```' % traceback.format_exc()
                    else:
                        reply += '```%s```' % ex
                    self._client.rtm_send_message(msg['channel'], reply)

        if not responded and category == 'respond_to':
            self._default_reply(msg)

    def register(self, keyword: str, value):
        self._registered_keywords[keyword] = value


class MessageWrapper(Message):
    def __init__(self, *args, **kwargs):
        super(MessageWrapper, self).__init__(*args, **kwargs)

    @property
    def sender(self):
        if 'username' in self._body:
            return self._body['username']
        return self._client.users[self._body["user"]]["name"]

    def reply_code(self, text: str) -> None:
        return self.reply("```%s```" % text)

    def reply(self, text: str, attachment_path: str = None, attachment_name: str = None) -> None:
        text = self.gen_reply(text)
        if attachment_path:
            self._client.upload_file(self._body['channel'], attachment_name or attachment_path, attachment_path, text)
        else:
            self.send(text)
