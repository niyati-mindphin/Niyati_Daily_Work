# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Dynco Base',
    'version': '15.0.1.1',
    'summary': 'Dynco Base Module',
    'description': '''
        Dynco Base Module.
        1. This module defines new sequence for partner numbering.
        2. This module contains Product Customer Code features.
        3. This module allows to print invoices in xls format.
        4. This module shows Transfer(picking)names in tree of sale&purchase..
        5. This module shows partner's division name.
        6. This module some accounting groups to show/hide accounting menu's.
        7. This module contains separate main menu of product.
    ''',
    'category': 'Tools',
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'depends': [
        'theme_prime',  # for _get_combination_info
        'web_editor',
        'dynco_multi_website',
        'website',
        'base',
        'product',
        'sale_management',
        'stock',
        'account_budget',
        'account',
        'purchase',
        'survey',
        'l10n_ch',
        'account_asset',
        'website_mass_mailing',
        'knk_image_before_and_after',
        'website_product_addon',
        'droggol_theme_common',  # Added to use Product Brands in Forecasting in Partner.
        'company_public_holidays_kanak',  # Added to use For Delivery Day and percent in sale order.
        'account_bank_statement_import',  # Added to use For Account number validation.
        'website_helpdesk',
        'account_accountant',
        'website_product_multi_price',  # for _get_combination_info
        'website_sale_product_avail_country',  # for _get_combination_info
        'website_hr_recruitment',
        'portal',
        'stock'
    ],
    'external_dependencies': {
        'python': ['pyqrcode', 'pypng']
    },
    'data': [
        'data/ir_sequence.xml',
        'data/data.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'data/server_action_views.xml',
        'security/ir.model.access.csv',
        'security/base_security.xml',
        'wizard/move_xls_list_view.xml',
        'wizard/output.xml',
        'wizard/sale_delivery_lead_advance_view.xml',
        'wizard/update_contact_views.xml',
        'reports/reports.xml',
        'reports/report_saleorder.xml',
        'reports/sale_report_extended_views.xml',
        'reports/invoice_report_extended_views.xml',
        'reports/product_pricelist_report.xml',
        'reports/ds_streak_report.xml',
        'views/templates.xml',
        'views/climaqua_pages/climaqua_returns_page.xml',
        'views/climaqua_pages/cimaqua_payment_and_shipping_page.xml',
        'views/climaqua_pages/climaqua_agbs_page.xml',
        'views/climaqua_pages/climaqua_privacy_page.xml',
        'views/climaqua_pages/climaqua_faqs_page.xml',
        'views/climaqua_pages/climaqua_idea_page.xml',
        'views/climaqua_pages/climaqua_media_page.xml',
        'views/climaqua_pages/climaqua_project_page.xml',
        'views/climaqua_pages/climaqua_imprint_page.xml',
        'views/climaqua_pages/climaqua_about_us_page.xml',
        'views/lechuza_pages/lechuza_unternehmen_page.xml',
        'views/lechuza_pages/lechuza_umwelt_page.xml',
        'views/lechuza_pages/lechuza_presse_page.xml',
        'views/lechuza_pages/lechuza_faqs_page.xml',
        'views/lechuza_pages/lechuza_agb_page.xml',
        'views/lechuza_pages/lechuza_datenschutz_page.xml',
        'views/lechuza_pages/lechuza_downloads_page.xml',
        'views/lechuza_pages/lechuza_gesetzliche_hinweise_page.xml',
        'views/lechuza_pages/lechuza_hilfe_zum_onlineshop_page.xml',
        'views/lechuza_pages/lechuza_zahlung_und_versand_page.xml',
        'views/lechuza_pages/lechuza_impressum_page.xml',
        'views/custom_theme.xml',
        'views/base_views.xml',
        'views/website_climaqua.xml',
        'views/website_lechuza.xml',
        'views/website_templates.xml',
        'views/snippets.xml',
        'views/website_dynco.xml',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/sales_views.xml',
        'views/account_views.xml',
        'views/mrp_bom_view.xml',
        'views/stock_views.xml',
        'views/project_views.xml',
        'views/product_brand_lead_views.xml',
        'views/account_budget_views.xml',
        'views/dynco_pages/hersteller.xml',
        'views/dynco_pages/b2b.xml',
        'views/dynco_pages/b2c.xml',
        'views/dynco_pages/wir.xml',
        'views/dynco_pages/dynco_brands/climaqua.xml',
        'views/dynco_pages/dynco_brands/lechuza.xml',
        'views/dynco_pages/dynco_brands/ndt.xml',
        'views/dynco_pages/dynco_brands/keramik.xml',
        'views/dynco_pages/dynco_brands/fellhof.xml',
        'views/dynco_pages/dynco_brands/poetic.xml',
        'views/dynco_pages/dynco_brands/esteras.xml',
        'views/dynco_pages/dynco_brands/urbalive.xml',
        'views/dynco_pages/dynco_brands/pelletray.xml',
        'views/dynco_pages/dynco_brands/qflame.xml',
        'views/config_menu_access.xml',
        'views/website_pelletray.xml',
        'views/signup_extended_views.xml',
        'views/website_extended_views.xml',
        'views/portal_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_valuation_layer_views.xml',
        'wizard/add_discount_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'dynco_base/static/src/js/theme_bg.js',
            'dynco_base/static/src/js/button.js',
            'dynco_base/static/src/js/language_widget.js',
            'dynco_base/static/src/scss/sale_order_qrcode.scss',
            'dynco_base/static/src/scss/language_selector.scss',
            'dynco_base/static/src/js/productdescriptionwidget.js',

        ],
        'web._assets_common_styles': [
            'dynco_base/static/src/scss/navbar.scss',
        ],
        'web.assets_frontend': [
            #  In detail page After add to cart animation image was going wrong in cart so replaced this file website_sale_utils.js to override animateClone method
            ('replace', 'website_sale/static/src/js/website_sale_utils.js', 'dynco_base/static/src/js/utils.js'),
            'dynco_base/static/src/js/portal_chatter.js',
            'dynco_base/static/src/scss/as_custom.scss',
            'dynco_base/static/src/scss/lechuza_homepage.scss',
            'dynco_base/static/src/fonts/montblank-icons.css',
            'dynco_base/static/src/scss/climaque_custom.scss',
            'dynco_base/static/src/js/custom.js',
            'dynco_base/static/src/js/product_availability.js'
        ],
        'web.assets_qweb': [
            'dynco_base/static/src/xml/language_dropdown.xml',
            'dynco_base/static/src/xml/pricelist_report.xml',
            'dynco_base/static/src/xml/button.xml',
        ]
    },
}
