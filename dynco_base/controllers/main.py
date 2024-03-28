# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).
import hashlib
import re
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
import json

from odoo import http, _
from odoo.http import request, content_disposition
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.theme_prime.controllers.main import ThemePrimeMainClass, ThemeWebsite
from odoo.addons.survey.controllers.main import Survey
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home


class ClimaquaWebsiteReturnPolicy(http.Controller):

    @http.route(['/retouren-1'], type='http', auth='public', website=True)
    def clima_retouren(self, **kwargs):
        geoip = request.session.get('geoip')
        partner_country_code = geoip.get('country_code')
        # User logined
        if request.env.user and not request.env.user._is_public():
            partner_id = request.env.user.partner_id
            if partner_id and partner_id.country_id:
                partner_country_code = partner_id.country_id.code

        if partner_country_code in ['DE', 'AT']:
            return request.render('dynco_base.climaqua_eu_return_policy_view')
        return request.render('dynco_base.climaqua_swiss_return_policy_view')


class ThemePrimeMainClassCustom(ThemePrimeMainClass):

    @http.route('/theme_prime/get_products_data', type='json', auth='public', website=True)
    def get_products_data(self, domain=None, fields=[], options={}, limit=25, order=None, **kwargs):
        if len(fields):
            fields.append('webshop_product_name')

        return super(ThemePrimeMainClassCustom, self).get_products_data(domain=domain, fields=fields, options=options, limit=limit, order=order, **kwargs)

    def _prepare_product_data(self, products, fields, options=None):

        options = options or {}
        pricelist = request.website.get_current_pricelist()
        price_public_visibility = request.website._dr_has_b2b_access()
        visibility_label = False
        showStockLabel = False

        if not price_public_visibility:
            visibility_label = self._get_tp_view_template('theme_prime.tp_b2b_price_label')

        extra_data = {'rating', 'offer_data', 'dr_stock_label', 'colors'} & set(fields)
        fields = list(set(fields) - extra_data)

        if 'dr_stock_label' in extra_data:
            showStockLabel = request.website._get_dr_theme_config('json_grid_product')['show_stock_label']
        currency_id = pricelist.currency_id

        result = products.read(fields)

        for res_product, product in zip(result, products):
            combination_info = product._get_combination_info(only_template=True)
            res_product.update(combination_info)
            price_info = self._get_computed_product_price(product, res_product, price_public_visibility, visibility_label, currency_id)
            res_product.update(price_info)
            res_product['product_variant_id'] = product._get_first_possible_variant_id()

            sha = hashlib.sha1(str(getattr(product, '__last_update')).encode('utf-8')).hexdigest()[0:7]
            # Images
            res_product['img_small'] = '/web/image/product.template/' + str(product.id) + '/image_256?unique=' + sha
            res_product['img_medium'] = '/web/image/product.template/' + str(product.id) + '/image_512?unique=' + sha
            res_product['img_large'] = '/web/image/product.template/' + str(product.id) + '/image_1024?unique=' + sha

            # short Description
            if 'description_sale' in fields:
                description = res_product.get('description_sale')
                res_product['short_description'] = description[:125] + '...' if description and len(description) > 125 else description or False
            # label and color
            if 'colors' in extra_data:
                res_product['colors'] = self._get_tp_view_template('theme_prime.tp_product_color_pills', {'product': product, 'limit': 4, 'no_label': True, '_classes': 'tp_snippet_for_card'})
            # label and color
            price_rule = pricelist.get_product_price_rule(product, 1, request.env.user.partner_id)[1]
            if 'dr_label_id' in fields and price_rule:
                disc = 0
                label = None
                if price_rule:
                    price_rule = request.env['product.pricelist.item'].browse(price_rule)
                    if price_rule and price_rule.cm_label_id:
                        if price_rule.show_discount_on_label:
                            disc = price_rule.discountPercentage()
                            if disc:
                                if int(disc.replace('%', '')) > 0:
                                    label = price_rule.cm_label_id
                if label:
                    res_product['label'] = label
                    res_product['label'] = label
                    res_product['label_id'] = label.id
                    res_product['label_template'] = self._get_tp_view_template('theme_prime.product_label', {'label': label, 'disc': disc})
            if 'dr_stock_label' in extra_data and showStockLabel and product.dr_show_out_of_stock:
                res_product['dr_stock_label'] = self._get_tp_view_template('theme_prime.product_stock_label', {'product': product})
            # rating
            if 'offer_data' in extra_data:
                offer = product._get_product_pricelist_offer()
                if offer:
                    rule = offer.get('rule')
                    res_product['offer_data'] = {
                        'date_end': offer.get('date_end'),
                        'offer_msg': rule.dr_offer_msg,
                        'offer_finish_msg': rule.dr_offer_finish_msg
                    }

            if 'rating' in extra_data:
                res_product['rating'] = self._get_rating_template(product.rating_avg)
                res_product['rating_avg'] = product.rating_avg
            # images
            if 'product_variant_ids' in fields:
                res_product['images'] = product.product_variant_ids.ids
            # website_category
            if 'public_categ_ids' in fields and product.public_categ_ids:
                first_category = product.public_categ_ids[0]
                res_product['category_info'] = {
                    'name': first_category.name,
                    'id': first_category.id,
                    'website_url': '/shop/category/' + str(first_category.id),
                }
            # brand
            if 'dr_brand_value_id' in fields:
                res_product['brand_info'] = False
                if product.dr_brand_value_id:
                    res_product['brand_info'] = {
                        'name': product.dr_brand_value_id.name,
                        'id': product.dr_brand_value_id.id,
                    }

        return result

    def _get_computed_product_price(self, product, product_data, price_public_visibility, visibility_label, currency_id):
        res = super(ThemePrimeMainClassCustom, self)._get_computed_product_price(product=product, product_data=product_data, price_public_visibility=price_public_visibility, visibility_label=visibility_label, currency_id=currency_id)
        if product.is_product_multi_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {'display_currency': currency_id}
            price_rule = request.website.get_current_pricelist().get_product_price_rule(product, 1, request.env.user.partner_id)[1]
            if price_rule:
                price_rule_id = request.env['product.pricelist.item'].browse(price_rule)
                if price_rule_id and price_rule_id.md_fixed_price:
                    product_data['list_price'] = price_rule_id.md_fixed_price
                    has_discounted_price = request.website.get_current_pricelist().currency_id.compare_amounts(product_data['list_price'], product_data['price']) == 1
                    product_data['has_discounted_price'] = has_discounted_price
                    res['list_price'] = FieldMonetary.value_to_html(product_data['list_price'], monetary_options) if price_public_visibility else ' '
                    res['has_discounted_price'] = product_data['has_discounted_price']
        return res


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        if kw.get('name') and kw.get('last_name'):
            kw['name'] = kw.get('name') + ' ' + kw['last_name']
        if kw.get('partner_id'):
            Partner = request.env['res.partner'].sudo().browse(int(kw.get('partner_id')))
            if Partner and kw.get('company_type'):
                Partner.company_type = kw.get('company_type')
        res = super().address(**kw)
        return res

    @http.route(['/attachment/download/portal'], type='http', auth="public", website=True)
    def attachment_download_portal(self, **post):
        attachment_ids = request.env['ir.attachment'].sudo().search([('res_id', '=', post.get('invoice_id')),('res_model', '=', post.get('model'))])
        file_dict = {}
        for attachment_id in attachment_ids:
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

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        res = super(WebsiteSale, self).shop_payment_confirmation(**post)
        company = request.env.user.company_id
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.partner_id and order.partner_id.preferred_bank_id:
                order.partner_bank_id = order.partner_id.preferred_bank_id.id
            else:
                if order.currency_id:
                    bank = request.env['res.partner.bank'].sudo().search([('partner_id', '=', company.partner_id.id), ('currency_id', '=', order.currency_id.id)], limit=1)
                    order.partner_bank_id = bank.id
        return res

    @http.route(['/shop/sale_pricelist_category'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def SalePricelistCategory(self, **kw):
        pricelist = request.website.pricelist_id
        if pricelist.ecommerce_category and pricelist.ecommerce_category.category_seo_url:
            return request.redirect(pricelist.ecommerce_category.category_seo_url)
        else:
            pricelist = request.env['product.pricelist'].search([('name', '=', 'B2C Public Price Switzerland')])
            return request.redirect(pricelist.ecommerce_category.category_seo_url)

    @http.route('/home', type='http', auth="public", website=True)
    def redirect_homepage(self, **post):
        return request.redirect('/')

    @http.route('/webshop/cart/update_json', type="json", auth="public", website=True)
    def webshop_cart_update_json(self, **post):
        order = request.website.sale_get_order(force_create=1)
        product_id = int(post.get('product_id'))
        qty = 1

        if product_id in order.order_line.mapped('product_id').ids:
            line = order.order_line.search([('product_id', '=', product_id)], limit=1)
            old_qty = line.product_uom_qty
            line.product_uom_qty = old_qty + qty
        else:
            order._cart_update(
                product_id=product_id,
                add_qty=qty,
                set_qty=0,
            )
        return True


class Survey(Survey):

    @http.route('/survey/start/<string:survey_token>/<int:partner_id>', type='http', auth='public', website=True)
    def field_service_survey_start(self, survey_token, partner_id, answer_token=None, email=False, **post):
        """ Start a survey by providing
         * a token linked to a survey;
         * a token linked to an answer or generate a new token if access is allowed;
        """
        # Get the current answer token from cookie
        answer_from_cookie = False
        if not answer_token:
            answer_token = request.httprequest.cookies.get('survey_%s' % survey_token)
            answer_from_cookie = bool(answer_token)

        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)

        if answer_from_cookie and access_data['validity_code'] in ('answer_wrong_user', 'token_wrong'):
            # If the cookie had been generated for another user or does not correspond to any existing answer object
            # (probably because it has been deleted), ignore it and redo the check.
            # The cookie will be replaced by a legit value when resolving the URL, so we don't clean it further here.
            access_data = self._get_access_data(survey_token, None, ensure_token=False)

        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo._create_answer(user=request.env.user, email=email, partner_survey_id=partner_id)
            except UserError:
                answer_sudo = False

        if not answer_sudo:
            try:
                survey_sudo.with_user(request.env.user).check_access_rights('read')
                survey_sudo.with_user(request.env.user).check_access_rule('read')
            except:
                return request.redirect("/")
            else:
                return request.render("survey.survey_403_page", {'survey': survey_sudo})

        return request.redirect('/survey/%s/%s' % (survey_sudo.access_token, answer_sudo.access_token))

class AuthSignupHome(Home):

    def get_auth_signup_qcontext(self):
        """ Shared helper returning the rendering context for signup and reset password """
        qcontext = super(AuthSignupHome, self).get_auth_signup_qcontext()
        qcontext['countries'] = request.env['res.country'].sudo().search([('code', 'in', ['CH', 'DE', 'AT', 'LI', 'NL', 'BE', 'LU', 'FR', 'DK', 'PL', 'CZ', 'IT'])])
        return qcontext

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):

        response = super().web_auth_signup(*args, **kw)
        if not response.qcontext.get('error') and request.env.user:
            values = {}
            partner_id = request.env.user.partner_id
            if kw.get('last_name'):
                values['name'] = partner_id.name + ' ' + kw['last_name']
            if kw.get('street'):
                values['street'] = kw['street']
            if kw.get('country_id'):
                values['country_id'] = int(kw['country_id'])
            partner_id.write(values)
        return response


class ThemeWebsiteCustom(ThemeWebsite):

    @http.route('/website/dr_search', type='json', auth="public", website=True)
    def dr_search(self, term, max_nb_chars, options, **kw):

        fuzzy_term, global_match = False, False
        search_config = request.website._get_dr_theme_config('json_product_search')
        has_formulate = self._dr_has_formulate(search_config)
        fuzzy_enabled = search_config.get('search_fuzzy')
        limit = max(min(search_config.get('search_limit'), 100), 5)
        search_types = ['products', 'categories', 'autocomplete', 'suggestions']
        results = {search_type: {'results': [], 'results_count': 0, 'parts': {}} for search_type in search_types}
        product_limit = max(min(search_config.get('search_max_product'), 100), 0)
        options = {'allowFuzzy': fuzzy_enabled, 'displayDescription': False, 'displayDetail': True, 'displayExtraLink': True, 'displayImage': True}
        if product_limit:
            results['products'] = self.autocomplete(search_type='products_only', term=term, order='name asc', limit=product_limit, options=options)
        product_fuzzy_term = results['products'].get('fuzzy_search')

        if search_config.get('search_category') and not has_formulate:
            results['categories'] = self.autocomplete(search_type='product_categories_only', term=term, order='sequence, name, id', limit=5, options=options)
            category_fuzzy_term = results['categories'].get('fuzzy_search')
            if fuzzy_enabled:
                empty_search = {'results': [], 'results_count': 0, 'parts': {}}
                if category_fuzzy_term == product_fuzzy_term:
                    fuzzy_term = product_fuzzy_term
                elif not category_fuzzy_term and results['categories'].get('results_count'):
                    results['products'], fuzzy_term = empty_search, False
                elif not product_fuzzy_term and results['products'].get('results_count'):
                    results['categories'], fuzzy_term = empty_search, False
                elif product_fuzzy_term and not category_fuzzy_term:   # category will be always empty based on above conditions
                    fuzzy_term = product_fuzzy_term
                elif category_fuzzy_term and not product_fuzzy_term:   # products will be always empty based on above conditions
                    fuzzy_term = category_fuzzy_term
                else:  # super rare case
                    all_results = self.autocomplete(search_type='products', term=term, order='sequence, name, id', limit=limit, options=options)
                    products_result = [res for res in all_results['results'] if res.get('_fa') == 'fa-shopping-cart']
                    category_result = [res for res in all_results['results'] if res.get('_fa') == 'fa-folder-o']
                    fuzzy_term = all_results.get('fuzzy_search')
                    results = {'products': {'results': products_result, 'results_count': len(products_result), 'parts': {}}, 'categories': {'results': category_result, 'results_count': len(category_result), 'parts': {}}}

        # suggestion search
        if search_config.get('search_attribute') or search_config.get('search_suggestion'):
            remain_limit = limit - min(product_limit, results['products'].get('results_count', 0))       # Odoo results_count returns count for full result (without limit)
            words = [i for i in term.split(' ') if i]   # split and filter spaces
            matchs, matched_dicts = False, {}
            for word in words:
                if matchs:
                    for match in matchs:
                        match_dict = matched_dicts[match]
                        if match_dict['remaining_words']:
                            match_dict['remaining_words'].append(word)
                        else:
                            unmatched_record_name = match_dict['unmatched_record_name']
                            regex_match = re.search(re.escape(word), unmatched_record_name, re.IGNORECASE)
                            if regex_match:
                                match_dict['matched_words'].append(word)
                                match_dict['unmatched_record_name'] = re.sub(re.escape(word), ' ', unmatched_record_name, flags=re.I)
                            else:
                                match_dict['remaining_words'].append(word)
                else:
                    matchs = self._match_attr_or_category(word)
                    if matchs:
                        for match in matchs:
                            matched_dicts[match] = match_dict = {'match': match, 'matched_words': [word], 'remaining_words': []}
                            match_dict['unmatched_record_name'] = re.sub(re.escape(match_dict['matched_words'][0]), ' ', match.ds_name, flags=re.I)

            match_list = list(matched_dicts.values())
            match_list.sort(key=lambda m: len(m['matched_words']), reverse=True)
            autocomplete_result = []

            for match_dict in match_list:
                autocomplete_data = []
                if match_dict['remaining_words']:
                    autocomplete_data = self._get_autocomplete_data(match_dict, remain_limit, search_config)
                elif not search_config.get('search_category') and match_dict['match']._name == 'product.public.category':
                    autocomplete_data = [self.generate_result_dict(match_dict['match'], False, match_dict['matched_words'], '')]
                if not match_dict['remaining_words']:
                    # if no remaining_words that means full data matched with record so suggestions become autocomplete
                    autocomplete_data += self._get_suggestions_data(match_dict, autocomplete_result, remain_limit, search_config, ignore_config=True)
                remain_limit -= len(autocomplete_data)
                autocomplete_result.extend(autocomplete_data)
                if not remain_limit:
                    break

            suggestions_result = []
            for match_dict in match_list:
                suggestions_data = self._get_suggestions_data(match_dict, autocomplete_result, min(remain_limit, 5), search_config)
                remain_limit -= len(suggestions_data)
                suggestions_result.extend(suggestions_data)
                if not remain_limit:
                    break

            results['autocomplete'] = {'results': autocomplete_result, 'results_count': len(autocomplete_result), "parts": {"name": True, "website_url": True}}
            results['suggestions'] = {'results': suggestions_result, 'results_count': len(suggestions_result), "parts": {"name": True, "website_url": True}}

            global_match = False
            if matchs and len(matchs) == 1 and (results['autocomplete'].get('results_count') or results['suggestions'].get('results_count')):
                if matchs._name == 'product.public.category':
                    fixed_str = _('View all products with category')
                    global_match = {'name': f'{fixed_str} <b class="text-primary">{matchs.ds_name}</b>', 'website_url': f'/shop?category={matchs.id}'}
                else:
                    fixed_str = _('View all products with')
                    global_match = {'name': f'{fixed_str} {matchs.attribute_id.name.lower()} <b class="text-primary">{matchs.ds_name}</b>', 'website_url': f'/shop?&attrib={matchs.attribute_id.id}-{matchs.id}'}

        return {**results, 'fuzzy_search': fuzzy_term, 'results': [], 'global_match': global_match,
                'result_length': sum([results.get(r_type, {}).get('results_count', 0) for r_type in search_types]),
                }


