# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero


class AccountReconcileModel(models.Model):
    _name = 'account.reconcile.model'
    _description = 'Preset to create journal entries during a invoices and payments matching'
    _order = 'sequence, id'

    # Base fields.
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(required=True, default=10)
    has_second_line = fields.Boolean(string='Add a second line', default=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    type = fields.Selection(selection=[
        ('manual', _('Create manually journal items on clicked button.')),
        ('write_off', _('Suggest an automatic write-off.')),
        ('invoices', _('Suggest a matching with existing invoices/bills.'))
    ], string='Type', default='manual', required=True)
    auto_reconcile = fields.Boolean(string='Reconcile Automatically',
        help='Reconcile the statement line with propositions automatically.')

    # ===== Conditions =====
    match_journal_ids = fields.Many2many('account.journal', string='Journals',
        domain="[('type', '=', 'bank')]",
        help='Restrict model to some journals.')
    nature = fields.Selection(selection=[
        ('amount_received', 'Amount Received'),
        ('amount_paid', 'Amount Paid'),
        ('both', 'Amount Paid/Received')
    ], string='Amount Nature', required=True, default='both', help='''Restrict model on amount nature:
        * Amount Received: Only applied when receiving an amount.
        * Amount Paid: Only applied when paying an amount.
        * Amount Paid/Received: Applied in both cases.''')
    match_amount = fields.Selection(selection=[
        ('lower', 'Is Lower Than'),
        ('greater', 'Is Greater Than'),
        ('between', 'Is Between'),
    ], string='Line Amount',
        help='Restrict to statement line amount being lower than, greater than or between specified amount(s).')
    match_amount_param = fields.Float(string='Amount Parameter')
    match_amount_second_param = fields.Float(string='Amount Second Parameter')
    match_label = fields.Selection(selection=[
        ('contains', 'Contains'),
        ('not_contains', 'Not Contains'),
        ('match_regex', 'Match Regex'),
    ], string='Line Label', help='''Restrict reconciliation propositions label on:
        * Contains: The proposition label must contains this string (case insensitive).
        * Not Contains: Negation of "Contains".
        * Match Regex: Define your own regular expression.''')
    match_label_param = fields.Char(string='Label Parameter')
    match_same_currency = fields.Boolean(string='Same Currency Matching', default=True,
        help='Restrict to propositions having the same currency as the statement line.')
    match_total_amount = fields.Boolean(string='Amount Matching', default=True,
        help='The sum of total residual amount propositions matches the statement line amount.')
    match_total_amount_param = fields.Float(string='Amount Matching %', default=100,
        help='The sum of total residual amount propositions matches the statement line amount under this percentage.')
    partner_is_set = fields.Boolean(string='Partner Is Set', help='Apply only when partner statement line is set.')
    match_partner_ids = fields.Many2many('res.partner', string='Partners',
        help='Restrict to some statement line partners.')
    match_partner_category_ids = fields.Many2many('res.partner.category', string='Partner Categories',
        help='Restrict to some statement line partner categories.')

    # ===== Write-Off =====
    # First part fields.
    account_id = fields.Many2one('account.account', string='Account', ondelete='cascade', domain=[('deprecated', '=', False)])
    journal_id = fields.Many2one('account.journal', string='Journal', ondelete='cascade', help="This field is ignored in a bank statement reconciliation.")
    label = fields.Char(string='Journal Item Label')
    amount_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage of balance')
        ], required=True, default='percentage')
    is_tax_price_included = fields.Boolean(string='Is Tax Included in Price', related='tax_id.price_include',
        help='Technical field used inside the view to make the force_tax_included field readonly if the tax is already price included.')
    tax_amount_type = fields.Selection(string='Tax Amount Type', related='tax_id.amount_type',
        help='Technical field used inside the view to make the force_tax_included field invisible if the tax is a group.')
    force_tax_included = fields.Boolean(string='Tax Included in Price',
        help='Force the tax to be managed as a price included tax.')
    amount = fields.Float(digits=0, required=True, default=100.0, help="Fixed amount will count as a debit if it is negative, as a credit if it is positive.")
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete='set null')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    # Second part fields.
    second_account_id = fields.Many2one('account.account', string='Second Account', ondelete='cascade', domain=[('deprecated', '=', False)])
    second_journal_id = fields.Many2one('account.journal', string='Second Journal', ondelete='cascade', help="This field is ignored in a bank statement reconciliation.")
    second_label = fields.Char(string='Second Journal Item Label')
    second_amount_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage of amount')
        ], string="Second Amount type",required=True, default='percentage')
    is_second_tax_price_included = fields.Boolean(string='Is Second Tax Included in Price', related='second_tax_id.price_include',
        help='Technical field used inside the view to make the force_second_tax_included field readonly if the tax is already price included.')
    second_tax_amount_type = fields.Selection(string='Second Tax Amount Type', related='second_tax_id.amount_type',
        help='Technical field used inside the view to make the force_second_tax_included field invisible if the tax is a group.')
    force_second_tax_included = fields.Boolean(string='Second Tax Included in Price',
        help='Force the second tax to be managed as a price included tax.')
    second_amount = fields.Float(string='Second Amount', digits=0, required=True, default=100.0, help="Fixed amount will count as a debit if it is negative, as a credit if it is positive.")
    second_tax_id = fields.Many2one('account.tax', string='Second Tax', ondelete='restrict', domain=[('type_tax_use', '=', 'purchase')])
    second_analytic_account_id = fields.Many2one('account.analytic.account', string='Second Analytic Account', ondelete='set null')
    second_analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Second Analytic Tags')

    @api.onchange('name')
    def onchange_name(self):
        self.label = self.name

    @api.onchange('tax_id')
    def _onchange_tax_id(self):
        if self.tax_id:
            self.force_tax_included = self.tax_id.price_include

    @api.onchange('second_tax_id')
    def _onchange_second_tax_id(self):
        if self.second_tax_id:
            self.force_second_tax_included = self.second_tax_id.price_include

    @api.onchange('match_total_amount_param')
    def _onchange_match_total_amount_param(self):
        if self.match_total_amount_param < 0 or self.match_total_amount_param > 100:
            self.match_total_amount_param = min(max(0, self.match_total_amount_param), 100)

    @api.multi
    def button_journal_items(self):
        move_lines = self.env['account.move.line'].search([('model_id', 'in', self.ids)])
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_lines.ids)],
        }


    ####################################################
    # RECONCILIATION PROCESS
    ####################################################

    @api.model
    def _get_taxes_move_lines_dict(self, tax, base_line_dict):
        ''' Get move.lines dict (to be passed to the create()) corresponding to a tax.
        :param tax:             An account.tax record.
        :param base_line_dict:  A dict representing the move.line containing the base amount.
        :return: A list of dict representing move.lines to be created corresponding to the tax.
        '''
        balance = base_line_dict['debit'] - base_line_dict['credit']
        currency = base_line_dict.get('currency_id') and self.env['res.currency'].browse(base_line_dict['currency_id'])
        res = tax.compute_all(balance, currency=currency)

        new_aml_dicts = []
        for tax_res in res['taxes']:
            tax = self.env['account.tax'].browse(tax_res['id'])

            new_aml_dicts.append({
                'account_id': tax.account_id and tax.account_id.id or base_line_dict['account_id'],
                'name': tax.name,
                'partner_id': base_line_dict.get('partner_id'),
                'debit': tax_res['amount'] > 0 and tax_res['amount'] or 0,
                'credit': tax_res['amount'] < 0 and -tax_res['amount'] or 0,
                'analytic_account_id': tax.analytic and base_line_dict['analytic_account_id'],
                'analytic_tag_ids': tax.analytic and base_line_dict['analytic_tag_ids'],
                'tax_exigible': tax.tax_exigibility == 'on_invoice',
            })
        return new_aml_dicts

    @api.multi
    def _get_write_off_move_lines_dict(self, st_line, move_lines):
        ''' Get move.lines dict (to be passed to the create()) corresponding to the reconciliation model's write-off lines.
        :param st_line:     An account.bank.statement.line record.
        :param move_lines:  An account.move.line recordset.
        :return: A list of dict representing move.lines to be created corresponding to the write-off lines.
        '''
        self.ensure_one()

        line_residual = st_line.currency_id and st_line.amount_currency or st_line.amount
        line_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.company_id.currency_id
        total_residual = sum(aml.currency_id and aml.amount_residual_currency or aml.amount_residual for aml in move_lines)
        balance = line_residual - total_residual

        if not self.account_id or float_is_zero(balance, precision_rounding=line_currency.rounding) or balance < 0:
            return []

        line_balance = self.amount_type == 'percent' and balance * (self.amount / 100.0) or self.amount

        new_aml_dicts = []

        # First write-off line.
        writeoff_line = {
            'name': self.label,
            'account_id': self.account_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'debit': line_balance < 0 and -line_balance or 0,
            'credit': line_balance > 0 and line_balance or 0,
        }
        new_aml_dicts.append(writeoff_line)

        if self.tax_id:
            writeoff_line['tax_ids'] = [(6, None, [self.tax_id.id])]
            self_ctx = self
            if self.force_tax_included:
                self_ctx = self_ctx.with_context(force_price_include=True)
            new_aml_dicts += self_ctx._get_taxes_move_lines_dict(self.tax_id, writeoff_line)

        # Second write-off line.
        if self.has_second_line and self.second_account_id:
            line_balance = balance - sum(aml['debit'] - aml['credit'] for aml in new_aml_dicts)
            second_writeoff_line = {
                'name': self.second_label,
                'account_id': self.second_account_id.id,
                'analytic_account_id': self.second_analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, self.second_analytic_tag_ids.ids)],
                'debit': line_balance < 0 and -line_balance or 0,
                'credit': line_balance > 0 and line_balance or 0,
            }
            new_aml_dicts.append(second_writeoff_line)

            if self.second_tax_id:
                second_writeoff_line['tax_ids'] = [(6, None, [self.second_tax_id.id])]
                self_ctx = self
                if self.force_second_tax_included:
                    self_ctx = self_ctx.with_context(force_price_include=True)
                new_aml_dicts += self_ctx._get_taxes_move_lines_dict(self.second_tax_id, second_writeoff_line)

        return new_aml_dicts

    @api.multi
    def _prepare_auto_reconciliation(self, st_line, move_lines, partner=None):
        ''' Reconcile the statement line with some move lines using this reconciliation model.
        :param st_line:     An account.bank.statement.line record.
        :param move_lines:  An account.move.line recordset.
        :param partner_id:  An optional res.partner record. If not set, st_line.partner_id will be used.
        :return:            Counterpart account.moves.
        '''
        self.ensure_one()

        # Create counterpart_aml_dicts + payment_aml_rec.
        counterpart_aml_dicts = []
        payment_aml_rec = self.env['account.move.line']
        for aml in move_lines:
            if aml.account_id.internal_type == 'liquidity':
                payment_aml_rec |= aml
            else:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
                counterpart_aml_dicts.append({
                    'name': aml.name if aml.name != '/' else aml.move_id.name,
                    'debit': amount < 0 and -amount or 0,
                    'credit': amount > 0 and amount or 0,
                    'move_line': aml,
                })

        # Create new_aml_dicts.
        new_aml_dicts = self._get_write_off_move_lines_dict(st_line, move_lines)

        line_residual = st_line.currency_id and st_line.amount_currency or st_line.amount
        line_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.company_id.currency_id
        total_residual = sum(aml.currency_id and aml.amount_residual_currency or aml.amount_residual for aml in move_lines)
        total_residual -= sum(aml['debit'] - aml['credit'] for aml in new_aml_dicts)

        # Create open_balance_dict
        open_balance_dict = None
        if float_compare(line_residual, total_residual, precision_rounding=line_currency.rounding) != 0:
            if not partner and not st_line.partner_id:
                open_balance_dict = False
            else:
                balance = total_residual - line_residual
                partner = partner or st_line.partner_id
                open_balance_dict = {
                    'name': '%s : %s' % (st_line.name, _('Open Balance')),
                    'account_id': balance < 0 and partner.property_account_payable_id.id or partner.property_account_receivable_id.id,
                    'debit': balance > 0 and balance or 0,
                    'credit': balance < 0 and -balance or 0,
                }
        return {
           'counterpart_aml_dicts': counterpart_aml_dicts,
           'payment_aml_rec': payment_aml_rec,
           'new_aml_dicts': new_aml_dicts,
           'open_balance_dict': open_balance_dict
        }

    ####################################################
    # RECONCILIATION CRITERIA
    ####################################################

    @api.model
    def _get_base_write_off_type_reconciliation_query(self, st_lines, partner_map=None):
        ''' Get base query for models having type == 'write_off'.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                (query, params)
        '''
        # Compute partners values table.
        partners_list = []
        for line in st_lines:
            partner_id = partner_map and partner_map.get(line.id) or line.partner_id.id or 0
            partners_list.append('(%d, %d)' % (line.id, partner_id))
        partners_table = '(VALUES %s) AS line_partner (line_id, partner_id)' % ','.join(partners_list)

        params = [tuple(st_lines.ids)]

        query = '''
            SELECT
                st_line.id                          AS id
            FROM account_bank_statement_line st_line
            LEFT JOIN account_journal journal       ON journal.id = st_line.journal_id
            LEFT JOIN res_company company           ON company.id = st_line.company_id
            LEFT JOIN ''' + partners_table + '''    ON line_partner.line_id = st_line.id
            WHERE st_line.id IN %s
        '''
        return query, params

    @api.model
    def _get_base_invoices_type_reconciliation_query(self, st_lines, excluded_ids=None, partner_map=None):
        ''' Get base query for models having type == 'invoices'.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                (query, params)
        '''
        query, params = self._get_base_write_off_type_reconciliation_query(st_lines, partner_map=partner_map)

        # Adapt the select.
        query = query.replace(
            'FROM',
            '''
            ,aml.id                              AS aml_id,
            aml.currency_id                     AS aml_currency_id,
            aml.amount_residual                 AS aml_amount_residual,
            aml.amount_residual_currency        AS aml_amount_residual_currency
            FROM
            '''
        )

        # Join the account_move_line table.
        query = query.replace(
            'WHERE',
            '''
            , account_move_line aml
            LEFT JOIN account_move move             ON move.id = aml.move_id
            LEFT JOIN res_company aml_company       ON aml_company.id = aml.company_id
            LEFT JOIN account_account aml_account   ON aml_account.id = aml.account_id
            WHERE
            '''
        )

        # Add where clauses on account.move.line.
        # N.B: The first part of the CASE is about 'blue lines' while the second part is about 'black lines'.
        query += '''
            AND aml.company_id = st_line.company_id
            AND aml.statement_id IS NULL
            AND move.state = 'posted'
            AND (
                line_partner.partner_id = 0
                OR
                aml.partner_id = line_partner.partner_id
            )

            AND (
                company.account_bank_reconciliation_start IS NULL
                OR
                aml.date > company.account_bank_reconciliation_start
            )

            AND CASE WHEN journal.default_credit_account_id IS NOT NULL
                AND journal.default_debit_account_id IS NOT NULL
                THEN
                    (
                        aml.account_id IN (journal.default_credit_account_id, journal.default_debit_account_id)
                        AND aml.payment_id IS NOT NULL
                    )
                    OR
                    (
                        aml_account.reconcile IS TRUE
                        AND aml.reconciled IS FALSE
                    )
                END
        '''
        if excluded_ids:
            query += 'AND aml.id NOT IN %s'
            params.append(tuple(excluded_ids))
        return query, params

    @api.multi
    def _apply_match_invoices_criterion(self, query, params):
        ''' Apply filter to match invoices.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        # Update select for communication.
        query = query.replace(
            'FROM',
            '''
                , CASE WHEN  
                    REGEXP_REPLACE(st_line.name, '[^0-9]', '', 'g') ~ REGEXP_REPLACE(invoice.number, '[^0-9]', '', 'g')
                    OR (
                        invoice.reference IS NOT NULL
                        AND
                        REGEXP_REPLACE(st_line.name, '[^0-9]', '', 'g') ~ REGEXP_REPLACE(invoice.reference, '[^0-9]', '', 'g')
                    )
                THEN TRUE ELSE FALSE END AS communication_flag                    
                FROM
            '''
        )

        # Join the account_invoice table.
        query = query.replace(
            'WHERE',
            '''
            LEFT JOIN account_invoice invoice ON invoice.move_name = move.name
            WHERE
            '''
        )

        # Add where clause.
        query += '''
            AND invoice.state = 'open'
            AND CASE WHEN st_line.amount >= 0.0 THEN
                    invoice.type IN ('out_invoice', 'in_refund')
                ELSE
                    invoice.type IN ('in_invoice', 'out_refund')
                END
            AND CASE WHEN line_partner.partner_id != 0 THEN
                    invoice.partner_id = line_partner.partner_id
                ELSE
                    (
                        REGEXP_REPLACE(st_line.name, '[^0-9]', '', 'g') ~ REGEXP_REPLACE(invoice.number, '[^0-9]', '', 'g')
                        OR (
                            invoice.reference IS NOT NULL
                            AND
                            REGEXP_REPLACE(st_line.name, '[^0-9]', '', 'g') ~ REGEXP_REPLACE(invoice.reference, '[^0-9]', '', 'g')
                        )
                    )
                END
        '''
        return query, params

    @api.multi
    def _apply_journal_ids_criterion(self, query, params):
        ''' Apply filter for the 'match_journal_ids' field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.match_journal_ids:
            return query, params

        return query + ' AND st_line.journal_id IN %s', params + [tuple(self.match_journal_ids.ids)]

    @api.multi
    def _apply_nature_criterion(self, query, params):
        ''' Apply filter for the 'nature' field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if self.nature == 'amount_received':
            return query + ' AND st_line.amount >= 0.0', params
        if self.nature == 'amount_paid':
            return query + ' AND st_line.amount <= 0.0', params
        return query, params

    @api.multi
    def _apply_line_amount_criterion(self, query, params):
        ''' Apply filter for the 'match_amount'/'match_amount_param'/'match_amount_second_param' fields.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.match_amount:
            return query, params

        # Join the res_currency table to get the decimal places.
        query = query.replace(
            'ON line_partner.line_id = st_line.id',
            '''
            ON line_partner.line_id = st_line.id
            LEFT JOIN res_currency currency             ON currency.id = st_line.currency_id
            LEFT JOIN res_currency jnl_currency         ON jnl_currency.id = journal.currency_id
            LEFT JOIN res_currency comp_currency        ON comp_currency.id = company.currency_id
            '''
        )

        common_clause = '''
            AND (
                (
                    st_line.currency_id IS NOT NULL
                    AND
                    (
                        (st_line.amount >= 0 AND ROUND(st_line.amount, currency.decimal_places) %s)
                        OR
                        (st_line.amount < 0 AND ROUND(-st_line.amount, currency.decimal_places) %s)
                    )
                )
                OR
                (
                    journal.currency_id IS NOT NULL
                    AND
                    (
                        (st_line.amount >= 0 AND ROUND(st_line.amount, jnl_currency.decimal_places) %s)
                        OR
                        (st_line.amount < 0 AND ROUND(-st_line.amount, jnl_currency.decimal_places) %s)
                    )
                )
                OR
                (st_line.amount >= 0 AND ROUND(st_line.amount, comp_currency.decimal_places) %s)
                OR
                (st_line.amount < 0 AND ROUND(-st_line.amount, comp_currency.decimal_places) %s)
            )
        '''

        if self.match_amount == 'lower':
            common_clause_operator = '<= %s'
            common_clause_operator_param = [self.match_amount_param]
        elif self.match_amount == 'greater':
            common_clause_operator = '>= %s'
            common_clause_operator_param = [self.match_amount_param]
        else:
            # if self.match_amount == 'between'
            common_clause_operator = 'IS BETWEEN %s AND %s'
            common_clause_operator_param = [self.match_amount_param, self.match_amount_second_param]

        common_clause %= tuple([common_clause_operator] * 6)
        return query + common_clause, params + (common_clause_operator_param * 6)

    @api.multi
    def _apply_line_label_criterion(self, query, params):
        ''' Apply filter for the 'match_label'/'match_label_param' fields.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if self.match_label == 'contains':
            return query + ' AND st_line.name ILIKE %s', params + ['%%%s%%' % self.match_label_param]
        if self.match_label == 'not_contains':
            return query + ' AND st_line.name NOT ILIKE %s', params + ['%%%s%%' % self.match_label_param]
        if self.match_label == 'match_regex':
            return query + ' AND st_line.name ~ %s', params + [self.match_label_param]
        return query, params

    @api.multi
    def _apply_partner_is_set_criterion(self, query, params):
        ''' Apply filter for the 'partner_is_set' field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.partner_is_set:
            return query, params

        return query + ' AND line_partner.partner_id != 0', params

    @api.multi
    def _apply_partner_ids_criterion(self, query, params):
        ''' Apply filter for the match_partner_ids field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.partner_is_set or not self.match_partner_ids:
            return query, params

        return query + ' AND line_partner.partner_id IN %s', params + [tuple(self.match_partner_ids.ids)]

    @api.multi
    def _apply_partner_category_ids_criterion(self, query, params):
        ''' Apply filter for the 'match_partner_category_ids' field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.partner_is_set or not self.match_partner_category_ids:
            return query, params

        query += ''' 
            AND line_partner.partner_id IN (
                SELECT categ.partner_id FROM res_partner_res_partner_category_rel categ WHERE categ.category_id IN %s
            )
        '''
        return query, params + [tuple(self.match_partner_category_ids.ids)]

    @api.multi
    def _apply_same_currency_criterion(self, query, params):
        ''' Apply filter for the 'match_same_currency' field.
        :param query:   The current query to be applied on this model.
        :param params:  The query parameters.
        :return:        (query, params)
        '''
        self.ensure_one()

        if not self.match_same_currency:
            return query, params

        query += '''
            AND (
                CASE WHEN st_line.currency_id IS NOT NULL AND st_line.currency_id != aml_company.currency_id THEN
                    aml.currency_id = st_line.currency_id
                WHEN journal.currency_id IS NOT NULL AND journal.currency_id != aml_company.currency_id THEN
                    aml.currency_id = journal.currency_id
                ELSE
                    aml.currency_id IS NULL
                END
            )
        '''
        return query, params

    @api.multi
    def _check_invoices_type_propositions(self, statement_line, candidates):
        ''' Check restrictions that can't be handled for each move.line separately.
        /!\ Only used by models having a type equals to 'invoices'.
        :param statement_line:  An account.bank.statement.line record.
        :param candidates:      Fetched account.move.lines from query (dict).
        :return:                True if the reconciliation propositions are accepted. False otherwise.
        '''
        if not self.match_total_amount:
            return True

        # Match total residual amount.
        total_residual = sum(
            aml['aml_currency_id'] and aml['aml_amount_residual_currency'] or aml['aml_amount_residual'] for aml in
            candidates)
        line_residual = statement_line.currency_id and statement_line.amount_currency or statement_line.amount
        line_currency = statement_line.currency_id or statement_line.journal_id.currency_id or statement_line.company_id.currency_id

        # Statement line amount must not be lower than the total residual.
        if float_compare(line_residual, total_residual, precision_rounding=line_currency.rounding) < 0:
            return False

        # Statement line amount is equal to the total residual.
        if float_is_zero(total_residual - line_residual, precision_rounding=line_currency.rounding):
            return True

        amount_percentage = (total_residual / line_residual) * 100
        return amount_percentage >= self.match_total_amount_param

    @api.multi
    def _get_invoices_type_reconciliation_query(self, st_lines, excluded_ids=None, partner_map=None):
        '''
        /!\ Must be called only on reconciliation models having type == 'invoices'.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                (query, params)
        '''
        # Default query/params.
        base_query, base_params = self._get_base_invoices_type_reconciliation_query(st_lines, excluded_ids=excluded_ids, partner_map=partner_map)

        # Aggregated query/params.
        queries = []
        params = []

        for record in self:
            # Record query/params.
            record_query = base_query.replace('SELECT', 'SELECT %s AS sequence, %s AS model_id,')
            record_params = [record.sequence, record.id] + base_params

            record_query, record_params = record._apply_match_invoices_criterion(record_query, record_params)
            record_query, record_params = record._apply_journal_ids_criterion(record_query, record_params)
            record_query, record_params = record._apply_nature_criterion(record_query, record_params)
            record_query, record_params = record._apply_line_amount_criterion(record_query, record_params)
            record_query, record_params = record._apply_line_label_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_is_set_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_ids_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_category_ids_criterion(record_query, record_params)
            record_query, record_params = record._apply_same_currency_criterion(record_query, record_params)

            queries.append(record_query)
            params += record_params

        return ' UNION ALL '.join(queries), params

    @api.multi
    def _get_write_off_type_reconciliation_query(self, st_lines, excluded_ids=None, partner_map=None):
        '''
        /!\ Must be called only on reconciliation models having type == 'write_off'.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                (query, params)
        '''
        # Default query/params.
        base_query, base_params = self._get_base_write_off_type_reconciliation_query(st_lines, partner_map=partner_map)

        # Aggregated query/params.
        queries = []
        params = []

        for record in self:
            # Record query/params.
            record_query = base_query.replace('SELECT', 'SELECT %s AS sequence, %s AS model_id,')
            record_params = [record.sequence, record.id] + base_params

            record_query, record_params = record._apply_journal_ids_criterion(record_query, record_params)
            record_query, record_params = record._apply_nature_criterion(record_query, record_params)
            record_query, record_params = record._apply_line_amount_criterion(record_query, record_params)
            record_query, record_params = record._apply_line_label_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_is_set_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_ids_criterion(record_query, record_params)
            record_query, record_params = record._apply_partner_category_ids_criterion(record_query, record_params)

            queries.append(record_query)
            params += record_params

        return ' UNION ALL '.join(queries), params

    @api.multi
    def _apply_reconciliation_model_rules(self, st_lines, excluded_ids=None, partner_map=None):
        ''' Get the query to get candidates for all reconciliation models.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                A dict mapping each statement line id with:
            * aml_ids:      A list of account.move.line ids.
            * write_off:    A list of account.move.line dict corresponding to the write_off.
            * model:        An account.reconcile.model record (optional).
            * status:       'reconciled' if the lines has been already reconciled, 'write_off' if the write_off must be
                            applied on the statement line.
        '''
        available_models = self.filtered(lambda m: m.type != 'manual')

        results = dict((r.id, {'aml_ids': [], 'write_off': []}) for r in st_lines)

        if not available_models:
            return results

        ordered_models = available_models.sorted(key=lambda m: (m.sequence, m.id))

        grouped_candidates = {}

        # Type == 'invoices'.
        # Map each (st_line.id, model_id) with matching amls.
        invoices_models = ordered_models.filtered(lambda m: m.type == 'invoices')
        if invoices_models:
            query, params = invoices_models._get_invoices_type_reconciliation_query(st_lines, excluded_ids=excluded_ids, partner_map=partner_map)
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()

            for res in query_res:
                grouped_candidates.setdefault(res['id'], {})
                grouped_candidates[res['id']].setdefault(res['model_id'], [])
                grouped_candidates[res['id']][res['model_id']].append(res)

        # Type == 'write_off'.
        # Map each (st_line.id, model_id) with a flag indicating the st_line matches the criteria.
        write_off_models = ordered_models.filtered(lambda m: m.type == 'write_off')
        if write_off_models:
            query, params = write_off_models._get_write_off_type_reconciliation_query(st_lines, partner_map=partner_map)
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()

            for res in query_res:
                grouped_candidates.setdefault(res['id'], {})
                grouped_candidates[res['id']].setdefault(res['model_id'], True)

        # Keep track of already processed amls.
        amls_ids_to_exclude = set()

        # Keep track of already reconciled amls.
        reconciled_amls_ids = set()

        # Iterate all and create results.
        for line in st_lines:
            for model in ordered_models:
                # No result found.
                if not grouped_candidates.get(line.id) or not grouped_candidates[line.id].get(model.id):
                    continue

                process_auto_reconcile = model.auto_reconcile
                if model.type == 'invoices':
                    candidates = grouped_candidates[line.id][model.id]

                    # If some invoices match on the communication, suggest them.
                    # Otherwise, suggest all invoices having the same partner.
                    # N.B: The only way to match a line without a partner is through the communication.
                    available_candidates_with_com = []
                    available_candidates_wo_com = []
                    for c in candidates:
                        # Don't take into account already reconciled lines.
                        if c['aml_id'] in reconciled_amls_ids:
                            continue

                        # Dispatch candidates between lines matching invoices with the communication or only the partner.
                        if c['communication_flag']:
                            available_candidates_with_com.append(c)
                        elif not available_candidates_with_com:
                            available_candidates_wo_com.append(c)
                    available_candidates = available_candidates_with_com or available_candidates_wo_com

                    # Needed to handle check on total residual amounts.
                    if model._check_invoices_type_propositions(line, available_candidates):
                        results[line.id]['model'] = model

                        # Add candidates to the result.
                        for candidate in available_candidates:

                            # Special case: the propositions match the rule but some of them are already consumed by
                            # another one. Then, suggest the remaining propositions to the user but don't make any
                            # automatic reconciliation.
                            if candidate['aml_id'] in amls_ids_to_exclude:
                                process_auto_reconcile = False
                                continue

                            results[line.id]['aml_ids'].append(candidate['aml_id'])
                            amls_ids_to_exclude.add(candidate['aml_id'])
                elif model.type == 'write_off':
                    results[line.id]['model'] = model
                    results[line.id]['status'] = 'write_off'

                # Add write_off lines and process the reconciliation.
                if process_auto_reconcile:
                    move_lines = self.env['account.move.line'].browse(results[line.id]['aml_ids'])
                    partner = partner_map and partner_map.get(line.id) and self.env['res.partner'].browse(partner_map[line.id])
                    reconciliation_results = model._prepare_auto_reconciliation(line, move_lines, partner=partner)

                    if not move_lines and not reconciliation_results['new_aml_dicts']:
                        continue

                    reconciled_amls_ids.update(move_lines.ids)

                    # An open balance is needed but no partner has been found.
                    if reconciliation_results['open_balance_dict'] is False:
                        results[line.id]['write_off'] = reconciliation_results['new_aml_dicts']
                    else:
                        new_aml_dicts = reconciliation_results['new_aml_dicts']
                        if reconciliation_results['open_balance_dict']:
                            new_aml_dicts.append(reconciliation_results['open_balance_dict'])
                        counterpart_moves = line.process_reconciliation(
                            counterpart_aml_dicts=reconciliation_results['counterpart_aml_dicts'],
                            payment_aml_rec=reconciliation_results['payment_aml_rec'],
                            new_aml_dicts=new_aml_dicts,
                        )
                        reconciled_move_lines = counterpart_moves.mapped('line_ids')
                        reconciled_move_lines.write({'model_id': model.id})
                        results[line.id]['status'] = 'reconciled'
                        results[line.id]['reconciled_lines'] = reconciled_move_lines
        return results
