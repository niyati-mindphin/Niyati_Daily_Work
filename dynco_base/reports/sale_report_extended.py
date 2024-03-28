# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).


import pytz
import babel.dates

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_brand_lead = fields.Many2one('dr.product.brand', string='Product Brand')
    invoice_date = fields.Date()


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_brand_lead'] = ", t.product_brand_lead as product_brand_lead"
        fields['invoice_date'] = ", s.invoice_date as invoice_date"
        groupby += ', t.product_brand_lead, s.invoice_date'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)