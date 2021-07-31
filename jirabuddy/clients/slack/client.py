import requests
from slacker import Slacker

upload_file_api = 'https://slack.com/api/files.upload'


class SlackClient(Slacker):
    def __init__(self, default_channel: str, alerts_channel: str, user_name: str, token: str):
        self.default_channel = default_channel
        self.alerts_channel = alerts_channel
        self.username = user_name
        self.token = token
        super().__init__(self.token)

    def channels_by_name(self):
        return {c['name']: c['id'] for c in self.channels.list().body['channels']}

    @property
    def default_channel_id(self):
        return self.channels_by_name()[self.default_channel[1:]]

    @property
    def alerts_channel_id(self):
        return self.channels_by_name()[self.alerts_channel[1:]]

    def send_to_slack(self, response, channel_id=None, channel=None):
        channel_id = channel_id or channel or self.default_channel_id
        return self.chat.post_message(channel_id, response, self.username, True)

    def post_file_to_slack(self, descriptor, filename='file', channel_id=None, channel=None, filetype='png', read=True):
        if channel:
            channel = channel[1:] if channel[0] in ['@', '#'] else channel
        channel_id = channel_id or self.channels_by_name().get(channel, None) or self.default_channel_id
        payload = {'channels': channel_id, 'token': self.token, 'filename': filename, 'filetype': filetype}
        if read:
            descriptor = descriptor.read()
        return requests.post(upload_file_api, data=payload, files={'file': descriptor})

    def post_snippet_to_slack(self, content, channel_id=None, channel=None, title=None):
        channel_id = channel_id or channel or self.default_channel_id
        return self.files.post('files.upload', data={'content': content, 'channels': channel_id, 'title': title})
