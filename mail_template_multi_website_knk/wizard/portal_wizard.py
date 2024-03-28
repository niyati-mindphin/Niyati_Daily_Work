# -*- coding: utf-8 -*-
# Powered by Mindphin Technologies.
# © 2023 Mindphin Technologies.

import logging

from odoo import _, models, fields
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_partner import now

_logger = logging.getLogger(__name__)


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    website_id = fields.Many2one('website', string="Website", related="partner_id.website_id")

    def _send_email(self):
        """ send notification email to a new portal user """
        self.ensure_one()

        # determine subject and body in the portal user's language
        template = self.env.ref('portal.mail_template_data_portal_welcome')
        if not template:
            raise UserError(_('The template "Portal: new user" not found for sending email to the portal user.'))

        lang = self.user_id.sudo().lang
        partner = self.user_id.sudo().partner_id

        portal_url = partner.with_context(signup_force_type_in_url='', lang=lang)._get_signup_url_for_action()[partner.id]
        partner.signup_prepare()
        if self.website_id and self.website_id.portal_access_mail_template:
            template = self.website_id.portal_access_mail_template
        template.with_context(dbname=self._cr.dbname, portal_url=portal_url, lang=lang).send_mail(self.id, force_send=True)

        return True
