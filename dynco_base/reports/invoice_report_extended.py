# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    product_brand_lead = fields.Many2one('dr.product.brand', string='Product Brand', required=True)
    price_total = fields.Float('Total', readonly=True)
    del_price_subtotal = fields.Float('Del.Untaxed Total', readonly=True)
    credit_notes = fields.Float('Credit Notes', readonly=True)
    climaqua_target = fields.Float('Climaqua Target', readonly=True)
    lechuza_target = fields.Float('Lechuza Target', readonly=True)
    coop_target = fields.Float('Coop Target', readonly=True)
    total_turnover = fields.Float('Total Turnover', readonly=True)

    climaqua_percentage = fields.Float('Climaqua %', readonly=True)
    lechuza_percentage = fields.Float('Lechuza %', readonly=True)
    coop_percentage = fields.Float('Coop %', readonly=True)

    def _select(self):
        res = super(AccountInvoiceReport, self)._select()
        select_str = res + """, template.product_brand_lead AS product_brand_lead """
        select_str = res + """, template.product_brand_lead AS product_brand_lead, line.price_total AS price_total, CASE WHEN move.move_type = 'out_refund' THEN line.balance * currency_table.rate ELSE 0 END AS credit_notes, CASE WHEN move.move_type = 'out_invoice' THEN -line.balance * currency_table.rate ELSE 0 END as del_price_subtotal, line.climaqua_target AS climaqua_target,line.lechuza_target AS lechuza_target,line.coop_target AS coop_target, ((CASE WHEN move.move_type = 'out_invoice' THEN -line.balance * currency_table.rate ELSE 0 END)-(CASE WHEN move.move_type = 'out_refund' THEN line.balance * currency_table.rate ELSE 0 END)) AS total_turnover"""
        return select_str
