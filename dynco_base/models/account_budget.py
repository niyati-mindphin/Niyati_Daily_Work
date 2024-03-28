# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    name = fields.Char(compute='_compute_line_name', store=True, readonly=False)
    date_from = fields.Date('Start Date', required=False)
    date_to = fields.Date('End Date', required=False)
    # planned_amount = fields.Monetary(compute='_compute_planned_amount',
    #     string='Planned Amount', required=True,
    #     help="Amount you plan to earn/spend. Record a positive amount if it is a revenue and a negative amount if it is a cost.")

    # @api.depends("general_budget_id", "general_budget_id.account_ids")
    # def _compute_planned_amount(self):
    #     for record in self:
    #         field_name = "target_%s" % record.date_from.year
    #         record.planned_amount = sum(record.general_budget_id.account_ids.mapped(field_name))