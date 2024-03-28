# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class UpdateContact(models.TransientModel):
    _name = "update.contact"
    _description = "Update Contact"

    @api.model
    def _get_default_fc_start_date(self):
        return fields.Date.today().replace(day=1, month=1)

    @api.model
    def _get_default_fc_end_date(self):
        return fields.Date.today().replace(day=31, month=12)

    fc_start_date = fields.Date("Start Date", default=_get_default_fc_start_date)
    fc_end_date = fields.Date("End Date", default=_get_default_fc_end_date)


    def action_confirm(self):
        partners = self.env['res.partner'].browse(self.env.context.get('active_ids'))
        partners.write({'fc_start_date': self.fc_start_date, 'fc_end_date': self.fc_end_date})
        for partner in partners:
            partner.action_customer_forecast()
