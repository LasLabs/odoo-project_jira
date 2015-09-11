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
from urlparse import parse_qsl
import requests

            
class ProjectJiraProject(models.Model):
    _name = 'project.jira.project'
    jira_id = fields.One2many('project.jira.oauth', 'jira_project_ids')
    project_ids = fields.One2many('project.project', 'jira_project_id')
