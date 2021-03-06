from slackbot.dispatcher import Message


class MessageWrapper(Message):
    def __init__(self, slack_client, body):
        super(MessageWrapper, self).__init__(slack_client, body)

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

