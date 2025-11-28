from odoo import http
from odoo.http import request

class TrcfFNBDashboardController(http.Controller):

    @http.route('/trcf_fnb_inventory/dashboard', 
                type='http', auth='user', website=False)
    def check_inventory_list(self, **kw):
        return request.render('trcf_fnb_inventory.trcf_dashboard_template')

