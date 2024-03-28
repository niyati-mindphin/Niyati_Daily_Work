# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    delivery_detail = fields.Char(string="Delivery Order", compute='_po_delivery', store=True)
    days_of_develiry = fields.Integer(string="Days of Delivery", copy=False)

    @api.depends('picking_ids')
    def _po_delivery(self):
        for order in self:
            order.delivery_detail = ','.join([p.name for p in order.picking_ids])

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        for rec in self:
            if rec.partner_id:
                for line in rec.order_line:
                    pricelist = rec.env['product.supplierinfo'].search([('name', '=', rec.partner_id.id), ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)], limit=1)
                    if pricelist and pricelist.cost_price:
                        line.price_unit = pricelist.cost_price
        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        products = self.order_line.mapped('product_id')
        if products:
            non_pos_products = products.filtered(lambda x: not x.available_in_pos)
            if non_pos_products:
                non_pos_products.write({'available_in_pos': True})
        return res
