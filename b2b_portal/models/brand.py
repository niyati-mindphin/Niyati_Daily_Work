# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.http import request


class DrProductBrand(models.Model):
    _inherit = ['dr.product.brand', 'website.multi.mixin']
    _name = 'dr.product.brand'

    brand_tag_ids = fields.Many2many('res.partner.category', string='Tags')
    is_hide_in_stock_filter = fields.Boolean(string="Hide In Stock Filter")
    b2b_show_rrp_price = fields.Boolean(string="Show RRP Price")
    b2b_show_product_price = fields.Boolean(string="Show Product Price")
    b2b_show_novelty_only = fields.Boolean(string="Show Novelty Only")
    b2b_tag_ids = fields.Many2many('dr.product.tags', string='Product Tags')
    b2b_brand_catalog = fields.Html(string='Brand Catalog', translate=True)
    catalog_url_ids = fields.One2many('catalog.url', 'brand_id', string='Catalog Url', help="Add Multipule catalog url here")
    video_url = fields.Char(string="Video Url", help="Ex. https://www.youtube.com/embed/VIDEO_ID replace the VIDEO_ID with video id")

    def can_access_from_current_website(self, website_id=False):
        can_access = True
        for record in self:
            if (False, request.env['website'].get_current_website().is_b2b_website):
                  return can_access
            if (website_id or record.website_id.id) not in (False, request.env['website'].get_current_website().id):
                can_access = False
                continue
        return can_access


class CatalogUrl(models.Model):
    _name = 'catalog.url'

    brand_id = fields.Many2one('dr.product.brand', string="Brand")
    name = fields.Char(string="Name")
    catalog_url = fields.Char(string="Catalog Url")
