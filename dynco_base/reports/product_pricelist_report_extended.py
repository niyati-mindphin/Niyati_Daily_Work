# -*- coding: utf-8 -*-

from odoo import api, models


class ProductPricelistReport(models.AbstractModel):
    _inherit= 'report.product.report_pricelist'

    def _get_report_data(self, data, report_type='html'):
        res = super(ProductPricelistReport, self)._get_report_data(data, report_type)
        res.update({'company_logo': self.env.user.company_id.logo,
            'tmp_company': self.env.user.company_id,
            'is_visible_description': data.get('is_visible_description', False) and bool(data['is_visible_description']),
            'is_visible_warehouse': data.get('is_visible_warehouse', False) and bool(data['is_visible_warehouse']),
            })
        return res

    def _get_product_data(self, is_product_tmpl, product, pricelist, quantities):
        data = super(ProductPricelistReport, self)._get_product_data(is_product_tmpl, product, pricelist, quantities)
        data.update({
            'default_code': product.default_code,
            'image': product.image_1920,
            'trade_unit': product.trade_unit_of_product,
            'description': product.product_variant_id.get_product_multiline_description_sale(),
            'curr_location': product.curr_location,
        })
        return data