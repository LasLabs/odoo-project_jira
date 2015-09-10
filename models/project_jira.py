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
from oauth_hook import OAuthHook
from Crypto.PublicKey import RSA
from urlparse import parse_qsl
import requests


class ProjectJiraOauth(models.Model):
    ''' Handle OAuth for Jira '''
    _name = 'project.jira.oauth'
    _description = 'Handles OAuth Logic For Jira Project'
    
    RSA_BITS = 4096
    KEY_LEN = 256
    OAUTH_BASE = 'plugins/servlet/oauth'
    REST_VER = '2'
    REST_BASE = 'rest/api'
    
    def __compute_default_consumer_key_val(self, ):
        ''' Generate a rnd consumer key of length self.KEY_LEN '''
        return urandom(self.KEY_LEN).encode('hex')

    consumer_key = fields.Char(default=__compute_default_consumer_key_val,
                               readonly=True)
    private_key = fields.Char(readonly=True)
    public_key = fields.Char(readonly=True)
    
    request_token = fields.Char(readonly=True)
    request_secret = fields.Char(readonly=True)
    auth_uri = fields.Char(readonly=True)
    
    access_token = fields.Char(readonly=True)
    access_secret = fields.Char(readonly=True)
    
    company_id = fields.Many2one('res.company')
    jira_project_ids = fields.Many2one('project.jira.project')
    uri = fields.Char()
    
    @api.one
    def __create_rsa_key_vals(self, ):
        ''' Create public/private RSA keypair   '''
        private = RSA.generate(self.RSA_BITS)
        self.public_key = private.publickey().exportKey()
        self.private_key = private.exportKey()
    
    @api.one
    def _do_oauth_leg_1(self, ):
        ''' Perform OAuth step1 to get req_token, req_secret, and auth_uri '''
        
        self.__create_rsa_key_vals() #< Gen new keypairs
        oauth_hook = OAuthHook(
            consumer_key=self.consumer_key, consumer_secret='',
            key_cert = self.private_key, header_auth=True
        )
        req = requests.post(
            '%s/%s/request-token' % (self.uri, self.OAUTH_BASE),
            verify=self.uri.startswith('https'),
            hooks={'pre_request': oauth_hook}
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
                self.uri, self.OAUTH_BASE
            ),
        })
       
    @api.one 
    def _do_oauth_leg_3(self, ):
        ''' Perform OAuth step 3 to get access_token and secret '''
        
        oauth_hook = OAuthHook(
            consumer_key=self.consumer_key, consumer_secret='',
            access_token=self.request_token,
            access_token_secret=self.request_secret,
            key_cert=self.private_key, header_auth=True 
        )
        req = requests.post(
            '%s/%s/access-token' % (self.uri, self.OAUTH_BASE),
            hooks={'pre_request': oauth_hook}
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
        
    @api.model
    def create(self, vals):
        ''' Hook into create, start oauth process & validate '''
        rec = super(ProjectJiraOauth, self).create(vals)
        rec._do_oauth_leg_1()
        
    @api.one
    def write(self, vals):
        ''' Hook into write, update oauth on URI change '''
        super(ProjectJiraOauth, self).write(vals)
        if vals.get('uri'):
            self._do_oauth_leg_1()
            
            
class ProjectJiraProject(models.Model):
    _name = 'project.jira.project'
    jira_id = fields.One2many('project.jira.oauth', 'jira_project_ids')
    project_ids = fields.One2many('project.project', 'jira_project_id')


class ProjectProject(models.Model):
    _inherit = 'project.project'
    jira_project_id = fields.Many2one('project.jira.project')

# 
# class ProjectTask(models.Model):
#     _inherit = 'project.task'


class ResCompany(models.Model):
    _inherit = 'res.company'
    jira_oauth_ids = fields.One2many('project.jira.oauth', 'company_id')