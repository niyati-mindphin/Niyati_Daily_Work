# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _send_confirmation_email(self):
        for stock_pick in self.filtered(lambda p: p.website_id.delivery_confirmation_mail_template and p.picking_type_id.code == 'outgoing'):
            delivery_template_id = stock_pick.website_id.delivery_confirmation_mail_template.id
            stock_pick.with_context(force_send=True).message_post_with_template(delivery_template_id, email_layout_xmlid='mail.mail_notification_light')
