# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleDeliveryLeadAdvance(models.TransientModel):
    _name = "sale.delivery.lead.advance"
    _description = "Sales Delivery Lead Advance"

    adv_actual_delivery_date = fields.Datetime(string='Actual Delivery Date', default=lambda self: fields.Datetime.now(), help="Date on which the order is shipped manage.", copy=False)
    is_delivered_wizard = fields.Boolean()
    transport_cost = fields.Float(string="Transport Cost")

    def advance_action_delivered(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        sale_orders.action_delivered(date=self.adv_actual_delivery_date, tc=self.transport_cost)
