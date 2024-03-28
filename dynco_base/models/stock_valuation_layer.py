# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""

    _inherit = 'stock.valuation.layer'

    @api.model
    def _get_default_ch_currency(self):
        ch_currency_id = self.env['res.currency'].search([('name', '=', 'CHF')], limit=1)
        return ch_currency_id.id

    @api.model
    def _get_default_eu_currency(self):
        eu_currency_id = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
        return eu_currency_id.id

    @api.model
    def _get_default_usd_currency(self):
        usd_currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        return usd_currency_id.id

    ch_currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_ch_currency, readonly=True, required=True)
    ch_value = fields.Monetary('Total CH Value', readonly=True, currency_field="ch_currency_id")
    eur_currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_eu_currency, readonly=True, required=True)
    eur_value = fields.Monetary('Total EUR Value', readonly=True, currency_field="eur_currency_id")
    usd_currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_usd_currency, readonly=True, required=True)
    usd_value = fields.Monetary('Total USD Value', readonly=True, currency_field="usd_currency_id")
    vendor_id = fields.Many2one("res.partner", "Vendor")
    unit_price = fields.Float('Unit Price', group_operator="avg")

    def create(self, vals):
        res = super(StockValuationLayer, self).create(vals)
        for rec in res:
            if rec.product_id and rec.product_id.seller_ids:
                seller = res.product_id.seller_ids[0]
                rec.vendor_id = seller.name
                rec.unit_price = seller.price
                if rec.ch_currency_id and seller.currency_id == res.ch_currency_id:
                    rec.ch_value = seller.price * rec.quantity
                if rec.usd_currency_id and seller.currency_id == res.usd_currency_id:
                    rec.usd_value = seller.price * rec.quantity
                if rec.eur_currency_id and seller.currency_id == res.eur_currency_id:
                    rec.eur_value = seller.price * rec.quantity
        return res
