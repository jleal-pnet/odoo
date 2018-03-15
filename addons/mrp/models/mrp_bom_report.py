# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.tools import config, float_round


class MrpBomReport(models.TransientModel):
    _name = 'mrp.bom.report'
    _description = "Mrp Bom Report"

    def _get_operation_line(self, routing, qty, level):
        operations = []
        total = 0.0
        for operation in routing.operation_ids:
            cycle_number = float_round(qty / operation.workcenter_id.capacity, precision_digits=1, rounding_method='UP')
            duration_expected = cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency
            duration_expected += operation.workcenter_id.time_stop + operation.workcenter_id.time_start
            total = ((duration_expected / 60.0) * operation.workcenter_id.costs_hour)
            operations.append({
                'level': level or 0,
                'operation': operation,
                'name': operation.name + ' - ' + operation.workcenter_id.name,
                'duration_expected': duration_expected,
                'total': float_round(total, precision_rounding=self.env.user.company_id.currency_id.rounding),
            })
        return operations

    def _get_price(self, bom, factor):
        price = 0
        if bom.routing_id:
            operations = self._get_operation_line(bom.routing_id, factor, 0)
            price += sum([op['total'] for op in operations])

        for line in bom.bom_line_ids:
            if line.child_bom_id:
                qty = line.product_uom_id._compute_quantity(line.product_qty * factor, line.child_bom_id.product_uom_id)
                sub_price = self._get_price(line.child_bom_id, qty)
                price += sub_price * qty
            else:
                prod_qty = line.product_qty * factor
                price += (line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * prod_qty)
        return price

    @api.model
    def _get_report_data(self, bom_id, searchQty=0, searchVariant=False):
        lines = {}
        bom = self.env['mrp.bom'].browse(bom_id)
        bom_quantity = float(searchQty) or bom.product_qty
        bom_product_variants = {}
        bom_uom_name = ''

        if bom:
            bom_uom_name = bom.product_uom_id.name

            # Get variants used for search
            if not bom.product_id:
                for variant in bom.product_tmpl_id.product_variant_ids:
                    bom_product_variants[variant.id] = variant.display_name

        lines = self._get_bom(bom_id, product_id=searchVariant, line_qty=bom_quantity, level=1)

        return {
            'lines': lines,
            'variants': bom_product_variants,
            'bom_uom_name': bom_uom_name,
            'bom_qty': bom_quantity,
            'is_variant_applied': self.env.user.user_has_groups('product.group_product_variant'),
            'is_uom_applied': self.env.user.user_has_groups('uom.group_uom')
        }

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        bom = self.env['mrp.bom'].browse(bom_id)
        current_line = self.env['mrp.bom.line'].browse(int(line_id))
        bom_quantity = current_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id)

        # Display bom components for current selected product variant
        if product_id:
            product = self.env['product.product'].browse(int(product_id))
        else:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id

        operations = self._get_operation_line(bom.routing_id, (bom_quantity / bom.product_qty), 0)
        lines = {
            'bom': bom,
            'bom_qty': bom_quantity,
            'bom_prod_name': product.display_name,
            'currency': self.env.user.company_id.currency_id,
            'product': product,
            'price': product.uom_id._compute_price(product.standard_price, bom.product_uom_id) * bom_quantity,
            'total': sum([op['total'] for op in operations]),
            'level': level or 0,
            'operations': operations,
            'operation_ids': [op['operation'].id for op in operations],
            'operations_cost': sum([op['total'] for op in operations]),
            'operations_time': sum([op['duration_expected'] for op in operations])
        }
        components, total = self._get_bom_lines(bom, bom_quantity, product, line_id)
        lines['components'] = components
        lines['total'] += total
        return lines

    def _get_bom_lines(self, bom, bom_quantity, product, line_id):
        components = []
        total = 0
        for line in bom.bom_line_ids:
            line_quantity = (bom_quantity) * line.product_qty
            if line._skip_bom_line(product):
                continue
            price = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line_quantity
            if line.child_bom_id:
                factor = line.product_uom_id._compute_quantity(line_quantity, line.child_bom_id.product_uom_id) * line.child_bom_id.product_qty
                total = self._get_price(line.child_bom_id, factor)
            else:
                total = price
            components.append({
                'prod_id': line.product_id.id,
                'prod_name': line.product_id.display_name,
                'prod_qty': line_quantity,
                'prod_uom': line.product_uom_id.name,
                'prod_cost': price,
                'parent_id': bom.id,
                'line_id': line.id,
                'total': total,
                'child_bom': line.child_bom_id.id,
                'phantom_bom': line.child_bom_id and line.child_bom_id.type == 'phantom' or False,
            })
            total += total
        return components, total

    @api.model
    def get_operations(self, bom_id=False, qty=0, level=0):
        bom = self.env['mrp.bom'].browse(bom_id)
        lines = self._get_operation_line(bom.routing_id, qty, level)
        values = {
            'bom_id': bom_id,
            'currency': self.env.user.company_id.currency_id,
            'operations': lines,
        }
        return self.env.ref('mrp.report_mrp_operation_line').render({'data': values})

    @api.model
    def get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        lines = self._get_bom(bom_id=bom_id, product_id=product_id, line_qty=line_qty, line_id=line_id, level=level)
        return self.env.ref('mrp.report_mrp_bom_line').render({'data': lines})

    @api.model
    def get_html(self, bom_id=False, searchQty=1, searchVariant=False):
        res = self._get_report_data(bom_id=bom_id, searchQty=searchQty, searchVariant=searchVariant)
        res['lines'] = self.env.ref('mrp.report_mrp_bom').render({'data': res['lines']})
        return res

    @api.model
    def get_pdf(self, bom_id, child_bom_ids=[], searchQty=0, searchVariant=False):
        bom_id = self.env.context.get('active_id')
        data = self.with_context(print_mode=True).get_report_data(bom_id, report_type='pdf')
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)
        report_values = {
            'mode': 'print',
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        }
        IrActionsReport = self.env['ir.actions.report']
        body = self.env['ir.ui.view'].render_template('mrp.report_mrp_bom_pdf', values=dict(report_values, data=data['lines'], report=self, context=self))
        header = IrActionsReport.render_template('web.internal_layout', values=report_values)
        header = IrActionsReport.render_template('web.minimal_layout', values=dict(report_values, subst=True, body=header))
        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body], header=header, landscape=True,
            specific_paperformat_args={'data-report-margin-top': 10, 'data-report-header-spacing': 10}
        )
