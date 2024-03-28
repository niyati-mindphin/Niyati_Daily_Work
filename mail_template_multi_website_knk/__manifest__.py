# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Mail Template Multi Website',
    'version': '15.0.1.0',
    'license': 'OPL-1',
    'summary': 'Mail Template Multi Website',
    'description': """Mail Template Multi Website send the mail from different website if website is true in mail template.
    """,
    'category': 'Productivity/Discuss',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'depends': ['account', 'auth_signup', 'sale', 'mail', 'website'],
    'data': [
        'data/mail_template_data.xml',
        'views/knk_mail_template_view.xml',
        'views/res_config_settings_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'price': 20,
    'currency': 'EUR'
}
