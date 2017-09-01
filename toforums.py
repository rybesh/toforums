#! /bin/sh
"exec" "`dirname $0`/bin/python" "$0" "$@"

from __future__ import print_function
import httplib2
import os
import string

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


class Gmail:

    def __init__(self):
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def list_messages(self):
        return self.service\
                   .users()\
                   .messages()\
                   .list(userId='me', q='in:inbox -category:forums')\
                   .execute()\
                   .get('messages', [])

    def get_headers(self, message_id):
        return self.service\
                   .users()\
                   .messages()\
                   .get(userId='me', id=message_id, format='metadata')\
                   .execute()['payload']['headers']

    def add_labels(self, message_id, labels):
        self.service\
            .users()\
            .messages()\
            .modify(userId='me', id=message_id,
                    body={'addLabelIds': labels, 'removeLabelIds': []})\
            .execute()


def match(header, name, value):
    if header['name'] == name and value in header['value']:
        return True
    if (name == 'To'):
        return match(header, 'CC', value)
    return False


def process(gmail, messages, category):
    with open(os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)), 'to%s.txt' % category)) as f:
        criteria = [map(string.strip, line.split(':'))
                    for line in f.readlines()]

    for message in messages:
        for header in gmail.get_headers(message['id']):
            for name, value in criteria:
                if match(header, name, value):
                    gmail.add_labels(
                        message['id'], ['CATEGORY_%s' % category.upper()])


def main():
    gmail = Gmail()
    messages = gmail.list_messages()
    for category in ['forums', 'promotions']:
        process(gmail, messages, category)


if __name__ == '__main__':
    main()
