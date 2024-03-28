# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class GetActiveLanguages(http.Controller):

    @http.route('/get_active_language', type='json', auth="user")
    def get_language(self):
        language = request.env['res.lang'].sudo().search(
            [('active', '=', True)])

        current_active = request.env.lang
        return {'current_active': current_active, "data": {r.code: {'id': [r.id], 'name': r.name, 'active': r.active, 'code': r.code, 'img_url': r.flag_image_url} for r in language}}

    @http.route('/set_language', type='json', auth="user")
    def set_language(self, **kw):

        user_id = request.env.uid
        temp = request.env['res.users'].sudo().browse(user_id)
        temp.sudo().write({'lang': kw['lang_id']})
        return True
