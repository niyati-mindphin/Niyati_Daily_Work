# -*- coding: utf-8 -*-
# Powered by Mindphin Technologies.
# © 2023 Mindphin Technologies.

import logging

from odoo import _, models, fields
from odoo.exceptions import UserError
# from odoo.tools.float_utils import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)


class ScheduleDateWizard(models.TransientModel):
    _name = 'planned.date.wizard'

    schedule_date = fields.Datetime(string="Schedule Date")
    send_mail = fields.Boolean('Send Mail')

    def button_validate_picking(self):
        print("\n\n\ncontext...", self._context)
        print("\n\n\ncontext..A.", self.env.context)

        pickings_to_validate = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        print("\n\n\\t---> pickings_to_validate", pickings_to_validate)
        return pickings_to_validate.with_context(
            default_planned_date = self.schedule_date, is_mail_send=self.send_mail).button_validate()