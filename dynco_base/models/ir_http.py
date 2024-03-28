from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):

    _inherit = "ir.http"

    def session_info(self):
        result = super(IrHttp, self).session_info()
        company = request.session.uid and request.env.user.company_id
        result.update(
            theme_has_background_image=bool(company and company.background_image)
        )
        return result
