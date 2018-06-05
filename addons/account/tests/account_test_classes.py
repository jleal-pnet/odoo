# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo.tests.common import HttpCase, tagged
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class AccountingTestCase(HttpCase):
    """ This class extends the base TransactionCase, in order to test the
    accounting with localization setups. It is configured to run the tests after
    the installation of all modules, and will SKIP TESTS if it  cannot find an already
    configured accounting (which means no localization module has been installed).
    """

    def setUp(self):
        super(AccountingTestCase, self).setUp()
        domain = [('company_id', '=', self.env.ref('base.main_company').id)]
        if not self.env['account.account'].search_count(domain):
            _logger.warn('Test skipped because there is no chart of account defined ...')
            self.skipTest("No Chart of account found")

    def check_complete_records(self, records, theorical_dicts):
        ''' Compare records with theorical list of dictionaries representing the expected results.
        The dictionary uses field names as keys. Field names could be either applied on the record itself
        (e.g. 'debit') or a composite path to another records (e.g. 'move_id.line_ids.debit').
        Comparison for many2one field could be either an id [resp. a list of ids] or a dict [resp. a list of dict].

        :param records:             The records to compare.
        :param theorical_dicts:     The expected results as a list of dicts.
        :return:                    True if all is equivalent, False otherwise.
        '''
        if len(records) != len(theorical_dicts):
            raise ValidationError('Too many records to compare: %d != %d.' % (len(records), len(theorical_dicts)))

        def _get_matching_record(record_values, theorical_dicts):
            # Search for a theorical dict having same values as the record.
            index = 0
            for candidate in theorical_dicts:
                if candidate == record_values:
                    return index
                index += 1
            return False

        keys = list(theorical_dicts[0].keys())
        for record_values in records.read(keys, load=False):
            # remove 'id' field which is automatically added by read()
            del(record_values['id'])

            # search for matching values in theorical_dicts
            matching_index = _get_matching_record(record_values, theorical_dicts)
            if matching_index:
                theorical_dicts.remove(matching_index)
            else:
                return False

        # theorical_dicts should be empty, otherwise there are missing lines in checked records
        if theorical_dicts:
            return False
        return True

    def ensure_account_property(self, property_name):
        '''Ensure the ir.property targeting an account.account passed as parameter exists.
        In case it's not: create it with a random account. This is useful when testing with
        partially defined localization (missing stock properties for example)

        :param property_name: The name of the property.
        '''
        company_id = self.env.user.company_id
        field_id = self.env['ir.model.fields'].search(
            [('model', '=', 'product.template'), ('name', '=', property_name)], limit=1)
        property_id = self.env['ir.property'].search([
            ('company_id', '=', company_id.id),
            ('name', '=', property_name),
            ('res_id', '=', None),
            ('fields_id', '=', field_id.id)], limit=1)
        account_id = self.env['account.account'].search([('company_id', '=', company_id.id)], limit=1)
        value_reference = 'account.account,%d' % account_id.id
        if property_id and not property_id.value_reference:
            property_id.value_reference = value_reference
        else:
            self.env['ir.property'].create({
                'name': property_name,
                'company_id': company_id.id,
                'fields_id': field_id.id,
                'value_reference': value_reference,
            })
