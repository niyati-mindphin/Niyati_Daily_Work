from odoo import http
from odoo.addons.web.controllers import main
from odoo.http import request
from odoo.addons.portal.controllers import portal, web
from odoo.tools import image_process
import werkzeug


class PortalWebHomeB2b(web.Home):
    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
            # request.env.user.partner_id.is_b2b_portal
            if not request.env.user._is_public() and request.website.is_b2b_website:
                return request.redirect_query('/b2b/dashbord', query=request.params)
            # return request.redirect_query('/my', query=request.params)
        return super(PortalWebHomeB2b, self).index(*args, **kw)

    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo().browse(uid).has_group('base.group_user'):
            homepage_id = request.website._get_cached('homepage_id')
            homepage = homepage_id and request.env['website.page'].sudo().browse(homepage_id)
            redirect = homepage.url
            if not request.env.user._is_public() and request.website.is_b2b_website:
                redirect = '/b2b/dashbord'
        return super(PortalWebHomeB2b, self)._login_redirect(uid, redirect=redirect)

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
            if request.env.user and not request.env.user._is_public() and request.website.is_b2b_website:
                return request.redirect_query('/b2b/dashbord', query=request.params)
            return request.redirect_query('/my', query=request.params)
        return super(PortalWebHomeB2b, self).web_client(s_action, **kw)

class CustomerPortal(portal.CustomerPortal):
    def _prepare_quotations_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sent', 'cancel'])
        ]

    def _prepare_orders_domain(self, partner):
        return [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done', 'delivered', 'complete'])
        ]

