# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    is_b2b_website = fields.Boolean(string='B2B Website')

    def check_qty_availablity(self, product, total_ordered_qty):
        if self.env.ref('stock_dropshipping.route_drop_shipping').sudo() not in product.sudo().route_ids:
            if total_ordered_qty >= product.sudo().qty_available:
                return True
            else:
                return False
        else:
            return False

    def group_by_brand_orders(self, orders):
        # data = self.env['sale.order'].read_group(domain=[('id', 'in', 'out_refund'), ('partner_id', '=', order.partner_id.id), ('state', '=', 'posted'), ('currency_id', '=', usd_currency.id)], fields=['amount_total'], groupby=['partner_id'])
        data = {}
        for brand in orders.mapped('brand_id'):
            data.update({brand: orders.filtered(lambda x: x.brand_id == brand)})
        return data

    def sale_product_domain(self):
        domain = super(Website, self).sale_product_domain()
        if request.website.is_b2b_website:
            domain = [("sale_ok", "=", True)]
        return domain

    def get_product_stock_avail(self, product):
        # qty = product.sudo().qty_available
        qty = product.with_context(warehouse=request.website._get_warehouse_available()).qty_available
        # limited_stock = product.company_id.limited_stock
        limited_stock = 10
        if qty > limited_stock:
            return 'In Stock'
        elif qty > 0 and qty <= limited_stock:
            return 'Limited Stock'
        else:
            return 'Out of Stock'

    def get_b2b_product_price_total(self, product, website_sale_order):
        if website_sale_order:
            print("\n\n\n\t----> website_sale_order.pricelist_id", website_sale_order.pricelist_id)
            line = website_sale_order.get_sale_order_line_on_product(product_id=product.id)
            if line:
                return line.price_subtotal
            else:
                return 0
        return 0

    def get_b2b_product_qty(self, product, website_sale_order):
        if website_sale_order:
            line = website_sale_order.get_sale_order_line_on_product(product_id=product.id)
            if line and line.product_packaging_qty:
                return str(int(line.product_packaging_qty))
            elif line:
                return str(int(line.product_uom_qty))
            else:
                return '0'
        return '0'

    def get_b2b_product_line_id(self, product, website_sale_order):
        if website_sale_order:
            line = website_sale_order.get_sale_order_line_on_product(product_id=product.id)
            if line:
                return line.id
            else:
                return None
        return None

    def get_is_b2b_website_or_not(self):
        # request.env.user.partner_id.is_b2b_portal
        if not request.env.user._is_public() and request.website.is_b2b_website:
            return True
        return False

    def _prepare_sale_order_values(self, partner):
        res = super()._prepare_sale_order_values(partner)
        partner_id = self.env['res.partner'].sudo().browse(res['partner_id'])
        team_id = self.env['crm.team'].sudo().browse(res['team_id'])
        if partner_id and partner_id.user_id:
            res['user_id'] = partner_id.user_id.id
        elif team_id and team_id.user_id:
            res['user_id'] = team_id.user_id.id
        return res
