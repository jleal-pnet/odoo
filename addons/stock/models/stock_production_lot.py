# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    _name = 'stock.production.lot'
    _inherit = ['mail.thread']
    _description = 'Lot/Serial'

    name = fields.Char(
        'Lot/Serial Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Lot/Serial Number")
    ref = fields.Char('Internal Reference', help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], required=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        related='product_id.uom_id', store=True)
    quant_ids = fields.One2many('stock.quant', 'lot_id', 'Quants', readonly=True)
    create_date = fields.Datetime('Creation Date')
    product_qty = fields.Float('Quantity', compute='_product_qty')
    purchase_order_ids = fields.Many2many('purchase.order', string="Purchase Orders", compute='_purchase_orders', readonly=True, store=False)
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders", compute='_sale_orders', readonly=True, store=False)

    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, product_id)', 'The combination of serial number and product must be unique !'),
    ]

    @api.model
    def create(self, vals):
        active_picking_id = self.env.context.get('active_picking_id', False)
        if active_picking_id:
            picking_id = self.env['stock.picking'].browse(active_picking_id)
            if picking_id and not picking_id.picking_type_id.use_create_lots:
                raise UserError(_("You are not allowed to create a lot for this operation type."))
        return super(ProductionLot, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'product_id' in vals:
            move_lines = self.env['stock.move.line'].search([('lot_id', 'in', self.ids)])
            if move_lines:
                raise UserError(_(
                    'You are not allowed to change the product linked to a serial or lot number ' +
                    'if some stock moves have already been created with that number. ' +
                    'This would lead to inconsistencies in your stock.'
                ))
        return super(ProductionLot, self).write(vals)

    @api.one
    def _product_qty(self):
        # We only care for the quants in internal or transit locations.
        quants = self.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
        self.product_qty = sum(quants.mapped('quantity'))


    @api.depends('name')
    def _purchase_orders(self):
        for stock_move_line in self.env['stock.move.line'].search([('lot_id','=',self.id),('state','=','done')]):
            for stock_move in stock_move_line.move_id:
                if (stock_move_line.move_id.picking_id.location_id.usage == "supplier" and stock_move.state=="done" ):
                    self.purchase_order_ids = [ stock_move.purchase_line_id.order_id.id]

    @api.depends('name')
    def _sale_orders(self):
        for stock_move_line in self.env['stock.move.line'].search([('lot_id','=',self.id),('state','=','done')]):
            for stock_move in stock_move_line.move_id:
                if (stock_move_line.move_id.picking_id.location_dest_id.usage == "customer" and stock_move.state=="done" ):
                    self.sale_order_ids = [ stock_move.sale_line_id.order_id.id]
