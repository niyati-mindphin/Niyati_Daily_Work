from odoo import conf, fields, http, SUPERUSER_ID, tools, _
import werkzeug
from odoo.http import request
# from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers

class DashboardPortalWeb(http.Controller):
    @http.route(['/my/statistics'], type='http', auth="user", website=True)
    def my_statistics(self, **post):
        if not request.env.user._is_public() and not request.website.is_b2b_website:
            raise werkzeug.exceptions.NotFound()
        return request.render("b2b_portal.dashboard_sharing_portal")

    @http.route("/my/statistics/board", type="http", auth="user", methods=['GET'])
    def render_dashboard_backend_view(self):
        return request.render(
            'b2b_portal.dashboard_sharing_embed',
            {'session_info': self._prepare_dashboard_sharing_session_info()},
        )

    def _prepare_dashboard_sharing_session_info(self):
        session_info = request.env['ir.http'].session_info()
        user_context = request.session.get_context() if request.session.uid else {}
        mods = conf.server_wide_modules or []
        # qweb_checksum = HomeStaticTemplateHelpers.get_qweb_templates_checksum(debug=request.session.debug, bundle="b2b_portal.assets_qweb")
        if request.env.lang:
            lang = request.env.lang
            session_info['user_context']['lang'] = lang
            # Update Cache
            user_context['lang'] = lang
        lang = user_context.get("lang")
        translation_hash = request.env['ir.translation'].get_web_translations_hash(mods, lang)
        cache_hashes = {
            # "qweb": qweb_checksum,
            "translations": translation_hash,

        }

        # project_company = project.company_id
        session_info.update(
            cache_hashes=cache_hashes,
            action_name='board.open_board_my_dash_action',
            user_companies={
                'current_company': request.env.user.company_id.id,
                'allowed_companies': {
                    request.env.user.company_id.id: {
                        'id': request.env.user.company_id.id,
                        'name': request.env.user.company_id.name,
                    },
                },
            },
            # FIXME: See if we prefer to give only the currency that the portal user just need to see the correct information in project sharing
            currencies=request.env['ir.http'].get_currencies(),
        )
        return session_info