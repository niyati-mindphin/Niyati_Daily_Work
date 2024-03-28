# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    signup_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'res.users')]", string='Signup Email Template')
    reset_password_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'res.users')]", string='Reset Password Email Template')
    delivery_confirmation_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'stock.picking')]", string='Delivery Confirmation Email Template')
    sale_order_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'sale.order')]", string='Sale Order Email Template')
    invoice_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'account.move')]", string='Invoice Email Template')
    portal_access_mail_template = fields.Many2one('mail.template', domain="[('model', '=', 'portal.wizard.user')]", string='Portal Access Email Template')
