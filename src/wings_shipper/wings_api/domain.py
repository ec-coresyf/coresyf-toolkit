"""Contains a class to manage domains in wings"""
import os
from .auth import Auth
import re


class ManageDomain(Auth):
    """A class to manage Domains in wings"""

    def __init__(self, server, userid):
        super(ManageDomain, self).__init__(server, userid)

    def upload_domain_file(self, domain_zip_filepath):
        filename = os.path.basename(domain_zip_filepath)
        zip_file = {
            'file': (filename, open(domain_zip_filepath, 'rb'))
                    }
        form_data = {
            'name': filename,
            'type': 'domain',
        }
        upload_result = self.session.post(self.server + '/upload',
                                          data=form_data,
                                          files=zip_file)

        if upload_result.status_code != 200:
            raise Exception('Unable to upload domain file to Wings')

        file_location = upload_result.json()['location']
        return file_location

    def import_domain(self, url):
        file_location = url
        # Uploads the domain file to Wings if it is a local file
        if os.path.exists(url):
            file_location = self.upload_domain_file(url)

        data = {'domain': os.path.basename(url), 'location': file_location}
        response = self.session.post(self.server + '/users/' +
                                     self.userid + '/domains/importDomain',
                                     data)

        if response.status_code != 200:
            raise Exception('Unable to import domain to Wings')
        return response.json()

    def get_domain_details(self, domain):
        response = self.session.get(self.server + '/users/' + self.userid +
                                    '/domains/getDomainDetails?domain=' +
                                    domain)
        if response.text:
            return response.json()
        else:
            return None

    def get_selected_domain(self):
        """A dummy method to get the selected domain (It seems there is no
        available resource to retrieve the selected one)
        """
        response = self.session.get(self.server + '/users/' + self.userid +
                                    '/domains')
        if response.text:
            return re.search(r'DOMAIN_ID = "(.*)";', response.text).group(1)
        else:
            return None

    def select_default_domain(self, domain):
        data = {'domain': domain}
        response = self.session.post(self.server + '/users/' +
                                     self.userid + '/domains/selectDomain',
                                     data)
        if response.status_code != 200:
            raise Exception('Unable to select default domain')
        return response.text

    def delete_domain(self, domain):
        data = {'domain': domain}
        self.session.post(self.server + '/users/' +
                          self.userid + '/domains/deleteDomain', data)
