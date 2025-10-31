from odoo import http
from odoo.http import request

class VATInfoController(http.Controller):

    @http.route('/vat_info_form/<string:pos_reference>', type='http', auth='public', website=True)
    def vat_info_form(self, pos_reference=None, **kw):

        if not pos_reference:
            return request.render('trcf_minvoice.vat_info_error_template')

        order = request.env['pos.order'].sudo().search([('pos_reference', '=', pos_reference)], limit=1)
        
        if not order:
            return request.render('trcf_minvoice.vat_info_error_template')
        
        return request.render('trcf_minvoice.vat_info_form_template', {
            'pos_reference': order.pos_reference,
            'order_id': order.id,
        })

    @http.route('/vat_info_submit', type='http', auth='public', website=True, csrf=False)
    def vat_info_submit(self, **post):

        pos_reference = post.get('pos_reference')
        order = request.env['pos.order'].sudo().search([('pos_reference', '=', pos_reference)], limit=1)

        if order:
            vat_info = {
                'vat_type': post.get('vat_type'),
                'vat_email': post.get('vat_email'),
                'vat_tax_id': post.get('vat_tax_id'),
                'vat_customer_name': post.get('vat_customer_name'),
                'vat_company_name': post.get('vat_company_name'),
                'vat_address': post.get('vat_address'),
                'vat_phone': post.get('vat_phone'),
                'vat_citizen_id': post.get('vat_citizen_id'),
                'vat_note': post.get('vat_note'),
                'vat_account_number': post.get('vat_account_number'),
                'vat_bank_name': post.get('vat_bank_name'),
                'vat_estimated_unit_code': post.get('vat_estimated_unit_code'),
                'vat_passport_number': post.get('vat_passport_number'),
            }

            order.sudo().write(vat_info)
            # Có thể trả về trang xác nhận thành công
            return request.render('trcf_minvoice.vat_info_thanks_template')
        else:
            # Xử lý trường hợp không tìm thấy đơn hàng
            return request.render('trcf_minvoice.vat_info_error_template')