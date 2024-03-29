# -*- coding: utf-8 -*-
import base64
import logging
import werkzeug
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from odoo.addons.http_routing.models.ir_http import slug
from odoo import fields, http, SUPERUSER_ID, tools, _
from werkzeug.exceptions import Forbidden, NotFound
from odoo.exceptions import AccessError
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website.controllers.main import Website, QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk
from odoo.http import request, content_disposition
from odoo.tools import consteq, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import expression
from odoo.tools.json import scriptsafe as json_scriptsafe
_logger = logging.getLogger(__name__)
import json
from datetime import datetime


class WebsiteSaleB2B(WebsiteSale):
    def _get_b2b_orders(self):
        partner = request.env.user.partner_id
        SaleOrder = request.env["sale.order"].sudo()
        draft_domain = [
            ("website_id", "=", request.website.id),
            ('partner_id', '=', partner.id),
            ("state", "in", ["draft"])
        ]
        confirm_domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ('partner_id', '=', partner.id),
            ("state", "in", ["sale"])
        ]
        done_domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ('partner_id', '=', partner.id),
            ("state", "in", ["done"])
        ]
        b2bquotations = SaleOrder.search(draft_domain)
        b2bOrders = SaleOrder.search(confirm_domain)
        b2bdoneOrders = SaleOrder.search(done_domain)
        order = request.website.sale_get_order(force_create=True)
        return {"b2bquotations": b2bquotations,
                "website_sale_order": order,
                "b2bOrders": b2bOrders,
                "b2bshippedOrder": b2bdoneOrders}

    def get_b2b_draft_orders(self):
        partner = request.env.user.partner_id
        SaleOrder = request.env["sale.order"].sudo()
        draft_domain = [
            ("website_id", "=", request.website.id),
            ('partner_id', '=', partner.id),
            ("state", "in", ["draft"])
        ]
        b2bquotations = SaleOrder.search(draft_domain)
        return b2bquotations

    def get_b2b_draft_brand_order(self, brand=None):
        b2bquotations = self.get_b2b_draft_orders()
        for quote in b2bquotations:
            if quote.brand_id and quote.brand_id.id == brand.id:
                request.session["sale_order_id"] = quote.id
                request.env.user.partner_id.last_website_so_id = quote.id
                order = request.website.sale_get_order()
                break;
        order = request.website.sale_get_order()
        if not order.brand_id:
            order.brand_id = brand.id
        elif order and order.brand_id and order.brand_id.id != brand.id:
            request.website.sale_reset()
            request.env.user.partner_id.last_website_so_id = False
            order = request.website.sale_get_order(force_create=1)
            request.session["sale_order_id"] = order.id
            request.env.user.partner_id.last_website_so_id = order.id
            order.brand_id = brand.id
        return request.website.sale_get_order()

    def _get_b2b_invoices(self):
        partner = request.env.user.partner_id
        Invoice = request.env["account.move"].sudo()
        unpaid_domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ('out_invoice', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
            ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))
        ]
        paid_domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ('out_invoice', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
            ('state', '=', 'posted'), ('payment_state', 'in', ('in_payment', 'paid'))
        ]
        b2bopeninvoices = Invoice.search(unpaid_domain)
        b2bpaidinvoces = Invoice.search(paid_domain)
        return {"b2bopeninvoices": b2bopeninvoices,
                "b2bpaidinvoces": b2bpaidinvoces
                }

    def _get_b2b_credit_notes(self):
        partner = request.env.user.partner_id
        Invoice = request.env["account.move"].sudo()
        domain = [
            # ("message_partner_ids", "child_of", [partner.commercial_partner_id.id]),
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_refund'),
            # ('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial'))
        ]
        b2bcredit_notes = Invoice.search(domain)
        return {"b2bcredit_notes": b2bcredit_notes
                }

    @http.route(['''/b2b/dashbord'''], type="http", auth="user", website=True)
    def B2bMainDashbord(self):
        # not request.env.user.partner_id.is_b2b_portal
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        values = self._get_b2b_orders()
        values.update(self._get_b2b_invoices())
        values.update(self._get_b2b_credit_notes())
        partner_id = request.env.user.partner_id
        all_brands = request.env['dr.product.brand'].search([('brand_tag_ids', 'in', partner_id.category_id.ids)])
        values.update({'all_brands': all_brands})
        return request.render('b2b_portal.b2bdashbord', values)

    def get_last_five_order_products_template_ids(self):
        partner = request.env.user.partner_id
        SaleOrder = request.env["sale.order"].sudo()
        confirm_domain = [
            ('partner_id', '=', partner.id),
            ("state", "in", ["sale", "done", "delivered", "complete"])
        ]
        orders = SaleOrder.search(confirm_domain, limit=5)
        return orders.mapped('order_line').mapped('product_id').ids

    def get_company_holiday_lives(self):
        pass
        # holidays = []
        # public_holiday = request.env['company.resource.calendar'].sudo().search([])
        # for global_leave in public_holiday.mapped('company_global_leave_ids'):
        #     holidays.append(datetime.strftime(global_leave.date_from, "%m-%d-%Y"))
        # return holidays

    @http.route('/b2b/set/planned/date', type="http", auth="user", website=True)
    def set_b2b_planned_date(self, **post):
        if post.get('planeddate'):
            planeddate = datetime.strptime(post.get('planeddate'), '%d.%m.%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if planeddate:
                request.session['b2b_select_planned_date'] = planeddate
        response = werkzeug.wrappers.Response()
        return response

    @http.route(['/b2b/product/fetch_barcode'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def b2b_product_fetch_barcode(self, barcode, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        product_id = request.env['product.product']
        if barcode:
            product_id = request.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        return product_id.id

    @http.route(['/b2b/brand/update_json'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def b2b_brand_update_product_json(self, brand=None, category=None, search='', **kwargs):
        """
        """
        value = {}
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kwargs.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}
        domain = [("sale_ok", "=", True)]
        domain = domain + [('is_published', '=', True)]
        if brand:
            brand_id = request.env['dr.product.brand'].browse(brand)
        if brand_id:
            domain = domain + [('product_brand_lead', '=', brand_id.id)]
        if kwargs.get('instock'):
            domain = domain + [('qty_available', '>', 0)]
        if category:
            domain = domain + [('public_categ_ids', 'child_of', int(category))]
        subdomains = []
        if search and len(search.split(' ')) > 1:
            for i, name in enumerate(search.split(' ')):
                subdomains.append([('name', 'ilike', name)])
        elif search:
            subdomains = [[('name', 'ilike', search)], [('product_variant_ids.default_code', 'ilike', search)]]
        if subdomains:
            # domain = domain + expression.OR(subdomains)
            domain = domain + expression.OR(subdomains)
        search_product = request.env['product.product'].sudo().search(domain)
        product_count = len(search_product)
        url = '/b2b/'
        if brand_id:
            url = "/b2b/%s" % (slug(brand_id))
        pager = request.website.pager(url=url, total=product_count, page=0, step=20, scope=7, url_args=kwargs)
        value['b2b_product_order_line'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_order_lines_tr", {
            'website_sale_order': order,
            'search': search,
            'products': search_product,
            'website': request.website,
            'brand': order.brand_id if order and order.brand_id else brand_id,
            'pager': pager,
            'pricelist': request.env.user.partner_id.property_product_pricelist
        })
        value['b2b_product_order_line_mobile_view'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_order_lines_tr_mobile_view", {
            'website_sale_order': order,
            'search': search,
            'products': search_product,
            'website': request.website,
            'brand': order.brand_id if order and order.brand_id else brand_id,
            'pager': pager,
            'pricelist': request.env.user.partner_id.property_product_pricelist
        })
        value['free_delivery_msg'] = order.free_delivery_message if order and order.free_delivery_message else ''
        return value

    @http.route([
        '''/b2b/<model("dr.product.brand"):brand>''',
        '''/b2b/<model("dr.product.brand"):brand>/page/<int:page>''',
        ], type="http", auth="user", website=True)
    def dashboard(self, page=0, brand=None, category=None, search='', ppg=False, min_price=0.0, max_price=0.0, **post):
        if not request.env.user._is_public() and not request.website.is_b2b_website or not brand:
            raise werkzeug.exceptions.NotFound()
        order = self.get_b2b_draft_brand_order(brand=brand);
        parner_id = request.env.user.partner_id
        if parner_id.property_account_position_id:
            if order.fiscal_position_id != parner_id.property_account_position_id:
                order.write({'fiscal_position_id': parner_id.property_account_position_id.id}) 
        if order and parner_id.property_product_pricelist:
            if parner_id.property_product_pricelist != order.pricelist_id:
                order.write({
                        'pricelist_id': parner_id.property_product_pricelist.id
                    })
                order.update_prices()
        request.session['b2b_brand_id'] = brand.id
        values = self._get_b2b_orders()
        values.update(self._get_b2b_invoices())
        values.update(self._get_b2b_credit_notes())
        add_qty = int(post.get('add_qty', 1))
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4
        url = "/b2b/%s" %(slug(brand))
        keep = QueryURL(url, search=search)
        website = request.env['website'].get_current_website()
        # website_domain = website.website_domain()
        now = datetime.timestamp(datetime.now())
        pricelist = website.pricelist_id

        if 'website_sale_pricelist_time' in request.session:
            # Check if we need to refresh the cached pricelist
            pricelist_save_time = request.session['website_sale_pricelist_time']
            if pricelist_save_time < now - 60*60:
                request.session.pop('website_sale_current_pl', None)
                website.invalidate_recordset(['pricelist_id'])
                pricelist = website.pricelist_id
                request.session['website_sale_pricelist_time'] = now
                request.session['website_sale_current_pl'] = pricelist.id
        else:
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id

        # pricelist_context, pricelist = self._get_pricelist_context()
        # request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        # request.update_context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)
        if search:
            post["search"] = search
        domain = [("sale_ok", "=", True)]
        # domain = [("is_my_dynco", "=", True)]
        domain = domain + [('is_published', '=', True)]
        domain = domain + [('product_brand_lead', '=', brand.id)]
        categories = request.env['product.product'].sudo().search(domain).mapped('public_categ_ids')
        # if post.get('instock'):
        #     domain = domain + [('qty_available', '>',  0)]
        if category:
            domain = domain + [('public_categ_ids', 'child_of', int(category))]
        subdomains = [[('name', 'ilike', search)], [('product_variant_ids.default_code', 'ilike', search)]]
        domain = domain + expression.OR(subdomains)
        if post.get('recent_order'):
            last_ordered_product_ids = self.get_last_five_order_products_template_ids()
            domain = domain + [('id', 'in', last_ordered_product_ids)]
        # domains.append(expression.OR(subdomains)
        if post.get('show_novelty_only'):
            domain = domain + [('product_variant_ids.dr_tag_ids', 'in',  brand.b2b_tag_ids.ids)]
        search_product = request.env['product.product'].sudo().search(domain)
        product_count = len(search_product)
        if search_product and post.get('instock'):
            search_product = search_product.with_context(warehouse=request.website._get_warehouse_available()).filtered(lambda x: x.qty_available > 0)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        values.update(self.checkout_values(order, **post))
        instockurl = "/b2b/%s" %(slug(brand))
        b2bbaseurl = "/b2b/%s" %(slug(brand))
        if order and brand:
            planneddate = order.get_planned_b2b_date(brand)
            if planneddate:
                request.session['b2b_select_planned_date'] = planneddate.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not post.get('instock'):
            instockurl = instockurl +'?instock=True'
        values.update({
            'search': search,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,
            'ppg': ppg,
            'ppr': ppr,
            'keep': keep,
            'only_services': False,
            'brand': brand,
            'recent_order': post.get('recent_order', False),
            'show_novelty_only': post.get('show_novelty_only', False),
            'instockurl': instockurl,
            'productinstock': post.get('instock', False),
            'categories':categories,
            'b2bbaseurl': b2bbaseurl,
            'category': category,
            'planneddate': order.get_planned_b2b_date(brand) if order and brand else False,
            'holidays': json.dumps(self.get_company_holiday_lives())
            })

        return request.render("b2b_portal.b2b_portal_shop", values)

    def b2b_checkout_check_address(self, order):
        billing_fields_required = self._get_mandatory_fields_billing(order.partner_id.country_id.id)
        if not all(order.partner_id.read(billing_fields_required)[0].values()):
            return request.redirect('/b2b/address?partner_id=%d' % order.partner_id.id)

        shipping_fields_required = self._get_mandatory_fields_shipping(order.partner_shipping_id.country_id.id)
        if not all(order.partner_shipping_id.read(shipping_fields_required)[0].values()):
            return request.redirect('/b2b/address?partner_id=%d' % order.partner_shipping_id.id)

    @http.route(['/b2b/address'], type='http', methods=['GET', 'POST'], auth="user", website=True, sitemap=False)
    def b2baddress(self, **kw):
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()
        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}
        redirect_uri_b2b = '/b2b'
        brand = None
        if request.session.get('b2b_brand_id'):
            brand = request.env['dr.product.brand'].browse(request.session.get('b2b_brand_id'))
            redirect_uri_b2b = redirect_uri_b2b +'/%s' %(slug(brand))
        partner_id = int(kw.get('partner_id', -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ('new', 'billing')
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                if partner_id == order.partner_id.id:
                    mode = ('edit', 'billing')
                    can_edit_vat = order.partner_id.can_edit_vat()
                else:
                    shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
                    if order.partner_id.commercial_partner_id.id == partner_id:
                        mode = ('new', 'shipping')
                        partner_id = -1
                    elif partner_id in shippings.mapped('id'):
                        mode = ('edit', 'shipping')
                    else:
                        return Forbidden()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)
            elif partner_id == -1:
                mode = ('new', 'shipping')
            else: # no mode - refresh without post?
                return request.redirect(redirect_uri_b2b)

        # IF POSTED
        if 'submitted' in kw and request.httprequest.method == "POST":
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors['error_message'] = error_msg
                values = kw
            else:
                partner_id = self._checkout_form_save(mode, post, kw)
                # We need to validate _checkout_form_save return, because when partner_id not in shippings
                # it returns Forbidden() instead the partner_id
                if isinstance(partner_id, Forbidden):
                    return partner_id
                if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.with_context(not_self_saleperson=True).onchange_partner_id()
                    # This is the *only* thing that the front end user will see/edit anyway when choosing billing address
                    order.partner_invoice_id = partner_id
                    if not kw.get('use_same'):
                        kw['callback'] = kw.get('callback') or \
                            (not order.only_services and (mode[0] == 'edit' and redirect_uri_b2b or '/b2b/address'))
                    # We need to update the pricelist(by the one selected by the customer), because onchange_partner reset it
                    # We only need to update the pricelist when it is not redirected to /confirm_order
                    if kw.get('callback', '') != redirect_uri_b2b:
                        request.website.sale_get_order(update_pricelist=True)
                elif mode[1] == 'shipping':
                    order.partner_shipping_id = partner_id

                # TDE FIXME: don't ever do this
                # -> TDE: you are the guy that did what we should never do in commit e6f038a
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(redirect_uri_b2b)
        is_bill_shipped = False
        if kw.get('callback') == '?use_billing':
            is_bill_shipped = True
        render_values = {
            'website_sale_order': order,
            'partner_id': partner_id if not is_bill_shipped else -1,
            'mode': mode if not is_bill_shipped else ('new', 'shipping'),
            'checkout': values,
            'can_edit_vat': can_edit_vat,
            'error': errors,
            'callback': kw.get('callback'),
            'brand':brand,
            'only_services': order and order.only_services,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        render_values.update(self._get_b2b_orders())
        render_values.update(self._get_b2b_invoices())
        return request.render("b2b_portal.b2baddress", render_values)

    @http.route(['/b2b/cart/update'], type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def b2b_cart_update(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}

        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        order._cart_update(
            product_id=int(product_id),
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
            no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
        )

        if not order.cart_quantity:
            request.website.sale_reset()

        order = request.website.sale_get_order()
        brand = order.partner_id.b2b_delivery_method_id.filtered(lambda x: x.brand_id == order.brand_id)
        if brand and brand.delivery_id:
            vals = brand.delivery_id.rate_shipment(order)
            if vals.get('success'):
                delivery_price = vals['price']
                order.set_delivery_line(brand.delivery_id, delivery_price)
        return request.redirect("/b2b/%s" % (slug(order.brand_id)))

    @http.route(['/b2b/cart/update_json'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def b2b_cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}

        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        value = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
            no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None
        )

        if not order.cart_quantity:
            request.website.sale_reset()

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity

        if not display:
            return value
        value['success'] = True
        value['sale_order'] = order.name
        value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': []
        })
        brand_id = False
        if request.session.get('b2b_brand_id', False):
            brand_id = request.env['dr.product.brand'].browse(request.session.get('b2b_brand_id', False))
        value['free_delivery_msg'] = order.free_delivery_message if order and order.free_delivery_message else '',
        value['b2b_product_order_line_product_id'] = product_id
        brand = order.partner_id.b2b_delivery_method_id.filtered(lambda x: x.brand_id == brand_id)
        if brand and brand.delivery_id:
            vals = brand.delivery_id.rate_shipment(order)
            if vals.get('success'):
                delivery_price = vals['price']
                order.set_delivery_line(brand.delivery_id, delivery_price)
        if request.env['sale.order.line'].browse(line_id) in order.order_line and set_qty > 0:
            if request.env['sale.order.line'].browse(line_id).product_id.product_tmpl_id:
                value['b2b_cart_line'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_cart_order_lines_tr", {
                    'website_sale_order': order,
                    'line': request.env['sale.order.line'].browse(line_id),
                    'website': request.website,
                    'date': fields.Date.today(),
                    'brand': order.brand_id if order and order.brand_id else brand_id,
                    'pricelist': request.env.user.partner_id.property_product_pricelist
                })

        value['b2b_cart_line_id'] = order.id
        value['b2b_portal.b2b_short_cart_summary'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_short_cart_summary", {
            'website_sale_order': order,
        })
        value['b2b_order_total'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_order_total", {
            'website_sale_order': order,
        })
        value['b2b_product_order_line'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_order_line_tr", {
            'website_sale_order': order,
            'product': request.env['product.product'].sudo().browse(product_id),
            'website': request.website,
            'brand': order.brand_id if order and order.brand_id else brand_id,
            'pricelist': request.env.user.partner_id.property_product_pricelist
        })
        value['b2b_product_order_line_mobile_view'] = request.env['ir.ui.view']._render_template("b2b_portal.b2b_order_line_tr_mobile_view", {
            'website_sale_order': order,
            'product': request.env['product.product'].sudo().browse(product_id),
            'website': request.website,
            'brand': order.brand_id if order and order.brand_id else brand_id,
            'pricelist': request.env.user.partner_id.property_product_pricelist
        })
        return value

    @http.route(['/b2b/cart'], type='http', auth="user", website=True, sitemap=False)
    def b2b_cart(self, access_token=None, revive='', **post):
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        """
        Main cart management + abandoned cart revival
        access_token: Abandoned cart SO access token
        revive: Revival method when abandoned cart. Can be 'merge' or 'squash'
        """
        redirect_uri_b2b = '/b2b'
        brand = None
        if request.session.get('b2b_brand_id'):
            brand = request.env['dr.product.brand'].browse(request.session.get('b2b_brand_id'))
            redirect_uri_b2b = redirect_uri_b2b +'/%s' %(slug(brand))
        order = request.website.sale_get_order()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/b2b/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'access_token': abandoned_order.access_token})

        if order and brand:
            planneddate = order.get_planned_b2b_date(brand)
            if planneddate:
                request.session['b2b_select_planned_date'] = planneddate.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        values.update(self.checkout_values(order, **post))
        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
            'planneddate': order.get_planned_b2b_date(brand) if order and brand else False,
            'redirect_uri_b2b': redirect_uri_b2b
        })
        values.update(self._get_b2b_orders())
        values.update(self._get_b2b_invoices())
        if order:
            order.order_line.filtered(lambda l: not l.product_id.active).unlink()
            order = order
        brand = order.partner_id.b2b_delivery_method_id.filtered(lambda x:x.brand_id == order.brand_id)
        if brand and brand.delivery_id:
            vals = brand.delivery_id.rate_shipment(order)
            if vals.get('success'):
                delivery_price = vals['price']
                order.set_delivery_line(brand.delivery_id, delivery_price)
                order.website_order_line = order.order_line
        return request.render("b2b_portal.b2bcart", values)

    @http.route(['/b2b/placeorder'], type='http', auth="user", website=True, sitemap=False)
    def b2bplaceorder(self, **post):
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        order = request.website.sale_get_order()
        if order and not len(order.order_line):
            return request.redirect('/b2b/cart')
        try:
            order._onchange_partner_shipping_id()
            order.order_line._compute_tax_id()
            order.with_context(send_email=True).action_confirm()
            request.session['sale_last_order_id'] = order.id
            request.website.sale_reset()
        except Exception as e:
            return request.redirect('/b2b/cart')
        return request.redirect('/b2b/placeorder/confirmation')

    @http.route(['/b2b/update_note'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def b2b_update_note(self, **kw):
        order = request.website.sale_get_order(force_create=1)
        value = order.update({
            'note': kw.get('note'),
        })
        return value

    @http.route(['/b2b/placeorder/confirmation'], type='http', auth="user", website=True, sitemap=False)
    def b2bplaceorderConfirm(self, **post):
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        values = {}
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            values['order'] = order
        else:
            values['order'] = None
        values.update(self._get_b2b_orders())
        values.update(self._get_b2b_invoices())
        return request.render('b2b_portal.b2bplaceorder', values)

    @http.route(
        ["/b2b/product/<model('product.product'):product>"],
        type="http",
        auth="user",
        website=True,
    )
    def b2b_product_detail(self, product, **post):
        values = {}
        values.update(self._get_b2b_orders())
        values.update(self._get_b2b_invoices())
        pricelist_context, pricelist = self._get_pricelist_context()
        product_context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)
        product = product.with_context(product_context)
        values.update({'product': product})
        return request.render("b2b_portal.b2b_product_details", values)


class Website(Website):
    @http.route("/", type="http", auth="public", website=True)
    def index(self, **kw):
        if request.env.user._is_public() and request.website.is_b2b_website:
            return request.redirect('/web/login')
        homepage = request.env['website.menu'].sudo().search([('website_id', '=', request.website.id), ('url', '=', '/')])
        print("\n\n\n\t--> homepage", homepage)
        # homepage = request.website.homepage_id

        if (homepage and (homepage.sudo().is_visible or request.env.user.has_group("base.group_user")) and homepage.url != "/"):
            if not request.env.user._is_public() and request.website.is_b2b_website:
                    return request.env["ir.http"].reroute("/b2b/dashbord")
            return request.env["ir.http"].reroute(homepage.url)
        website_page = request.env["ir.http"]._serve_page()
        print("\n\n\n\t------------> website_page", website_page)
        if website_page:
            if homepage.url == "/":
                print("\n\n\n\t---1............")
                if not request.env.user._is_public() and request.website.is_b2b_website:
                    print("\n\n\n\t---2............")
                    # return request.env["ir.http"].reroute("/b2b/dashbord")
                    return request.redirect('/b2b/dashbord')
            print("\n\n\n\t----> website_page", website_page)
            return website_page
        else:
            top_menu = request.website.menu_id
            first_menu = (
                top_menu
                and top_menu.child_id
                and top_menu.child_id.filtered(lambda menu: menu.is_visible)
            )
            if (
                first_menu
                and first_menu[0].url not in ("/", "")
                and (not (first_menu[0].url.startswith(("/?", "/#", " "))))
            ):
                return request.redirect(first_menu[0].url)
        raise request.not_found()

    # @http.route(['/download/datasheet'], type='http', auth="public", website=True)
    # def download_datasheet(self, **post):
    #     sale_order_id = request.env['sale.order'].search([('id', '=', post.get('sale_order'))])
    #     sale_order_id.order_line
    #     return True

    @http.route(['/download/images'], type='http', auth="public", website=True)
    def download_images(self, **post):
        sale_order_id = request.env['sale.order'].sudo().search([('id', '=', post.get('sale_order'))])
        images = []
        for order_line_id in sale_order_id.order_line:
            images += [order_line_id.product_id.image_1920]
            images += order_line_id.product_id.cproduct_image_ids.mapped('image_1920')
        attachments = request.env['ir.attachment']
        for index, image in enumerate(images, 1):
            attachments += request.env['ir.attachment'].sudo().create({
                'name': 'Image %s.jpg' % (index),
                'res_id': sale_order_id.id,
                'res_model': 'sale.order',
                'datas': image,
                'type': 'binary',
            })
        file_dict = {}
        for attachment_id in attachments:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = dict(path=file_path, name=file_name)
        zip_filename = datetime.now()
        zip_filename = "%s.zip" % zip_filename
        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()
        return request.make_response(bitIO.getvalue(),
                                     headers=[('Content-Type', 'application/x-zip-compressed'),
                                              ('Content-Disposition', content_disposition(zip_filename))])


class WebsiteHelpdesk(WebsiteHelpdesk):

    @http.route()
    def website_helpdesk_teams(self, team=None, **kwargs):
        res = super(WebsiteHelpdesk, self).website_helpdesk_teams(team, **kwargs)
        if res and request.website and request.website.is_b2b_website:
            team = res.qcontext['teams'].filtered(lambda x: x.name.lower() == 'b2b dynco')[:1]
            res.qcontext['team'] = team
            res.qcontext['teams'] = team
        return res
