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
        if not theorical_dicts:
            return True

        # Prefetch fields.
        keys = list(theorical_dicts[0].keys())
        fields_names = [k for k in keys if '.' not in k]
        fields = self.env['ir.model.fields'].search([('name', 'in', fields_names), ('model', '=', records._name)])
        fields_map = dict(((f.name, f.model), f) for f in fields)

        def _get_field_value(record, key):
            # Retrieve the field and the end-path records.
            if '.' in key:
                # Manage composite fields.
                split = key.split('.')
                relational_key = '.'.join(split[:-1])
                field_name = split[len(split) - 1]
                end_records = record.mapped(relational_key)
            else:
                # Case of basic field.
                field_name = key
                end_records = record
            # Retrieve the ir.ui.fields record.
            if (field_name, end_records._name) in fields_map:
                field = fields_map[(field_name, end_records._name)]
            else:
                field = fields_map[(field_name, end_records._name)] =\
                    self.env['ir.model.fields'].search([('name', '=', field_name), ('model', '=', end_records._name)])
            return field, end_records

        def _get_matching_record(record, theorical_dicts):
            # Search for a theorical dict having same values as the record.
            for candidate in theorical_dicts:
                match = True
                for field_name in keys:
                    field, field_records = _get_field_value(record, field_name)

                    value = field_records.mapped(field.name)
                    candidate_value = candidate[field_name]

                    # Deal with x2many fields by comparing ids or calling check_complete_records recursively.
                    if field.ttype in ('one2many', 'many2many'):
                        if candidate_value and isinstance(candidate_value, list) and isinstance(candidate_value[0], dict):
                            if not self.check_complete_records(value, candidate_value):
                                match = False
                                break
                        elif not sorted(value.ids) == sorted(candidate_value or []):
                            match = False
                            break
                        continue

                    # Deal with many2one field.
                    if field.ttype == 'many2one':
                        if isinstance(candidate_value, dict):
                            if not self.check_complete_records(value, [candidate_value]):
                                match = False
                                break
                        elif (candidate_value or value) and value.id != candidate_value:
                            match = False
                            break
                        continue

                    value = value[0] if value else None
                    if field.ttype == 'float':
                        if not float_is_zero(value - candidate_value):
                            match = False
                            break
                    elif field.ttype == 'monetary':
                        currency_field = record._fields[field_name]
                        currency_field_name = currency_field._related_currency_field
                        currency = getattr(record, currency_field_name)
                        if currency.compare_amounts(value, candidate_value) if currency else value != candidate_value:
                            match = False
                            break
                    elif (candidate_value or value) and value != candidate_value:
                        match = False
                        break

                if match:
                    return candidate
            return None

        for record in records:
            matching_record = _get_matching_record(record, theorical_dicts)

            if matching_record:
                theorical_dicts.remove(matching_record)
            else:
                return False

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
