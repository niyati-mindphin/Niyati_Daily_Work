# -*- coding: utf-8 -*-

import logging
import requests
import base64
import urllib.request
import json
from datetime import timedelta, datetime
from werkzeug import urls
from odoo.http import request

from odoo import fields, models, api, _
from odoo.exceptions import AccessError
from odoo.tools.float_utils import float_round

from odoo.addons.b2b_portal.models.product import CommanProductTemplate
from odoo.addons.website.tools import get_video_embed_code

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _inherit = 'product.image'

    cproduct_tmpl_id = fields.Many2one('product.template', 'Related Product', copy=True)
    product_extra_img_url = fields.Char(compute='_compute_product_extra_img_url', string='Product Extra Image URL')

    def _compute_product_extra_img_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for img in self:
            img.product_extra_img_url = ''
            if img.product_tmpl_id:
                if img.product_tmpl_id.website_id and img.product_tmpl_id.website_id.domain:
                    base_url = img.product_tmpl_id.website_id.domain if img.product_tmpl_id.website_id else base_url
                product_name = img.product_tmpl_id.default_code or img.product_tmpl_id.name.replace("/", " ")
                endpoint = '/web/image/%s/%s/image_1920/%s.jpg' % (img._name, img.id, product_name)
                img.product_extra_img_url = urls.url_join(base_url, endpoint)

            elif img.cproduct_tmpl_id:
                if img.cproduct_tmpl_id.website_id and img.cproduct_tmpl_id.website_id.domain:
                    base_url = img.cproduct_tmpl_id.website_id.domain if img.product_tmpl_id.website_id else base_url
                product_name = img.cproduct_tmpl_id.default_code or img.cproduct_tmpl_id.name.replace("/", " ")
                endpoint = '/web/image/%s/%s/image_1920/%s.jpg' % (img._name, img.id, product_name)
                img.product_extra_img_url = urls.url_join(base_url, endpoint)


class WebsiteProductCategory(models.Model):
    _inherit = 'product.public.category'
    _order = 'sequence'

    categ_bottom_description = fields.Html('Category Bottom Description', translate=True)


class BaseProductTemplate(models.Model):
    _inherit = 'product.template'

    curr_location = fields.Html(string="Current Location with Qty", compute="_compute_curr_location", store=True)
    product_img_url = fields.Char(compute='_compute_product_img_url', string='Product Image URL')
    media_visibility = fields.Selection([
        ('without_copyright', 'Without Copyright'),
        ('with_copyright', 'With Copyright')], string='Website Media Visibility', default="without_copyright")

    def _get_images(self):
        # @overide
        """Return a list of records implementing `image.mixin` to
        display on the carousel on the website for this template.

        This returns a list and not a recordset because the records might be
        from different models (template and image).

        It contains in this order: the main image of the template and the
        Template Extra Images.
        """
        res = super(BaseProductTemplate, self)._get_images()
        if self.media_visibility:
            if self.media_visibility == 'without_copyright':
                return res
            elif self.media_visibility == 'with_copyright':
                self.ensure_one()
                return [self] + list(self.cproduct_image_ids)
            else:
                return res
        else:
            return res

    def _compute_product_img_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for p_image in self:
            if p_image.website_id and p_image.website_id.domain:
                base_url = p_image.website_id.domain
            if p_image.default_code:
                p_name = p_image.default_code
            elif p_image.name:
                p_name = p_image.name.replace("/", " ")
            else:
                p_name = ''
            p_image.product_img_url = '%s/web/image/%s/%s/image_1920/%s.jpg' % (base_url, p_image._name, p_image.id, p_name)

    @api.depends('default_code', 'product_variant_ids.stock_quant_ids', 'product_variant_ids.stock_move_ids', 'product_variant_ids.stock_move_ids.state', 'product_variant_ids.stock_quant_ids.location_id.name')
    def _compute_curr_location(self):
        cnt = 1
        for template in self:
            cnt += 1
            quants = template.product_variant_ids.mapped('stock_quant_ids')
            data = '<b><table cellspacing="5">'
            for quant in quants:
                if quant.location_id and quant.quantity and quant.location_id.usage == 'internal':
                    data += '<tr>'
                    data += '<td>' + quant.location_id.display_name + '&nbsp;&nbsp;&nbsp;&nbsp;</td>'
                    data += '<td>' + str(int(quant.quantity)) + '&nbsp;&nbsp;&nbsp;&nbsp;</td>'
                    data += '</tr>'
            template.curr_location = data + '</b></table>'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(BaseProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        if combination_info['product_id']:
            # ========== theme price =========
            website = self.env['website'].get_current_website()
            # [TO-DO] startswith('theme_prime') is not a good way must need to find another way in next version
            # Note: kig-odoo
            theme_id = website.sudo().theme_id
            product = self.env['product.product'].sudo().browse(combination_info['product_id'])
            if website and theme_id and theme_id.name.startswith('theme_prime'):
                IrUiView = self.env['ir.ui.view']
                combination_info['dr_extra_fields'] = IrUiView._render_template('theme_prime.product_extra_fields', values={'website': website, 'product_variant': product, 'product': product.product_tmpl_id})

            # ========== multi price =============
            # geoip = {'city': 'TEST', 'country_code': 'CH', 'country_name': 'Switzerland', 'region': 'HE', 'time_zone': 'Switzerland'}
            # geoip = {'city': 'Frankfurt am Main', 'country_code': 'DE', 'country_name': 'Germany', 'region': 'HE', 'time_zone': 'Europe/Berlin'}
            # geoip = {'city': 'Gandhinagar', 'country_code': 'IN', 'country_name': 'India', 'region': 'HE', 'time_zone': 'India'}
            geoip = request.session.get('geoip')
            partner_country_code = geoip.get('country_code')
            # User logined
            if self.env.user and not self.env.user._is_public():
                partner_id = self.env.user.partner_id
                if partner_id and partner_id.country_id:
                    partner_country_code = partner_id.country_id.code

            quantity = self.env.context.get('quantity', add_qty)
            context = dict(self.env.context, quantity=quantity, pricelist=pricelist.id if pricelist else False)
            product_template = self.with_context(context)
            combination = combination or product_template.env['product.template.attribute.value']
            if not product_id and not combination and not only_template:
                combination = product_template._get_first_possible_combination(parent_combination)

            product_template = product_template.with_context(current_attributes_price_extra=[v.price_extra or 0.0 for v in combination])
            # product = self.env['product.product'].sudo().browse(combination_info['product_id'])

            # multi_price = product.product_multiple_price_ids.filtered(lambda l: partner_country_code in l.country_ids.mapped('code'))

            # if multi_price and product and product.is_product_multi_price:
            #     # current_website = self.env['website'].get_current_website()
            #     if not pricelist:
            #         pricelist = website.get_current_pricelist()
            #     partner = self.env.user.partner_id
            #     company_id = website.company_id
            #     quantity_1 = 1
            #     tax_display = self.env.user.has_group('account.group_show_line_subtotals_tax_excluded') and 'total_excluded' or 'total_included'
            #     taxes = partner.property_account_position_id.map_tax(product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id))
            #     list_price = multi_price[0].price or 0.0
            #     list_price += product.price_extra
            #     if self._context.get('no_variant_attributes_price_extra'):
            #         list_price += sum(self._context.get('no_variant_attributes_price_extra'))
            #     list_price = taxes.compute_all(list_price, pricelist.currency_id, quantity_1, product, partner)[tax_display]
            #     combination_info.update({'list_price': list_price})
            #     if pricelist:
            #         final_price, rule_id = pricelist.get_product_price_rule(product, quantity or 1.0, partner)
            #         if rule_id:
            #             price = final_price
            #         else:
            #             price = multi_price[0].price
            #     else:
            #         price = multi_price[0].price if pricelist else list_price
            #     price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
            #     has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount, price) == 1
            #     combination_info.update({'has_discounted_price': has_discounted_price})
            #     if not has_discounted_price:
            #         combination_info.update({'price': price})
            #         price_without_discount = list_price if pricelist and pricelist.discount_policy == 'without_discount' else price
            #         has_discounted_price = (pricelist or product_template).currency_id.compare_amounts(price_without_discount, price) == 1
            #         combination_info.update({'has_discounted_price': has_discounted_price})
            #         if not has_discounted_price:
            #             combination_info.update({'price': price})

            # ============= product avail country and login user email_id pass for customer_stock_notification_knk module===============
            # product = self.env['product.product'].sudo().browse(combination_info['product_id'])
            warehouse_id = False
            free_qty = 0
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
                free_qty = product.with_context(warehouse=warehouse_id.id).free_qty
            combination_info.update({
                'free_qty': free_qty,
                'email': self.env.user.email if self.env.user else None,
            })
        return combination_info


class product_video(models.Model):
    _name = 'product.video'
    _description = 'Product Video'
    _order = "sequence"

    name = fields.Char(string="Title")
    video_url = fields.Char(string="Video url", required="True")
    image = fields.Binary(string="Thumbnail")
    product_tmpl_id = fields.Many2one('product.template', 'Related Product', copy=True)
    sequence = fields.Integer(string='Sequence', help="Gives the sequence order when displaying a list of product video")
    embed_code = fields.Html(compute="_compute_embed_code", sanitize=False)

    @api.depends('video_url')
    def _compute_embed_code(self):
        for image in self:
            image.embed_code = get_video_embed_code(image.video_url)

    @api.onchange('video_url')
    def set_video_image(self):
        if self.video_url:
            try:
                if len(self.video_url.split('/')) >= 2:
                    domain = self.video_url.split('/')[2]
                    if domain == 'player.vimeo.com':
                        vimeo_url = 'http://vimeo.com/api/v2/video/' + self.video_url.split('/')[-1] + '.json'
                        vimeo_response = urllib.request.urlopen(vimeo_url)
                        vimeo_content = vimeo_response.read()
                        vimeo_data = json.loads(vimeo_content.decode('utf8'))
                        vimeo_thumbnail_large_img = requests.get(vimeo_data[0]['thumbnail_large'].replace("'", '')).content
                        self.image = base64.b64encode(vimeo_thumbnail_large_img)
                    if domain == 'www.youtube.com':
                        # youtube_embed_url = self.video_url.replace('watch?v=', 'embed/')
                        youtube_url = 'http://img.youtube.com/vi/' + self.video_url.split('?v=')[-1] + '/0.jpg'
                        youtube_response = urllib.request.urlopen(youtube_url)
                        youtube_content = youtube_response.read()
                        self.image = base64.b64encode(youtube_content)
                else:
                    _logger.exception('Wrong Video URL')
                    raise AccessError(_("Wrong Video URL"))
            except urllib.error.URLError as e:
                _logger.exception('Video URL Not Found: %s' % e.reason)
                raise AccessError(_("Video URL Not Found: %s") % e)


class ProductCustomerCode(models.Model):
    _name = "product.customer.code"
    _description = 'Product Customer Code'
    _order = 'sequence, id'

    name = fields.Char(
        'Name',
        default='Customer Product Codes',
        readonly=True)
    sequence = fields.Integer(
        'Sequence',
        default=10,
        help="Assigns the priority to the list of product customers.")
    product_code = fields.Char(
        'Customer Product Code',
        size=64,
        required=True,
        help="""This customer's product code
                will be used when searching into
                a request for quotation.""")
    product_name = fields.Char(
        'Customer Product Name',
        size=128,
        help="""This customer's product name will
                be used when searching into a
                request for quotation.""")
    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product Template',
        index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        'Product Variant',
        help="When this field is filled in, the vendor data will only apply "
             "to the variant.")
    partner_id = fields.Many2one(
        'res.partner',
        'Customer',
        required=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=False,
        default=lambda self: self.env.user.company_id)


class ProductProductTemplate(models.Model):
    _inherit = "product.template"

    product_customer_code_ids = fields.One2many(
        'product.customer.code',
        'product_tmpl_id',
        'Customer Codes')
    sale_delay = fields.Float(
        'Customer Lead Time (B2C)', default=0,
        help="Delivery lead time for B2C Customer, in days. It's the number of days, promised to the customer, between the confirmation of the sales order and the delivery.")
    sale_delay_b2b = fields.Float(
        'Customer Lead Time (B2B)', default=0, help="Delivery lead time for B2B customer, in days. It's the number of days, promised to the customer, between the confirmation of the sales order and the delivery.")
    sale_delay_b2c = fields.Float(
        'Customer Lead Time (B2C)', default=0)
    webshop_product_name = fields.Char(string="Webshop Product Name", translate=True)
    product_icon_ids = fields.One2many('product.icon', 'product_tmpl_id', string='Icons')
    additional_info = fields.Html(string="Additional Product Information", translate=True, sanitize_attributes=False)
    webshop_marketing_text = fields.Html(string="Webshop Marketing Text", translate=True, sanitize_attributes=False)
    product_video_ids = fields.One2many('product.video', 'product_tmpl_id', string='Product Video')
    sales_count_cnt = fields.Float(compute='_compute_sales_count_cnt', string='Sold')
    product_brand_lead = fields.Many2one('dr.product.brand', string='Product Brand')
    cproduct_image_ids = fields.One2many('product.image', 'cproduct_tmpl_id', string='Images With Copyright')
    masse_info = fields.Html(string="Dimensions & filling quantities",translate=True, sanitize_attributes=False)
    item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', 'Pricelist Items')
    is_my_dynco = fields.Boolean(string="MY.DYNCO", default=True)

    @api.depends('product_variant_ids.sales_count_cnt')
    def _compute_sales_count_cnt(self):
        for product in self:
            product.sales_count_cnt = float_round(sum([p.sales_count_cnt for p in product.with_context(active_test=False).product_variant_ids]), precision_rounding=product.uom_id.rounding)

    def action_assemble_product_price(self):
        if self.bom_ids:
            assemble_price = 0
            suppliers = []
            for bom in self.bom_ids:
                component_ids = bom.bom_line_ids.mapped('product_id')
                for component in component_ids:
                    vendors_ids = component._select_date_seller()
                    if vendors_ids.ids:
                        suppliers.append(vendors_ids)
                    assemble_price += sum(vendors_ids.mapped('price'))
            for sup in suppliers:
                currency = False
                if sup.currency_id:
                    currency = sup.currency_id.id
                uom = False
                if sup.product_uom:
                    uom = sup.product_uom.id
                dlay = 1
                if sup.delay and dlay > sup.delay:
                    dlay = sup.delay
            if suppliers:
                vendor = self.env['res.partner'].search([('is_assemble_partner', '=', True)])
                self.seller_ids = [(0, 0, {'name':vendor.id,
                                           'currency_id': currency or vendor.currency_id.id,
                                           'date_start': datetime.today(),
                                           'min_qty': 1,
                                           'product_uom': uom or '',
                                           'price': assemble_price,
                                           'cost_price': 0,
                                           'delay': dlay,

                    })]

    def action_view_sales(self):
        return{
            'name': 'Sale Order Line',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order.line',
            'domain': [('product_id', 'in', self.mapped('product_variant_ids').ids)],
        }

    def _get_lechuza_images(self):
        """Return a list of records implementing `image.mixin` to
        display on the carousel on the website for this template.

        This returns a list and not a recordset because the records might be
        from different models (template and image).

        It contains in this order: the main image of the template and the
        Template Extra Images.
        """
        if self.media_visibility and self.media_visibility == 'without_copyright':
            self.ensure_one()
            return self._get_images()
        self.ensure_one()
        return [self] + list(self.cproduct_image_ids)


class ProductProduct(models.Model):
    _inherit = "product.product"

    sales_count_cnt = fields.Float(compute='_compute_sales_count_cnt', string='Sold')

    def _compute_sales_count_cnt(self):
        for product in self:
            date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
            product.sales_count_cnt = sum(self.env['sale.order.line'].search([('confirmation_date', '>', date_from), ('product_id', 'in', product.ids), ('state', 'not in', ('draft', 'cancel', 'sent'))]).mapped('qty_delivered'))

    def action_view_sales(self):
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        return{
            'name': 'Sale Order Line',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order.line',
            'domain': [('confirmation_date', '>', date_from), ('product_id', 'in', self.ids), ('state', 'not in', ('draft', 'cancel', 'sent'))],
        }

    def action_assemble_product_price(self):
        pass         

    def _get_lechuza_images(self):
        self.ensure_one()
        variant_images = list(self.product_variant_image_ids)
        if self.image_variant_1920:
            # if the main variant image is set, display it first
            variant_images = [self] + variant_images
        else:
            # If the main variant image is empty, it will fallback to template
            # image, in this case insert it after the other variant images, so
            # that all variant images are first and all template images last.
            variant_images = variant_images + [self]
        # [1:] to remove the main image from the template, we only display
        # the template extra images here
        return variant_images + self.product_tmpl_id._get_lechuza_images()[1:]

    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        suppliers = super(ProductProduct, self)._select_seller(partner_id=partner_id, quantity=quantity, date=date, uom_id=uom_id, params=params)
        partner = self.env['res.partner'].browse(self.env.context.get('customer_id'))
        if partner and partner.business_type:
            suppliers = self.seller_ids
            if partner.business_type == 'b2c' and 29642 in suppliers.mapped('name').ids:
                return suppliers.filtered(lambda x: x.name.id == 29642).sorted('sequence', reverse=True)[:1]
            else:
                if 29960 in suppliers.mapped('name').ids:
                    return suppliers.filtered(lambda x: x.name.id == 29960).sorted('sequence', reverse=True)[:1]
                else:
                    suppliers.sorted('sequence', reverse=True)[:1]
        if suppliers:
            return suppliers.sorted('price')[:1]
        else:
            return self.env['product.supplierinfo']


class product_icon(models.Model):
    _name = "product.icon"
    _description = "Product Icons"

    name = fields.Char(string="Name")
    icon = fields.Binary(string="Icon", attachment=True)
    product_tmpl_id = fields.Many2one('product.template', string='Related Product')


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    price = fields.Float(
        'Purchase', default=0.0, digits='Product Price',
        required=True, help="The price to purchase a product")
    cost_price = fields.Float(
        string='Cost Price', default=0.0,
        digits='Product Price')
    cost_currency_id = fields.Many2one(
        'res.currency', 'Cost Currency', default=lambda self: self.env.user.company_id.currency_id.id)
    default_code = fields.Char(string="Art-Nr", store=True)

    @api.onchange('product_tmpl_id')
    def onchange_product_template(self):
        if self.product_tmpl_id:
            code = self.product_tmpl_id.default_code
            self.default_code = code if code else ''


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    dynamic_text_1 = fields.Html(
        'dynamic Text one', translate=True)

    dynamic_text_2 = fields.Html(
        'dynamic Text two', translate=True)
    ecommerce_category = fields.Many2one('product.public.category', string="Ecommerce Category")

    @api.model
    def default_get(self, fields_list):
        """Override default_get method to set company_id if present in field_vals."""
        res = super(ProductPricelist, self).default_get(fields_list)

        # Check if 'company_id' is in field_vals
        if 'company_id' in fields_list:
            res['company_id'] = self.env.company.id
        return res

    def remove_ecommerce_category(self):
        pricelists = self.env['product.pricelist'].search([('ecommerce_category', '!=', False)])
        for rec in pricelists:
            for product in rec.ecommerce_category.product_tmpl_ids:
                price_rule = self.env['product.pricelist.item'].search([('compute_price', '=', 'fixed'), ('applied_on', '=', '1_product'), ('cm_label_id', '!=', False), ('product_tmpl_id', '=', product.id), ('date_end', '>', datetime.today())])
                if not price_rule:
                    product.public_categ_ids = [(3, rec.ecommerce_category.id)]


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    cm_label_id = fields.Many2one('dr.product.label', string='Label')
    show_discount_on_label = fields.Boolean(string="Show Discount On Label")

    def discountPercentage(self):
        sales_price = disPercent = False
        if self.applied_on in ['1_product', '0_product_variant']:
            if self.applied_on == '1_product':
                product = self.product_tmpl_id
            if self.applied_on == '0_product_variant':
                product = self.product_id
            sales_price = product.list_price
            if self.md_fixed_price:
                sales_price = self.md_fixed_price
            if self.compute_price == 'fixed':
                price = self._compute_price(sales_price, product.uom_id, product.product_variant_ids[0]),
                disc_price = price[0]
            elif self.compute_price == 'percentage':
                disc_price = self.percent_price
            else:
                disc_price = self.price_discount
        if sales_price:
            discount = sales_price - disc_price
            disPercent = str(int((discount / sales_price) * 100)) + '%'
        return disPercent

    @api.model
    def create(self, vals):
        if 'compute_price' in vals.keys():
            if vals['compute_price'] == 'fixed' and vals['applied_on'] == '1_product' and vals['cm_label_id']:
                product = self.env['product.template'].browse(int(vals['product_tmpl_id']))
                pricelist = self.env['product.pricelist'].browse(int(vals['pricelist_id']))
                if pricelist.ecommerce_category:
                    product.public_categ_ids = [(4, pricelist.ecommerce_category.id)]
        return super(PricelistItem, self).create(vals)

    def write(self, vals):
        for rec in self:
            if rec.compute_price == 'fixed' and rec.applied_on == '1_product' and ('cm_label_id' in vals and vals['cm_label_id']):
                if 'product_tmpl_id' in vals:
                    product = self.env['product.template'].browse(vals['product_tmpl_id'])
                else:
                    product = rec.product_tmpl_id
                if 'pricelist_id' in vals:
                    pricelist = self.env['product.pricelist'].browse(vals['pricelist_id'])
                else:
                    pricelist = rec.pricelist_id
                if pricelist.ecommerce_category:
                    product.public_categ_ids = [(4, pricelist.ecommerce_category.id)]
        return super(PricelistItem, self).write(vals)

    def action_delete_price_rule(self):
        for rec in self:
            rec.unlink()
        return {
            'name': _('Add Discounts'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'add.discount',
            'res_id': self.env.context.get('active_id'),
            'target': 'new',
            'context': {'active_id': self.env.context.get('active_id')}
        }

    def unlink(self):
        for rec in self:
            if rec.product_tmpl_id and rec.pricelist_id.ecommerce_category:
                price_rule = self.env['product.pricelist.item'].search([('compute_price', '=', 'fixed'), ('applied_on', '=', '1_product'), ('cm_label_id', '!=', False), ('product_tmpl_id', '=', rec.product_tmpl_id.id), ('date_end', '>', datetime.today()), ('id', '!=', rec.id)])
                if not price_rule:
                    rec.product_tmpl_id.public_categ_ids = [(3, rec.pricelist_id.ecommerce_category.id)]
        return super(PricelistItem, self).unlink()


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    website_id = fields.Many2one('website')


CommanProductTemplate._get_combination_info = BaseProductTemplate._get_combination_info
