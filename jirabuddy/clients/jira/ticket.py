from typing import List

from jira import Comment, Issue
from pandas import DataFrame

from .utils import jira_time_format
from ...common.enum import enum


class Ticket(Issue):
    def __init__(self, client, key: str = None, **kwargs):
        super(Ticket, self).__init__(client._options, client._session)
        self.find(key, params=kwargs)
        self.client = client
        self.key = self.raw['key']
        self.link = f"{self.client.server}/browse/{self.key}"

    def comment(self, message: str) -> None:
        self.client.add_comment(self.key, message)

    def get_comments(self) -> List[Comment]:
        return self.client.comments(self.key)

    def get_history_dataframe(self, include_comments: bool = True) -> DataFrame:
        self.find(self, {"expand": "changelog"})
        hst = []
        for change_log in self.changelog.histories:
            for cl in change_log.items:
                hst.append((jira_time_format(change_log.created), change_log.author.key, cl.field,
                            cl.__dict__["from"] or cl.fromString, cl.to or cl.toString))
        if include_comments:
            for c in self.get_comments():
                hst.append((jira_time_format(c.created), c.author.key, "comment", "", c.body))
        return DataFrame(hst if hst else None, columns=["time", "user", "field", "from", "to"]).sort("time")

    @property
    def f(self):
        super_dict = self.fields.__dict__
        super_fields = {self.client.FieldsByKey.__dict__.get(key, key): value for key, value in super_dict.items() if
                        not key.startswith("__")}
        return enum("TicketFields", **super_fields)
