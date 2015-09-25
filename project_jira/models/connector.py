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
from openerp import models, fields
from openerp.addons.connector.connector import Environment
from openerp.addons.connector.checkpoint import checkpoint


class JiraBinding(models.AbstractModel):
    _name = 'jira.binding'
    _inherit = 'external.binding'
    _description = 'Jira Abstract Binding'
    
    # 'openerp_id': openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='coffee.backend',
        string='Coffee Backend',
        required=True,
        ondelete='restrict',
    )
    jira_id = fields.Int(string='ID in Jira',
                            select=True)


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with. """
    backend_record = session.env['coffee.backend'].browse(backend_id)
    env = Environment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env


def add_checkpoint(session, model_name, record_id, backend_id):
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'coffee.backend', backend_id)