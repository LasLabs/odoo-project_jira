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


class ProjectTask(models.Model):
    '''
        @TODO
    '''
    _inherit = 'project.task'

    @api.model
    def pull_remote(self, date_from, date_to=None, updated=True):
        '''
        Get projects from remote JIRA instance, create locally if unknown
        @param  date_from   datetime    Search from date
        @param  date_to     datetime    Search to date
        @param  updated     bool    Search for updated date? (otherwise create)
        @throws EnvironmentError    On missing parent data,
                                    such as a task without a project
        @TODO: abstract this
        '''

        search_col = 'updated' if updated else 'created'
        domain = ['%s >= %s' % (search_col,ields.Datetime.to_string(date_from))]
        if date_to is not None:
            domain.append(
                '%s <= %s' % (search_col, fields.Datetime.to_string(date_to))
            )
        domain = ' AND '.join(domain)

        for jira_id in self.env['project.jira.project'].search([]):

            oauth_id = jira_id.oauth_id
            jira_issues = oauth_id.client.search_issues(
                '%s AND project = %s' % (domain, jira_id.key)
            )

            for jira_issue in jira_issues:
                
                fields = jira_issue.fields
                vals_issue = {
                    'company_id': oauth_id.company_id,
                    'delay_hours': fields.timeestimate,
                    'delegated_user_id': oauth_id.client.search_users()
                }
                domain = [(key, '=', val) for key, val in vals_issue.items()]
                existing_project = self.search(domain)
    
                if not existing_project:
                    existing_project = self.create(vals_issue)
