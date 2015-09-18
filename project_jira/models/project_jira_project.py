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


class ProjectJiraProject(models.Model):
    '''
        @TODO
    '''
    _name = 'project.jira.project'
    _description = 'Project methods and data specific to JIRA'

    oauth_id = fields.One2many(
        'project.jira.oauth', 'jira_project_ids', required=True, readonly=True
    )
    project_id = fields.One2many('project.project', 'jira_project_id')

    key = fields.Char(
        string='JIRA Project Key', required=True, readonly=True
    )
    name = fields.Char(
        string='JIRA Project Name', required=True, readonly=True
    )

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

        #   @TODO: Find a way to search issues. I think this is JIRA API issue
        # search_col = 'updated' if updated else 'created'
        # domain = [(search_col, '>=', date_from)]
        # if date_to is not None:
        #     domain.append((search_col, '<=', date_to))

        #   @TODO: add some sort of filtering or something?
        for oauth_id in self.env['project.jira.oauth'].search([]):
            jira_projects = oauth_id.client.projects.projects()

            for jira_project in jira_projects:

                vals_project = {
                    'key': jira_project.key,
                    'name': jira_project.name,
                    'oauth_id': self.id,
                }
                domain = [(key, '=', val) for key, val in vals_project.items()]
                existing_project = self.search(domain)
    
                if not existing_project:
                    existing_project = self.create(vals_project)
