# -*- coding: utf-8 -*-

import werkzeug

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _handle_exception(cls, exception):
        response = super(IrHttp, cls)._handle_exception(exception)
        return response
