from datetime import datetime

from requests.cookies import RequestsCookieJar


class JiraClientError(Exception):
    pass


class ObliviousCookieJar(RequestsCookieJar):
    def set_cookie(self, *args, **kwargs):
        """Simply ignore any request to set a cookie."""
        pass

    def copy(self):
        """Make sure to return an instance of the correct class on copying."""
        return ObliviousCookieJar()


def jira_time_format(time: str):
    return datetime.strptime(time[:-5], '%Y-%m-%dT%H:%M:%S.%f')
