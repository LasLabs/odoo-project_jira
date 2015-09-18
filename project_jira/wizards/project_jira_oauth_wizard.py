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
        ('leg_1', 'OAuth Remote Config'),
        ('leg_2', 'OAuth Remote Auth'),
        ('done', 'Complete')
    ], default='new')
    auth_uri = fields.Char(related='oauth_id.auth_uri')
    name = fields.Char()
    uri = fields.Char()
    verify_ssl = fields.Boolean(string='Verify SSL?', default=True)
    consumer_key = fields.Char(related='oauth_id.consumer_key')
    public_key = fields.Text(related='oauth_id.public_key')

    @api.model
    def __get_action(self, ):
        act = self.env['ir.actions.act_window'].for_xml_id(
            'project_jira', 'project_jira_oauth_launch_wizard'
        )
        act['res_id'] = self.id
        return act

    @api.multi
    def do_oauth_initial(self, ):
        ''' '''
        vals = {
            'name': self.name,
            'uri': self.uri,
            'company_id': self._context.get('active_id'),
            'verify_ssl': self.verify_ssl
        }
        oauth_id = self.env['project.jira.oauth'].create(vals)
        oauth_id.create_rsa_key_vals()  # Gen new keypairs

        self.write({
            'state': 'leg_1',
            'oauth_id': oauth_id.id,
        })

        return self.with_context(self._context).__get_action()

    @api.multi
    def do_oauth_leg_1(self, ):
        ''' '''
        self.oauth_id._do_oauth_leg_1()
        self.write({
            'state': 'leg_2',
        })
        return self.with_context(self._context).__get_action()

    @api.multi
    def do_oauth_leg_3(self, ):
        ''' '''
        self.oauth_id._do_oauth_leg_3()
        self.state = 'done'
        return self.with_context(self._context).__get_action()
