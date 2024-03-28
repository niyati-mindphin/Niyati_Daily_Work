# -*- coding: utf-8 -*-

from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_at_date(self):
        res = super(StockQuantityHistory, self).open_at_date()
        active_model = self.env.context.get('active_model')
        if active_model == 'stock.valuation.layer':
            res['domain'] = [('create_date', '<=', self.inventory_datetime), ('product_id.type', '=', 'product'), ('product_id.route_ids', 'not in', self.env.ref('stock_dropshipping.route_drop_shipping').ids)]
        return res
