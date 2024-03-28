# -*- coding: utf-8 -*-
from odoo import fields, models


class OutputList(models.TransientModel):
    _name = 'output.list'
    _description = "Excel Output"

    name = fields.Char('Name', size=256)
    xls_output = fields.Binary('Excel output', readonly=True)
