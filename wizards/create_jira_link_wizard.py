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
from Crypto.PublicKey import RSA
from urlparse import parse_qsl
import requests


class ProjectJiraOauthWizard(models.TransientModel):
    ''' Handle OAuth for Jira '''
    _name = 'project.jira.oauth.wizard'
    _description = 'Wizard to create connection and perform Oauth dance'
    
    def _compute_default_session(self, ):
        return self.env['res.company'].browse(self._context.get('active_id'))
    
    def _compute_default_auth_uri(self, ):
        return self.oauth_id.auth_uri
    
    oauth_id = fields.Many2one('project.jira.oauth')
    company_id = fields.Many2one('res.company',
                                 default=_compute_default_session)
    state = fields.Selection([
        ('new', 'New Creation'),
        ('leg_2', 'OAuth Authorization'),
        ('done', 'Complete')
    ], default='new')
    auth_uri = fields.Char(related='oauth_id.auth_uri')
    name = fields.Char()
    uri = fields.Char()
    verify_ssl = fields.Boolean(string='Verify SSL?', default=True)
    
    @api.one
    def do_oauth_leg_1(self, ):
        ''' '''
        oauth_id = self.env['project.jira.oauth'].create({
            'name': self.name,
            'uri': self.uri,
            'company_id': self.company_id.id,
            'verify_ssl': self.verify_ssl
        })
        
        self.write({
            'state': 'leg_2',
            'oauth_id': oauth_id,
        })
            
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'project.jira.oauth.wizard',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self._context,
        }
    
    @api.one
    def do_oauth_leg_3(self, ):
        ''' '''
        self.oauth_id._do_oauth_leg_3()
        self.state = 'done'
        return {'type': 'ir.actions.act_window_close'}