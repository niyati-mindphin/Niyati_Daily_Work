# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.http import request
import random


class Website(models.Model):
    _inherit = 'website'

    delivey_time = fields.Char(
        'Default Delivery Time', default=0.0,
        help="Delivery lead time, in days. It's the number of days, promised to the customer, between the confirmation of the sales order and the delivery.")
    is_top_header = fields.Boolean(string='Is Pre Header', help="Is Pre Header on Website")
    top_header_content = fields.Html(string='Pre Header Content', translate=True, help="Pre Header Content on Website")
    is_signup_view = fields.Boolean(string="Is Signup View", default=False,
        help="Website have extended signup view or not.")
    login_background_image = fields.Binary(string="Login Background Image")
    show_tag_filter = fields.Boolean(string="Show Tag Filter in Shop", default=False)
    webhook_url = fields.Char('Webhook URL')

    def get_product_avail_variants(self, product):
        product_avail_variants = self.env['product.template'].search([('categ_id', '=', product.categ_id.id), ('is_published', '=', True), ('type', '=', 'product')])
        return product_avail_variants

    def _take_three_numbers(self, numbers_list, num_to_take):
        if len(numbers_list) < num_to_take:
            raise ValueError("Number of elements to take exceeds the length of the list.")
        return random.sample(numbers_list, num_to_take)

    def get_rating_from_product(self, product):
        current_website_id = self.env.context.get('website_id')
        product_rating_ids = self.env['rating.rating'].sudo().search([('res_id', '=', product.id), ('is_internal', '=', False), ('rating', '=', 5)], limit=20)

        if len(product_rating_ids) != 20:
            cal = 20 - len(product_rating_ids)
            other_rating_ids = self.env['rating.rating'].sudo().search([('product_id.website_id', '=', current_website_id), ('is_internal', '=', False), ('res_id', '!=', product.id), ('res_model', '=', 'product.template'), ('rating', '=', 5)], limit=cal)
            product_rating_ids += other_rating_ids

        numbers_list = list(product_rating_ids)
        vals = self._take_three_numbers(numbers_list, 3)

        return vals

    def get_rating_from_all_products(self):
        current_website_id = self.env.context.get('website_id')
        all_products_rating_ids = self.env['rating.rating'].sudo().search([('product_id.website_id', '=', current_website_id), ('is_internal', '=', False), ('res_model', '=', 'product.template'), ('rating', '=', 5)], limit=30)
        numbers_list = list(all_products_rating_ids)
        vals = self._take_three_numbers(numbers_list, 6)

        return vals

    def get_product_stock_available(self, product):
        # geoip = {'city': 'Frankfurt am Main', 'country_code': 'DE', 'country_name': 'Germany', 'region': 'HE', 'time_zone': 'Europe/Berlin'}
        geoip = request.session.get('geoip')
        geo_country_code = geoip.get('country_code')
        warehouse_id = False
        qty_available = 0
        geo_country_code = geoip.get('country_code')
        if self.env.user and not self.env.user._is_public():
            partner_id = self.env.user.partner_id
            country_id = partner_id.country_id
            if country_id:
                warehouse_id = self.env['stock.warehouse'].sudo().search([('country_ids', 'in', [country_id.id])], limit=1)
        else:
            country_id = self.env['res.country'].sudo().search([('code', '=', geo_country_code)], limit=1)
            if country_id:
                warehouse_id = self.env['stock.warehouse'].sudo().search([('country_ids', 'in', [country_id.id])], limit=1)
        if warehouse_id:
            qty_available = product.sudo().with_context(warehouse=warehouse_id.id).qty_available

        is_in_stock = False
        is_out_of_stock = False
        is_limited_stock = False
        # qty = product.sudo().with_context(warehouse=request.website._get_warehouse_available()).qty_available
        limited_stock = 10
        if qty_available > limited_stock:
            is_in_stock = True
        elif qty_available > 0 and qty_available <= limited_stock:
            is_limited_stock = True
        else:
            is_out_of_stock = True
        values = {
            'is_in_stock': is_in_stock,
            'is_out_of_stock': is_out_of_stock,
            'is_limited_stock': is_limited_stock,
        }
        return values


class website_menu(models.Model):
    _inherit = "website.menu"

    menu_icon = fields.Char("Menu icon", help="add class for icon (for ex.ci ci-themenwelt)")
