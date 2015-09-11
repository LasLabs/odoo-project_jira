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

            
class ProjectJiraProject(models.Model):
    '''
        @TODO
    '''
    _name = 'project.jira.project'
    _description = 'Project methods and data specific to JIRA'
    
    jira_oauth_id = fields.One2many('project.jira.oauth', 'jira_project_ids',
                              required=True)
    project_ids = fields.One2many('project.project', 'jira_project_id')
    
    key = fields.Char(string='JIRA Project Key', required=True)
    name = fields.Char(string='JIRA Project Name', required=True)