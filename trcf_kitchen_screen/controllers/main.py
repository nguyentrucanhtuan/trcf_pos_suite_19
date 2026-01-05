from odoo import http
from odoo.http import request

class TrcfKitchenController(http.Controller):

    @http.route('/pos/kitchen_screen/<int:screen_id>', type='http', auth='user', website=True, allow_frames=True)
    def kitchen_screen_page(self, screen_id, **kwargs):
        """Trang hiển thị màn hình bếp trực tiếp cho Iframe"""
        # Logic này sẽ render template kitchen, OWL component sẽ tự load data qua RPC
        return request.render('trcf_kitchen_screen.kitchen_screen_iframe_template', {
            'screen_id': screen_id,
        })
