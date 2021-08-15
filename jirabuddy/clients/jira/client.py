import random
from typing import List, Optional, Union

import jira
import logging

from jira import JIRAError
from time import sleep

from .ticket import Ticket
from .utils import ObliviousCookieJar
from ...common.enum import to_enumable

DEV_STATUS_API_PATH = "{server}/rest/dev-status/latest/{path}"
JIRA_SERVER_ERRORS_TO_RETRY = (500, 504)


class JiraClient(jira.client.JIRA):
    def __init__(self, server: str, username: str, password: str, lazy: bool = False, *args, **kwargs):
        self._current_project: [str, None] = kwargs.pop("default_project", None)
        super().__init__(basic_auth=(username, password),
                         options={"server": server,
                                  "verify": kwargs.pop("ca_bundle", True)},
                         *args, **kwargs)
        self.server: str = server
        self._session.cookies = ObliviousCookieJar()
        self._current_user: str = username
        self._current_ticket: [Ticket, None] = None
        self.TicketTypes = None
        self.Priorities = None
        self.Components = None
        self.Projects = None
        self.FixVersions = None
        self.FieldsByKey = None
        self.FieldsByName = None
        self.Statuses = None
        self.EpicLinks = None

        if not lazy:
            self.load()

    def load(self):
        if not self.TicketTypes:
            self.TicketTypes = to_enumable("TicketTypes", "name", "name", self.issue_types())
        if not self.Priorities:
            self.Priorities = to_enumable("Priority", "name", "name", self.priorities())
        if not self.Projects:
            self.Projects = to_enumable("Projects", "name", "key", self.projects())
        if not self.FieldsByName:
            self.FieldsByName = to_enumable("Fields", "name", "id", self.fields())
        if not self.FieldsByKey:
            self.FieldsByKey = to_enumable("Fields", "id", "name", self.fields(), clean_values=True)
        if not self.Statuses:
            self.Statuses = to_enumable("Statuses", "name", "id", self.statuses())

        if self._current_project:
            if not self.Components:
                self.Components = to_enumable("Components", "name", "id",
                                              self.project_components(self._current_project))
            if not self.FixVersions:
                self.FixVersions = to_enumable("FixVersions", "name", "name",
                                               self.project_versions(self._current_project))

    def set_project(self, project: str) -> None:
        self._current_project = project

    def set_ticket(self, key: str, **kwargs) -> None:
        self._current_ticket = Ticket(client=self, key=key, **kwargs)

    def get_ticket(self, key: str = None, **kwargs) -> Ticket:
        if ("http://" in key or "https://" in key) and r"/browse/" in key:
            key = key.split(r"/")[-1]
            if "|" in key:
                key = key.split("|")[0]
        return Ticket(client=self, key=key, **kwargs) if key else self._current_ticket

    def search_tickets(self, jql: str, fields=None, *args, **kwargs):
        try:
            jira_issues = self.search_issues(jql, fields=fields, *args, **kwargs)
        except JIRAError as e:
            if e.status_code in JIRA_SERVER_ERRORS_TO_RETRY:  # Jira sometimes returns internal server error, retry once if so
                logging.error('Retrying: %s' % e.__str__())
                sleep(random.randint(1, 5))
                jira_issues = self.search_issues(jql, fields=fields, *args, **kwargs)  # raise if 500 returned again
            else:
                raise
        return [self.get_ticket(issue.key, fields=fields) for issue in jira_issues]

    def comment(self, message: str, ticket_key: str = None) -> None:
        self.get_ticket(key=ticket_key).comment(message)

    def create_ticket(self,
                      summary: str,
                      ticket_type: str = "Task",
                      description: str = "",
                      project: str = None,
                      assignee: str = None,
                      reporter: str = None,
                      priority: str = None,
                      components: Optional[Union[List[str], str]] = None,
                      fix_versions: Optional[Union[List[str], str]] = None,
                      **kwargs) -> Ticket:

        fields_kwargs = dict(summary=summary,
                             project={'key': project or self._current_project},
                             issuetype={'name': ticket_type},
                             description=description)
        if assignee:
            fields_kwargs["assignee"] = {'name': assignee} or None

        if reporter:
            fields_kwargs["reporter"] = {'name': reporter} or None

        if priority:
            fields_kwargs["priority"] = {'name': priority}

        if fix_versions:
            if not isinstance(fix_versions, list):
                fix_versions = [self.FixVersions.get(fv) for fv in fix_versions]
            fields_kwargs["fixVersions"] = [{"name": fv} for fv in fix_versions]

        if components:
            if not isinstance(components, list):
                components = [self.Components.get(cm) for cm in components.split(",")]
            fields_kwargs["components"] = [{"id": cm} for cm in components]

        fields_kwargs.update(kwargs)
        issue = self.create_issue(**fields_kwargs)
        return self.get_ticket(issue.key)
