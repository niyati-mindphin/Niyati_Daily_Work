# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    show_qrcode = fields.Boolean(string='Show QR-code', help='Show QR-code on the order confirmation page on the website')
