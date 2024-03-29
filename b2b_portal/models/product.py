# -*- coding: utf-8 -*-

import logging
from odoo import models, api
from odoo.osv import expression
from odoo.addons.website_sale_stock_wishlist.models.product_template import ProductTemplate
logger = logging.getLogger(__name__)


class CommanProductTemplate(models.Model):
    _inherit = [
        'rating.mixin',
        "product.template",
        "website.seo.metadata",
        'website.published.multi.mixin',
        'website.searchable.mixin',
    ]
    _name = 'product.template'

    @api.depends('is_published', 'website_id')
    @api.depends_context('website_id')
    def _compute_website_published(self):
        Flag = False
        current_website_id = self._context.get('website_id')
        if current_website_id:
            web_id = self.env['website'].sudo().browse(current_website_id)
            if web_id.is_b2b_website:
                Flag = True
                for record in self:
                    record.website_published = record.is_published
        if not Flag:
            for record in self:
                if current_website_id:
                    record.website_published = record.is_published and (not record.website_id or record.website_id.id == current_website_id)
                else:
                    record.website_published = record.is_published

    def _search_website_published(self, operator, value):
        if not isinstance(value, bool) or operator not in ('=', '!='):
            logger.warning('unsupported search on website_published: %s, %s', operator, value)
            return [()]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            value = not value

        current_website_id = self._context.get('website_id')
        is_published = [('is_published', '=', value)]
        if current_website_id:
            Flag = False
            web_id = self.env['website'].sudo().browse(current_website_id)
            if web_id.is_b2b_website:
                Flag = True
                return is_published
            if not Flag:
                on_current_website = self.env['website'].website_domain(current_website_id)
                return (['!'] if value is False else []) + expression.AND([is_published, on_current_website])
        else:  # should be in the backend, return things that are published anywhere
            return is_published

    def _get_combination_info(
        self, combination=False, product_id=False, add_qty=1.0,
        parent_combination=False, only_template=False,
    ):
    # def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        """Override for website, where we want to:
            - take the website pricelist if no pricelist is set
            - apply the b2b/b2c setting to the result

        This will work when adding website_id to the contextdef _get_combination_info(
        self, combination=False, product_id=False, add_qty=1.0,
        parent_combination=False, only_template=False,
    ):, which is done
        automatically when called from routes with website=True.
        """
        self.ensure_one()

        current_website = False

        if self.env.context.get('website_id'):
            current_website = self.env['website'].get_current_website()
            # if not pricelist:
            pricelist = current_website._get_current_pricelist()

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            parent_combination=parent_combination, only_template=only_template)

        if self.env.context.get('website_id'):
            if current_website and current_website.is_b2b_website:
                context = dict(self.env.context, ** {
                    'quantity': self.env.context.get('quantity', add_qty),
                    # 'pricelist': pricelist and pricelist.id
                })
                # pricelist = current_website._get_current_pricelist()

                product = (self.env['product.product'].browse(combination_info['product_id']) or self).with_context(context).sudo()
                partner = self.env.user.partner_id
                company_id = current_website.company_id

                tax_display = 'total_excluded'
                fpos = self.env['account.fiscal.position'].sudo()._get_fiscal_position(partner)
                product_taxes = product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id)
                taxes = fpos.map_tax(product_taxes)

                # The list_price is always the price of one.
                quantity_1 = 1
                combination_info['price'] = self.env['account.tax']._fix_tax_included_price_company(
                    combination_info['price'], product_taxes, taxes, company_id)

                # price = taxes.compute_all(combination_info['price'], pricelist.currency_id, product, partner)[tax_display]
                price = taxes.compute_all(combination_info['price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
                if pricelist.discount_policy == 'without_discount':
                    combination_info['list_price'] = self.env['account.tax']._fix_tax_included_price_company(
                        combination_info['list_price'], product_taxes, taxes, company_id)
                    list_price = taxes.compute_all(combination_info['list_price'], pricelist.currency_id, product, partner)[tax_display]
                else:
                    list_price = price
                combination_info['price_extra'] = self.env['account.tax']._fix_tax_included_price_company(combination_info['price_extra'], product_taxes, taxes, company_id)
                # price_extra = taxes.compute_all(combination_info['price_extra'], quantity_1, product, partner)[tax_display]
                price_extra = taxes.compute_all(combination_info['price_extra'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
                # has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1

                combination_info.update(
                    base_unit_name=product.base_unit_name,
                    base_unit_price=product.base_unit_price,
                    price=price,
                    list_price=list_price,
                    price_extra=price_extra,
                    # has_discounted_price=has_discounted_price,
                )
            # else:
            #     context = dict(self.env.context, ** {
            #         'quantity': self.env.context.get('quantity', add_qty),
            #         'pricelist': pricelist and pricelist.id
            #     })

            #     product = (self.env['product.product'].browse(combination_info['product_id']) or self).with_context(context).sudo()
            #     partner = self.env.user.partner_id
            #     company_id = current_website.company_id

            #     tax_display = self.user_has_groups('account.group_show_line_subtotals_tax_excluded') and 'total_excluded' or 'total_included'
            #     fpos = self.env['account.fiscal.position'].sudo()._get_fiscal_position(partner.id)
            #     product_taxes = product.sudo().taxes_id.filtered(lambda x: x.company_id == company_id)
            #     taxes = fpos.map_tax(product_taxes)

            #     # The list_price is always the price of one.
            #     quantity_1 = 1
            #     combination_info['price'] = self.env['account.tax']._fix_tax_included_price_company(
            #         combination_info['price'], product_taxes, taxes, company_id)
            #     price = taxes.compute_all(combination_info['price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            #     if pricelist.discount_policy == 'without_discount':
            #         combination_info['list_price'] = self.env['account.tax']._fix_tax_included_price_company(
            #             combination_info['list_price'], product_taxes, taxes, company_id)
            #         list_price = taxes.compute_all(combination_info['list_price'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            #     else:
            #         list_price = price
            #     combination_info['price_extra'] = self.env['account.tax']._fix_tax_included_price_company(combination_info['price_extra'], product_taxes, taxes, company_id)
            #     price_extra = taxes.compute_all(combination_info['price_extra'], pricelist.currency_id, quantity_1, product, partner)[tax_display]
            #     has_discounted_price = pricelist.currency_id.compare_amounts(list_price, price) == 1
            #     free_qty = product.with_context(warehouse=current_website._get_warehouse_available()).free_qty if combination_info['product_id'] else 0
            #     product_type = product.product_tmpl_id.type if combination_info['product_id'] else product.type

            #     combination_info.update(
            #         free_qty=free_qty,
            #         product_type=product_type,
            #         base_unit_name=product.base_unit_name,
            #         base_unit_price=product.base_unit_price,
            #         price=price,
            #         list_price=list_price,
            #         price_extra=price_extra,
            #         has_discounted_price=has_discounted_price,
            #     )

        return combination_info

ProductTemplate._get_combination_info = CommanProductTemplate._get_combination_info