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
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create,
                                                  ImportMapper
                                                  )
from openerp.addons.connector.exception import IDMissingInBackend
from .unit.backend_adapter import (GenericAdapter,
                                   JIRA_DATETIME_FORMAT,
                                   )
from .unit.import_synchronizer import (DelayedBatchImporter,
                                       JiraImporter,
                                       )
from .unit.mapper import normalize_datetime
from .backend import jira
from .connector import get_environment


class JiraProjectProject(models.Model):
    
    _name = 'jira.project.project'
    _inherits = {'project.project': 'jira_id'}
    _description = 'JIRA Project'
    
    backend_id = fields.Many2one(
        comodel_name='jira.backend',
        string='JIRA backend',
        required=True,
        ondelete='restrict',
    )
    jira_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        ondelete='cascade',
    )
    sync_date = fields.Datetime(
        string='Last synchronization date'
    )


class ProjectProject(models.Model):
    
    _inherit = 'project.project'
    jira_bind_ids = fields.One2many(
        comodel_name='jira.project.project',
        inverse_name='jira_id',
        string='JIRA Bindings'
    )


@jira
class ProjectProjectAdapter(GenericAdapter):
    _model_name = 'jira.project.project'
    _jira_model = 'issue'

    def _call(self, method, arguments):
        try:
            return super(ProjectProjectAdapter, self)._call(
                method, arguments
            )
        except Exception as err:
            # this is the error in the Jira API
            # when the customer does not exist
            
            raise
            #   @TODO:
            # if err.faultCode == 102:
            #     raise IDMissingInBackend
            # else:
            #     raise

    def search(self, filters=None, from_date=None, to_date=None,
               jira_website_ids=None):
        """ Search records according to some criteria and return a
        list of ids
        :rtype: list
        """
        if filters is None:
            filters = {}

        dt_fmt = JIRA_DATETIME_FORMAT
        if from_date is not None:
            # updated_at include the created records
            filters.setdefault('updated_at', {})
            filters['updated_at']['from'] = from_date.strftime(dt_fmt)
        if to_date is not None:
            filters.setdefault('updated_at', {})
            filters['updated_at']['to'] = to_date.strftime(dt_fmt)
        if jira_website_ids is not None:
            filters['website_id'] = {'in': jira_website_ids}
            
        return self._call('customer.search',
                          [filters] if filters else [{}])


@jira
class ProjectProjectBatchImporter(DelayedBatchImporter):
    """ Import the Jira Projects.
    For every partner in the list, a delayed job is created.
    """
    _model_name = ['jira.project.project']

    def run(self, filters=None):
        """ Run the synchronization """
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        jira_website_ids = [filters.pop('jira_website_id')]
        record_ids = self.backend_adapter.search(
            filters,
            from_date=from_date,
            to_date=to_date,
            jira_website_ids=jira_website_ids)
        _logger.info('search for jira projects %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id)


ProjectProjectBatchImport = ProjectProjectBatchImporter  # deprecated


@jira
class ProjectProjectImportMapper(ImportMapper):
    _model_name = 'jira.project.project'

    direct = [
        #   ("from", "to")
    ]

    @only_create
    @mapping
    def openerp_id(self, record):
        """ Will bind the customer on a existing partner
        with the same email """
        partner = self.env['res.partner'].search(
            [('email', '=', record['email']),
             ('customer', '=', True),
             '|',
             ('is_company', '=', True),
             ('parent_id', '=', False)],
            limit=1,
        )
        if partner:
            return {'openerp_id': partner.id}


@jira
class ProjectProjectImporter(JiraImporter):
    _model_name = ['jira.res.partner']

    _base_mapper = ProjectProjectImportMapper

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        pass
        # record = self.jira_record
        # self._import_dependency(record['group_id'],
        #                         'jira.res.partner.category')

    def _after_import(self, partner_binding):
        """ Import the tasks? """
        pass


ProjectProjectImport = ProjectProjectImporter  # deprecated
