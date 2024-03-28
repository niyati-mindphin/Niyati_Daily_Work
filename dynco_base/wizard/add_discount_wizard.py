# -*- coding: utf-8 -*-

from odoo import models, fields, _
from collections import namedtuple


class AddDiscount(models.TransientModel):
    _name = 'add.discount'
    _description = 'Add Discount'

    discount_percentage = fields.Float("Discount Percentage", required=True)
    product_template_ids = fields.Many2many('product.template', string="Products", required=True)
    start_date = fields.Datetime("Start Date", required=True)
    end_date = fields.Datetime("End Date", required=True)
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist", required=True)
    price_rules_ids = fields.Many2many('product.pricelist.item', string="Price Rules")

    def create_dicounts(self):
        for product in self.product_template_ids:
            discount_price = product.list_price - (product.list_price * self.discount_percentage)
            new_fixed_price = 0.05 * round(discount_price / 0.05)
            self.env['product.pricelist.item'].create({
                'pricelist_id': self.pricelist_id.id,
                'compute_price': "fixed",
                'md_fixed_price': product.list_price,
                'fixed_price': new_fixed_price,
                'applied_on': '1_product',
                'product_tmpl_id': product.id,
                'date_start': self.start_date,
                'date_end': self.end_date,
                'min_quantity': 1,
                'cm_label_id': self.env['dr.product.label'].search([], limit=1).id,
                'show_discount_on_label': True,
            })

    def get_price_rules(self):
        product_prices = self.env['product.pricelist.item'].search([])
        for price_rule in product_prices:
            if price_rule.pricelist_id.id == self.pricelist_id.id and price_rule.compute_price == 'fixed' and price_rule.applied_on == '1_product' and (price_rule.product_tmpl_id.id in self.product_template_ids.ids) and price_rule.cm_label_id and price_rule.date_start and price_rule.date_end:
                Range = namedtuple('Range', ['start', 'end'])
                r1 = Range(start=self.start_date, end=self.end_date)
                r2 = Range(start=price_rule.date_start, end=price_rule.date_end)
                delta = (min(r1.end, r2.end) - max(r1.start, r2.start)).days + 1
                overlap = max(0, delta)
                if overlap > 0:
                    self.price_rules_ids = [(4, price_rule.id)]
        return {
            'name': _('Add Discounts'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'add.discount',
            'res_id': self.id,
            'target': 'new',
            'context': {'active_id': self.id}
        }
