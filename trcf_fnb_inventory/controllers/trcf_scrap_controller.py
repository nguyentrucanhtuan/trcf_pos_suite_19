from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time

class TrcfScrapController(http.Controller):

    @http.route('/trcf_fnb_inventory/scrap_list', type='http', auth='user', website=False)
    def scrap_list(self, **kw):
        return request.render('trcf_fnb_inventory.scrap_list_template')

    @http.route('/trcf_fnb_inventory/scrap_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def scrap_add(self, **kw):
        return request.render('trcf_fnb_inventory.scrap_form_template')
