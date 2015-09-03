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
from jira.packages.requests_oauth.hook import OAuthHook
from Crypto.PublicKey import RSA
from urlparse import parse_qsl
import requests


class ProjectJiraOauthWizard(models.TransientModel):
    ''' Handle OAuth for Jira '''
    _name = 'project.jira.oauth.wizard'
    _description = 'Second leg of Oauth Dance'
    
    def _default_session(self, ):
        self.env['project.jira.oauth'].browse(self._context.get('active_id'))
    
    @api.one
    def _do_oauth_leg_2(self, ):
        ''' '''
        self.env['']