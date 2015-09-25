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

import logging
from jira import JIRA
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from openerp.addons.connector.exception import (NetworkRetryableError,
                                                RetryableJobError)
from datetime import datetime
_logger = logging.getLogger(__name__)


JIRA_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


recorder = {}


def call_to_key(method, arguments):
    """ Used to 'freeze' the method and arguments of a call to Jira
    so they can be hashable; they will be stored in a dict.

    Used in both the recorder and the tests.
    """
    def freeze(arg):
        if isinstance(arg, dict):
            items = dict((key, freeze(value)) for key, value
                         in arg.iteritems())
            return frozenset(items.iteritems())
        elif isinstance(arg, list):
            return tuple([freeze(item) for item in arg])
        else:
            return arg

    new_args = []
    for arg in arguments:
        new_args.append(freeze(arg))
    return (method, tuple(new_args))


def record(method, arguments, result):
    """ Utility function which can be used to record test data
    during synchronisations. Call it from JiraCRUDAdapter._call

    Then ``output_recorder`` can be used to write the data recorded
    to a file.
    """
    recorder[call_to_key(method, arguments)] = result


def output_recorder(filename):
    import pprint
    with open(filename, 'w') as f:
        pprint.pprint(recorder, f)
    _logger.debug('recorder written to file %s', filename)


class JiraLocation(object):

    def __init__(self, location, oauth_id,):
        self._location = locatio
        self.oauth_id = oauth_id

    @property
    def location(self):
        return self.oauth_id.client


class JiraCRUDAdapter(CRUDAdapter):
    """ External Records Adapter for Jira """

    def __init__(self, connector_env):
        """

        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(JiraCRUDAdapter, self).__init__(connector_env)
        self.jira = self.backend_record.client

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, id, data):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, id):
        """ Delete a record on the external system """
        raise NotImplementedError

    def _call(self, api_path, post_data=False):
        try:
            _logger.debug("Start calling Jira api %s", method)
            
            with self.jira() as api:
                
                start = datetime.now()
                try:
                    if post_data:
                        result = api.post(api_path, post_data)
                    else:
                        result = api.get(api_path, )
                except:
                    _logger.error("api.call(%s, %s) failed", api_path, post_data)
                    raise
                else:
                    _logger.debug("api.call(%s, %s) returned %s in %s seconds",
                                  api_path, post_data, result,
                                  (datetime.now() - start).seconds)
                # Uncomment to record requests/responses in ``recorder``
                # record(method, arguments, result)
                return result
        except:
            raise   #   @TODO
        #     
        # except (socket.gaierror, socket.error, socket.timeout) as err:
        #     raise NetworkRetryableError(
        #         'A network error caused the failure of the job: '
        #         '%s' % err)
        # except xmlrpclib.ProtocolError as err:
        #     if err.errcode in [502,   # Bad gateway
        #                        503,   # Service unavailable
        #                        504]:  # Gateway timeout
        #         raise RetryableJobError(
        #             'A protocol error caused the failure of the job:\n'
        #             'URL: %s\n'
        #             'HTTP/HTTPS headers: %s\n'
        #             'Error code: %d\n'
        #             'Error message: %s\n' %
        #             (err.url, err.headers, err.errcode, err.errmsg))
        #     else:
        #         raise


class GenericAdapter(JiraCRUDAdapter):

    _model_name = None
    _jira_model = None
    _admin_path = None

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('%s.search' % self._jira_model,
                          [filters] if filters else [{}])

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        arguments = [int(id)]
        if attributes:
            # Avoid to pass Null values in attributes. Workaround for
            # https://bugs.launchpad.net/openerp-connector-jira/+bug/1210775
            # When Jira is installed on PHP 5.4 and the compatibility patch
            # http://jira.com/blog/jira-news/jira-now-supports-php-54
            # is not installed, calling info() with None in attributes
            # would return a wrong result (almost empty list of
            # attributes). The right correction is to install the
            # compatibility patch on Jira.
            arguments.append(attributes)
        return self._call('%s.info' % self._jira_model,
                          arguments)

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        return self._call('%s.list' % self._jira_model, [filters])

    def create(self, data):
        """ Create a record on the external system """
        return self._call('%s.create' % self._jira_model, [data])

    def write(self, id, data):
        """ Update records on the external system """
        return self._call('%s.update' % self._jira_model,
                          [int(id), data])

    def delete(self, id):
        """ Delete a record on the external system """
        return self._call('%s.delete' % self._jira_model, [int(id)])

    def admin_url(self, id):
        """ Return the URL in the Jira admin for a record """
        if self._admin_path is None:
            raise ValueError('No admin path is defined for this record')
        backend = self.backend_record
        url = backend.admin_location
        if not url:
            raise ValueError('No admin URL configured on the backend.')
        path = self._admin_path.format(model=self._jira_model,
                                       id=id)
        url = url.rstrip('/')
        path = path.lstrip('/')
        url = '/'.join((url, path))
        return url
