# -*- coding: utf-8 -*-

{
    "name": "B2B Portal",
    "category": "Tools",
    "author": "Kanak Infosystems LLP.",
    "summary": "B2B Portal",
    "version": "17.0.1.0",
    "license": "OPL-1",
    "description": """B2B Portal""",
    "depends": [
        "sale_stock",
        "delivery",
        "purchase",
        "website_sale",
        "website_sale_stock",
        "website_helpdesk",
        "dynco_base",
        "stock_dropshipping"
    ],
    "data": [
        # "data/ir_model_data.xml",
        # "data/mail_template.xml",
        # "data/base_automation.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/views.xml",
        "views/components.xml",
        "views/ir_ui_qweb_templates.xml",
        "views/b2bheader.xml",
        "views/dashboard.xml"
    ],
    'assets': {
        'web.assets_frontend': [
            'b2b_portal/static/src/scss/select2.min.css',
            'b2b_portal/static/src/scss/switchify.css',
            'b2b_portal/static/src/scss/stacktable.css',
            'b2b_portal/static/src/scss/style.scss',
            'b2b_portal/static/src/scss/responsive.scss',
            # # 'b2b_portal/static/src/js/stacktable.js', already commented
            'b2b_portal/static/src/lib/html5-qrcode.min.js',
            'b2b_portal/static/src/js/switchify.js',
            'b2b_portal/static/src/js/script.js',
            # 'b2b_portal/static/src/js/b2b_quick_view_dialog.js',
            # 'b2b_portal/static/src/js/select2.min.js',

        ],
        # 'b2b_portal.assets_qweb': [
        #     ('include', 'web.assets_qweb'),
        #     'b2b_portal/static/src/dashbord_sharing/dashbord_sharing.xml'
        # ],
        # 'b2b_portal.webclient': [
        #     ('include', 'web.assets_qweb'),
        #     ('include', 'web.assets_backend'),
        #     ('remove', 'web_enterprise/static/src/legacy/legacy_service_provider.js'),
        #     ('remove', 'web_studio/static/src/home_menu/**/*.js'),
        #     ('remove', 'web_enterprise/static/src/webclient/home_menu/*'),
        #     'b2b_portal/static/src/dashbord_sharing/*',
        #     'web/static/src/start.js',
        #     'web/static/src/legacy/legacy_setup.js',
        # ],
    },
    "installable": True,
}
