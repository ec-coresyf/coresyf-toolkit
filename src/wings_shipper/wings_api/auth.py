"""Manages basic authentication with wings client"""
import requests


class Auth(object):
    """A class to authenticate users through wings"""
    def __init__(self, server, userid):
        """ Constructor for the auth class.
        Initializes a session to be used with wings.
        """
        self.session = requests.Session()
        self.server = server
        self.userid = userid

    def login(self, password):
        """Performs a request to wings to login a user"""
        response = self.session.get(self.server + '/sparql')
        data = {
            'j_username': self.userid,
            'j_password': password
        }
        response = self.session.post(self.server + '/j_security_check', data)
        if response.status_code != 200 and response.status_code != 403:
            return False
        return True

    def logout(self):
        """Logs out form wings on the current session"""
        self.session.get(self.server + '/jsp/logout.jsp')
