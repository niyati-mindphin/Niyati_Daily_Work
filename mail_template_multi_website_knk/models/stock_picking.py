# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _send_confirmation_email(self):
        if self._context.get('is_mail_send'):
            for stock_pick in self.filtered(lambda p: p.website_id.delivery_confirmation_mail_template and p.picking_type_id.code == 'outgoing' or p.picking_type_id.code == 'incoming'):
                delivery_template_id = stock_pick.website_id.delivery_confirmation_mail_template.id
                stock_pick.with_context(force_send=True).message_post_with_template(delivery_template_id, email_layout_xmlid='mail.mail_notification_light')

    def set_planed_date(self):
        return {
            'name': 'Schedule Date',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'planned.date.wizard',
            'context': {'default_schedule_date': self.sale_id.schedule_date},
            'target': 'new',
        }

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self._context.get('default_planned_date'):
            self.write({'date_done': self._context.get('default_planned_date'),
                        'planned_date': self.sale_id.schedule_date})
        return res
