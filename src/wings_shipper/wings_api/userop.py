"""Contains class to perform user related operations in wings"""
from .auth import Auth


class UserOperation(Auth):
    """A class to manage user operations when making requests to wings."""

    def __init__(self, server, userid, domain):
        """Initializes the user operation class"""
        super(UserOperation, self).__init__(server, userid)
        self.domain = domain

    def get_request_url(self):
        """Builds an URL to make requests to Wings"""
        return '{}/users/{}/{}/'.format(
            self.server, self.userid, self.domain)

    def get_export_url(self):
        """Builds an URL with exports for the user"""
        return 'http://localhost:8080/wings/export/users/{}/{}/'.format(
            self.userid, self.domain)