from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time

class TrcfProcessingController(http.Controller):

    @http.route('/trcf_fnb_inventory/processing_list', type='http', auth='user', website=False)
    def processing_list(self, **kw):
        return request.render('trcf_fnb_inventory.processing_list_template')

    @http.route('/trcf_fnb_inventory/processing_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def processing_add(self, **kw):
        return request.render('trcf_fnb_inventory.processing_form_template')
