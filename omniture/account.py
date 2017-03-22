""" omniture.accounts """

import binascii
import time
from hashlib import sha1
import json
from datetime import datetime
import requests

from .elements import Value, Element, Segment
from .query import Query
from .utils import AddressableList, memoize

# encoding: utf-8

class Account(object):
    """ Omniture user account """
    DEFAULT_ENDPOINT = 'https://api.omniture.com/admin/1.3/rest/'

    def __init__(self, username, secret, endpoint=DEFAULT_ENDPOINT):
        self.username = username
        self.secret = secret
        self.endpoint = endpoint
        #data = self.request('Company', 'GetReportSuites')['report_suites']
        #suites = [Suite(suite['site_title'], suite['rsid'], self) for suite in data]
        #self.suites = AddressableList(suites)

    def request(self, api, method, query=None):
        """ make Omniture request """
        if query is None:
            query = {}
        response = requests.post(
            self.endpoint,
            params={'method': api + '.' + method},
            data=json.dumps(query),
            headers=self._build_token()
            )
        return response.json()

    def _serialize_header(self, properties):
        """ Prepare header for request """
        header = []
        for key, value in properties.items():
            header.append('{key}="{value}"'.format(key=key, value=value))
        return ', '.join(header)

    def _build_token(self):
        """ build auth token """
        nonce = str(time.time())
        base64nonce = binascii.b2a_base64(binascii.a2b_qp(nonce))
        created_date = datetime.utcnow().isoformat() + 'Z'
        sha_object = sha1((nonce + created_date + self.secret).encode('utf-8'))
        password_64 = binascii.b2a_base64(sha_object.digest())

        properties = {
            "Username": self.username,
            "PasswordDigest": password_64.strip().decode('ascii'),
            "Nonce": base64nonce.strip().decode('ascii'),
            "Created": created_date,
        }
        header = 'UsernameToken ' + self._serialize_header(properties)

        return {'X-WSSE': header}


class Suite(Value):
    """ Class of available report suites """
    def request(self, api, method, query=None):
        """ request against a report suite """
        if query is None:
            query = {}
        raw_query = {}
        raw_query.update(query)
        if 'reportDescription' in raw_query:
            raw_query['reportDescription']['reportSuiteID'] = self.id
        elif api == 'ReportSuite':
            raw_query['rsid_list'] = [self.id]

        return self.account.request(api, method, raw_query)

    def __init__(self, title, rsid, account):
        super(Suite, self).__init__(title, rsid, account)

        self.account = account

    @property
    @memoize
    def metrics(self):
        """ return available metrics for report suite """
        data = self.request('ReportSuite', 'GetAvailableMetrics')[0]['available_metrics']
        return Value.list('metrics', data, self, 'display_name', 'metric_name')

    @property
    @memoize
    def elements(self):
        """ return available elements for report suite """
        data = self.request('ReportSuite', 'GetAvailableElements')[0]['available_elements']
        return Element.list('elements', data, self, 'display_name', 'element_name')

    @property
    @memoize
    def evars(self):
        """ return available evars for report suite """
        data = self.request('ReportSuite', 'GetEVars')[0]['evars']
        return Value.list('evars', data, self, 'name', 'evar_num')

    @property
    @memoize
    def segments(self):
        """ return available segments for report suite """
        data = self.request('ReportSuite', 'GetSegments')[0]['sc_segments']
        return Segment.list('segments', data, self, 'name', 'id')

    @property
    def report(self):
        """ return a report for report suite """
        return Query(self)
