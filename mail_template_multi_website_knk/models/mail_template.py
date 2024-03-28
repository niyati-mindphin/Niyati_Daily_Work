# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    website_id = fields.Many2one('website', string="Website", help="Here We Select The Website Which Are Using To Send Mail.")
