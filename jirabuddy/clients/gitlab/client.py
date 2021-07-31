import gitlab
import gitlab.v4.objects

from ...common.enum import to_enumable


class GitLabClientWrapper(object):
    def __init__(self, url: str, token: str, default_project=None):
        self._client = gitlab.Gitlab(url, private_token=token)

        self._projects = None
        self._users = None
        self._project: [gitlab.v4.objects.projects.Project, None] = None
        self._merge_requests = None

        if default_project:
            self.project = default_project

    @property
    def projects(self):
        if not self._projects:
            self._projects = to_enumable(name="gitlabProjects",
                                         key="_attrs.name",
                                         value=None,
                                         iterable=self._client.projects.list(all=True))
        return self._projects

    @property
    def users(self):
        if not self._users:
            self._users = to_enumable(name="gitlabUsers",
                                      key="_attrs.name",
                                      value=None,
                                      iterable=self._client.users.list(all=True))
        return self._users

    @property
    def project(self) -> gitlab.v4.objects.projects.Project:
        if not self._project:
            raise RuntimeError("project must be set")
        return self._project

    @project.setter
    def project(self, project: [str, gitlab.v4.objects.projects.Project]):
        if isinstance(project, str):
            if project in self.projects.names:
                project: gitlab.v4.objects.projects.Project = self.projects[project]
            else:
                raise RuntimeError("unknown project %s. known projects: %s", project, self.projects.names)
        self._project = project
