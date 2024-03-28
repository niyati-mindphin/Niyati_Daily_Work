# -*- coding: utf-8 -*-
from odoo import models, SUPERUSER_ID

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = super(SaleOrder, self)._find_mail_template(force_confirmation_template)
        if not self.website_id:
            return template_id

        if self.website_id:
            if self.website_id.sale_order_mail_template:
                template_id = self.website_id.sale_order_mail_template.id

        return template_id

    def action_quotation_send(self):
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if self.website_id:
            template = self.website_id.sale_order_mail_template
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for so in self:
            template_id = so._find_mail_template()
            lang = self.env.context.get('lang')
            template = self.env['mail.template'].browse(template_id)
            if so.website_id:
                template = so.website_id.sale_order_mail_template
            if template.lang:
                lang = template._render_lang(self.ids)[so.id]
            if template:
                so.with_user(SUPERUSER_ID).with_context(force_send=True, lang=lang).message_post_with_template(template.id, email_layout_xmlid='mail.mail_notification_light')
        return res
