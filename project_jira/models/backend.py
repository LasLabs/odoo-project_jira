# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dave Lasley <dave@laslabs.com>
#    Copyright: 2015 LasLabs, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from os import urandom
from oauthlib.oauth1 import SIGNATURE_RSA
from requests_oauthlib import OAuth1
from Crypto.PublicKey import RSA
from jira import JIRA
from urlparse import parse_qsl
import requests
import openerp.addons.connector.backend as backend


jira = backend.Backend('jira')
""" Generic Jira Backend """

jira2 = backend.Backend(parent=jira, version='2')
""" Jira Backend for Api Version 2 """


class JiraSession(OAuth1Session):
    ''' Inherit Oauth1Session for more convenient API usage '''

    def __init__(self, api_uri, private_key, *args, **kwargs):
        super(JiraSession, self).__init__(private_key, *args, **kwargs)
        self.uri = uri

    def get(self, api_path, *args, **kwargs):
        if isinstance(api_path, list):
            api_path = '/'.join(api_path)
        uri = '%s/%s/' % (self.uri, api_path)
        resp = super(JiraSession, self).get(uri, *args, **kwargs)
        #   @TODO: Error handling
        return resp.json()
    
    def post(self, api_path, post_data, *args, **kwargs):
        if isinstance(api_path, list):
            api_path = '/'.join(api_path)
        uri = '%s/%s/' % (self.uri, api_path)
        resp = super(JiraSession, self).post(uri, post_data, *args, **kwargs)
        #   @TODO: Error handling
        return resp.json()


class JiraBackend(models.Model):
    ''' Handle OAuth for Jira '''
    _name = 'jira.backend'
    _description = 'Handles OAuth Logic For Jira Project'
    _inherit = 'connector.backend'

    _backend_type = 'jira'

    RSA_BITS = 4096
    KEY_LEN = 255   # 255 == max Atlassian db col len
    OAUTH_BASE = 'plugins/servlet/oauth'
    REST_VER = '2'
    REST_BASE = 'rest/api'

    def __compute_default_consumer_key_val(self, ):
        ''' Generate a rnd consumer key of length self.KEY_LEN '''
        return urandom(self.KEY_LEN).encode('hex')[:self.KEY_LEN]
    
    @api.one
    def _compute_oauth_client(self, ):
        ''' Return JIRA session, create if one isn't established
            @return jira.JIRA
        '''

        if self.uri:

            oauth = {
                'access_token': self.access_token,
                'access_token_secret': self.access_secret,
                'consumer_key': self.consumer_key,
                'key_cert': self.private_key,
            }
            options = {
                'server': self.uri,
                'verify': self.verify_ssl,
            }

            self.client = JIRA(options, oauth=oauth)

    consumer_key = fields.Char(default=__compute_default_consumer_key_val,
                               readonly=True)
    private_key = fields.Text(readonly=True)
    public_key = fields.Text(readonly=True)

    request_token = fields.Char(readonly=True)
    request_secret = fields.Char(readonly=True)
    auth_uri = fields.Char(readonly=True)

    access_token = fields.Char(readonly=True)
    access_secret = fields.Char(readonly=True)

    company_id = fields.Many2one('res.company')
    jira_project_ids = fields.Many2one('project.jira.project')
    uri = fields.Char()
    location = fields.Char(related='uri')  #  < @TODO: GET RID OF THIS!
    name = fields.Char()
    verify_ssl = fields.Boolean(default=True)
    client = fields.Binary(compute='_compute_oauth_client',
                           readonly=True, store=False)
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
    )

    @api.model
    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [('2', 'API Version 2'),]

    @api.one
    def create_rsa_key_vals(self, ):
        ''' Create public/private RSA keypair   '''
        private = RSA.generate(self.RSA_BITS)
        self.public_key = private.publickey().exportKey()
        self.private_key = private.exportKey()

    @api.one
    def _do_oauth_leg_1(self, ):
        ''' Perform OAuth step1 to get req_token, req_secret, and auth_uri '''

        oauth_hook = OAuth1(
            client_key=self.consumer_key, client_secret='',
            signature_method=SIGNATURE_RSA, rsa_key=self.private_key,
        )
        req = requests.post(
            '%s/%s/request-token' % (self.uri, self.OAUTH_BASE),
            verify=self.verify_ssl, auth=oauth_hook
        )
        resp = dict(parse_qsl(req.text))

        token = resp.get('oauth_token', False)
        secret = resp.get('oauth_token_secret', False)

        if False in [token, secret]:
            raise KeyError('Did not get token (%s) or secret (%s). Resp %s',
                           token, secret, resp)

        self.write({
            'request_token': token,
            'request_secret': secret,
            'auth_uri': '%s/%s/authorize?oauth_token=%s' % (
                self.uri, self.OAUTH_BASE, token
            ),
        })

    @api.one
    def _do_oauth_leg_3(self, ):
        ''' Perform OAuth step 3 to get access_token and secret '''

        oauth_hook = OAuth1(
            client_key=self.consumer_key, client_secret='',
            signature_method=SIGNATURE_RSA, rsa_key=self.private_key,
            resource_owner_key=self.request_token,
            resource_owner_secret=self.request_secret,
        )
        req = requests.post(
            '%s/%s/access-token' % (self.uri, self.OAUTH_BASE),
            verify=self.verify_ssl, auth=oauth_hook
        )
        resp = dict(parse_qsl(req.text))

        token = resp.get('oauth_token', False)
        secret = resp.get('oauth_token_secret', False)

        if False in [token, secret]:
            raise KeyError('Did not get token (%s) or secret (%s). Resp %s',
                           token, secret, resp)

        self.write({
            'access_token': token,
            'access_secret': secret,
        })
