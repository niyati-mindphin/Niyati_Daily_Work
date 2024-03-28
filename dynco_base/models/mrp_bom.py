# -*- coding: utf-8 -*-

from odoo import models, fields


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    sd_on_hand = fields.Html(related='product_id.curr_location', string="Available Stock")
