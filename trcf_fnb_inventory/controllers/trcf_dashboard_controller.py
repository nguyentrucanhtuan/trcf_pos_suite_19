from odoo import http
from odoo.http import request
from ..i18n import get_translator

class TrcfFNBDashboardController(http.Controller):

    @http.route('/trcf_fnb_inventory/dashboard',
                type='http', auth='user', website=False)
    def check_inventory_list(self, **kw):
        return request.render('trcf_fnb_inventory.trcf_dashboard_template', {'t': get_translator(request)})

    @http.route('/trcf_fnb_inventory/set_lang/<string:lang>',
                type='http', auth='user', website=False)
    def set_lang(self, lang, **kw):
        """Switch the current user's language (en_US / vi_VN) and bounce
        back to whichever TRCF page they were on. This is the same
        res.users.lang field Odoo's own Preferences page writes to, so it
        also affects native Odoo screens -- one toggle, not two."""
        allowed = {'en_US', 'vi_VN'}
        redirect_to = request.httprequest.referrer or '/trcf_fnb_inventory/dashboard'
        if lang not in allowed:
            return request.redirect(redirect_to)
        try:
            request.env.user.sudo().write({'lang': lang})
        except Exception:
            # e.g. vi_VN not yet installed under Settings > Translations > Languages
            pass
        return request.redirect(redirect_to)

