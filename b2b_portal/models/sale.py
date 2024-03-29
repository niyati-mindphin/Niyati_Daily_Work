# -*- coding: utf-8 -*-

import logging

from odoo import fields, models
from datetime import datetime
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    brand_id = fields.Many2one('dr.product.brand', string="Brand")
    show_description = fields.Boolean(string="Show Description", help="To Show Description in Report")

    def get_sale_order_line_on_product(self, product_id=None):
        self.ensure_one()
        product = self.env['product.product'].browse(product_id)
        domain = [('order_id', '=', self.id), ('product_id', '=', product_id)]
        return self.env['sale.order.line'].sudo().search(domain, limit=1)

    def get_planned_b2b_date(self, brand=None):
        product_brand = []
        lead_data = []
        holidays = []
        product_brand.append(brand)
        # If Customer have not set brand lead time than take from default company setting.
        if not self.partner_id.product_brand_lead_ids:
            product_brand_lead_data = self.company_id.comp_product_brand_lead_ids
        else:
            product_brand_lead_data = self.partner_id.product_brand_lead_ids
        for brand_lead in product_brand_lead_data:
            if brand_lead.product_brand_lead not in product_brand:
                continue
            lead_data.append(brand_lead.delivery_lead_time)
        # if lead_data:
        #     max_lead = max(lead_data)
        #     public_holiday = self.env['company.resource.calendar'].search([])
        #     for global_leave in public_holiday.mapped('company_global_leave_ids'):
        #         holidays.append(datetime.strftime(global_leave.date_from, "%Y-%m-%d"))
        #     dateorder = datetime.now().strptime(datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),DEFAULT_SERVER_DATETIME_FORMAT)
        #     return self.date_by_adding_business_days(dateorder, max_lead, holidays)
        return False

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if request and request.session.get('b2b_select_planned_date'):
            try:
                self.schedule_date = datetime.strptime(request.session.get('b2b_select_planned_date'), DEFAULT_SERVER_DATETIME_FORMAT)
                request.session['b2b_select_planned_date'] = None
            except Exception as e:
                pass
        return res

    def _website_product_id_change(self, order_id, product_id, qty=0, **kwargs):
        res = super(SaleOrder, self)._website_product_id_change(order_id, product_id, qty=qty, **kwargs)
        order = self.sudo().browse(order_id)
        if order and order.website_id.is_b2b_website:
            product_context = dict(self.env.context)
            product_context.setdefault('lang', order.partner_id.lang)
            product_context.update({
                'partner': order.partner_id,
                'quantity': qty,
                'date': order.date_order,
                'pricelist': order.pricelist_id.id,
            })
            product = self.env['product.product'].with_context(product_context).browse(product_id)
            if product and product.trade_unit_of_product:
                packaging_id = self.env['product.packaging'].sudo().search([('product_id', '=', product.id), ('qty', '=', product.trade_unit_of_product)], limit=1)
                if not packaging_id:
                    packaging_id = self.env['product.packaging'].sudo().create({
                        'name': '%s (Pack of %s)' % (product.name, product.trade_unit_of_product),
                        'company_id': self.company_id.id or self.env.company.id,
                        'product_id': product.id,
                        'sales': True,
                        'purchase': True,
                        'qty': product.trade_unit_of_product
                    })
                res['product_packaging_id'] = packaging_id.id
                res['product_uom_qty'] = qty * packaging_id.qty
                res['product_packaging_qty'] = qty
        return res

