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
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)


#  fields.Datetime.from(to)_string(from_date)


class ProjectJiraSync(models.Model):
    ''' Handle Syncing Logic '''
    _name = 'project.jira.sync'
    _description = 'Handles Syncing Logic For Jira'

    model_id = fields.Many2one('ir.model')
    last_sync = fields.Datetime(help='Last time model has pulled to remote')
    sync_order = fields.Int(help='Automatically detected sync order')

    SYNC_EVERY = timedelta(5)

    @api.model
    def pull_remotes(self, ):
        '''
        Loops models in the sync table and runs their pull_remote()
        '''

        now = datetime.now()
        now_str = fields.Datetime.to_string(now)
        date = now - self.SYNC_EVERY

        for rec in self.search([('last_sync', '<=', date)]):

            try:
                if rec.pull_remote:

                    if rec.pull_remote(now):
                        rec.last_sync = now_str

                    else:
                        #   @TODO something here
                        _logger.error(
                            "Some sort of error in %s.pull_remote(%s). @TODOs",
                            rec, now
                        )

                else:
                    #   @TODO something here
                    _logger.error(
                        "%s in syncing table, but doesn't implement pull_remote()",
                        rec
                    )

            except EnvironmentError as e:
            #   Needs parent data that will likely be filled with a sync
            #   Hopefully the logic should just stagger these eventually
                _logger.info('Missing parent data for %s, skipping. - %s',
                             rec, e)
                continue