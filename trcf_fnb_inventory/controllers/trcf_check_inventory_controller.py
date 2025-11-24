from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time

class TrcfCheckInventoryController(http.Controller):

    @http.route('/trcf_fnb_inventory/check_inventory_list', type='http', auth='user', website=False)
    def check_inventory_list(self, **kw):
        return request.render('trcf_fnb_inventory.check_inventory_list_template')

    @http.route('/trcf_fnb_inventory/check_inventory_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def check_inventory_add(self, **kw):
        return request.render('trcf_fnb_inventory.check_inventory_form_template')
