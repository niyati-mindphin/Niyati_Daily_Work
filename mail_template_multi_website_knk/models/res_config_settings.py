# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    signup_mail_template = fields.Many2one('mail.template', string='Signup Email Template', related='website_id.signup_mail_template', readonly=False)
    reset_password_mail_template = fields.Many2one('mail.template', string='Reset Passsword Email Template', related='website_id.reset_password_mail_template', readonly=False)
    delivery_confirmation_mail_template = fields.Many2one('mail.template', string='Delivery Confirmation Email Template', related='website_id.delivery_confirmation_mail_template', readonly=False)
    sale_order_mail_template = fields.Many2one('mail.template', string='Sale Order Email Template', related='website_id.sale_order_mail_template', readonly=False)
    invoice_mail_template = fields.Many2one('mail.template', string='Invoice Email Template', related='website_id.invoice_mail_template', readonly=False)
    portal_access_mail_template = fields.Many2one('mail.template', string='Portal Access Email Template', related='website_id.portal_access_mail_template', readonly=False)
