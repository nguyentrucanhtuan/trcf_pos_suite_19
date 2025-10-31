# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
import json

import logging
import pprint

# KHAI BÁO LOGGER Ở ĐÂY
_logger = logging.getLogger(__name__)

class TrcfMinvoicePosOrder(models.Model):
    _inherit = 'pos.order'
    
    trcf_reference_tax_code = fields.Char(
        string='Mã Đối Chiếu VAT',
        copy=False,
        help='Mã đối chiếu để xác minh VAT cho đơn hàng'
    )
    
    trcf_is_vat_sent= fields.Boolean(
        string='Đã xuất VAT',
        compute='_compute_trcf_is_vat_sent',
        store=True,
        help='Đơn hàng chưa có mã đối chiếu VAT'
    )
    
    @api.depends('trcf_reference_tax_code')
    def _compute_trcf_is_vat_sent(self):
        for order in self:
            order.trcf_is_vat_sent = bool(order.trcf_reference_tax_code)


    def action_send_vat_minvoice_api(self):

        minvoice_tax_code = self.env['ir.config_parameter'].sudo().get_param('trcf_minvoice.tax_code')
        minvoice_invoice_series = self.env['ir.config_parameter'].sudo().get_param('trcf_minvoice.invoice_series')
        minvoice_api_token = self.env['ir.config_parameter'].sudo().get_param('trcf_minvoice.api_token')
        minvoice_company_name = self.env['ir.config_parameter'].sudo().get_param('trcf_minvoice.company_name')

        # URL API
        if not minvoice_tax_code or not minvoice_invoice_series or not minvoice_api_token:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Cần điền thông tin VAT INVOICE',
                    'message': f'Cần điền thông tin VAT INVOICE mới được phát hành hoá đơn',
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        API_URL = f"https://{minvoice_tax_code}.minvoice.app/api/InvoiceApi78/Save"
                
        for order in self:
            # pprint.pprint(order.read())
            # pprint.pprint(order.lines.read())
            if order.vat_type == "company":
                inv_buyerEmail = order.vat_email
                inv_buyerTaxCode = order.vat_tax_id
                inv_buyerDisplayName = order.vat_customer_name
                inv_buyerLegalName =  order.vat_company_name
                inv_buyerAddressLine = order.vat_address
                #phone
                cccdan = order.vat_citizen_id
                #note
                inv_buyerBankAccount = order.vat_account_number
                inv_buyerBankName = order.vat_bank_name
                mdvqhnsach_nmua = order.vat_estimated_unit_code
                so_hchieu = order.vat_passport_number

            elif order.vat_type == "individual": 
                inv_buyerDisplayName = order.vat_customer_name
                inv_buyerLegalName =  "."
                inv_buyerTaxCode = ""
                inv_buyerAddressLine = order.vat_address
                inv_buyerEmail = order.vat_email
                #phone
                cccdan = order.vat_citizen_id
                #note
                inv_buyerBankAccount = order.vat_account_number
                inv_buyerBankName = order.vat_bank_name
                mdvqhnsach_nmua = order.vat_estimated_unit_code
                so_hchieu = order.vat_passport_number
                
            else:
                inv_buyerDisplayName = "khách không lấy hoá đơn"
                inv_buyerLegalName = "khách không lấy hoá đơn"
                inv_buyerTaxCode = ""
                inv_buyerAddressLine = "."
                inv_buyerEmail = ""
                inv_buyerBankAccount = "."
                inv_buyerBankName = "."
                cccdan = ""
                mdvqhnsach_nmua = ""
                so_hchieu = ""

            # --- Bắt đầu phần code mới để tạo dữ liệu chi tiết sản phẩm ---
            invoice_details = []
            stt = 1
            for line in order.lines:
                # Lấy thông tin từ order line
                invoice_details.append({
                    "tchat": 1,
                    "stt_rec0": stt,
                    "inv_itemCode": line.product_id.default_code or '',
                    "inv_itemName": line.full_product_name,
                    "inv_unitCode": line.product_uom_id.name,
                    "inv_quantity": line.qty,
                    "inv_unitPrice": line.price_unit,
                    "inv_discountPercentage": line.discount,
                    "inv_discountAmount": (line.price_unit * line.qty) * (line.discount / 100.0),
                    "inv_TotalAmountWithoutVat": line.price_subtotal,
                    "ma_thue": 8,
                    "inv_vatAmount": line.price_subtotal_incl - line.price_subtotal,
                    "inv_TotalAmount": line.price_subtotal_incl
                })
                stt += 1
            
            payload = {
                "editmode": 1,
                "data": [
                    {
                        "inv_invoiceSeries": minvoice_invoice_series,
                        "inv_invoiceIssuedDate": order.date_order.strftime('%Y-%m-%d'),
                        "inv_currencyCode": "VND",
                        "inv_exchangeRate": 1,
                        "so_benh_an": order.pos_reference,
                        "inv_buyerDisplayName": inv_buyerDisplayName or "",
                        "inv_buyerLegalName": inv_buyerLegalName or "",
                        "inv_buyerTaxCode": inv_buyerTaxCode,
                        "inv_buyerAddressLine": inv_buyerAddressLine or "", 
                        "inv_buyerEmail": inv_buyerEmail or "",
                        "inv_buyerBankAccount": inv_buyerBankAccount or "",
                        "inv_buyerBankName": inv_buyerBankName or "",
                        "inv_paymentMethodName": "TM/CK",
                        "inv_discountAmount": 0,
                        "inv_TotalAmountWithoutVat": order.amount_total - order.amount_tax,
                        "inv_vatAmount": order.amount_tax,
                        "inv_TotalAmount": order.amount_total,
                        "key_api": order.pos_reference,
                        "cccdan": cccdan or "",
                        "so_hchieu": so_hchieu or "",
                        "mdvqhnsach_nmua": mdvqhnsach_nmua ,
                        "ma_ch": "",
                        "ten_ch": minvoice_company_name or "",
                        "details": [
                            {
                                "data" : invoice_details
                            }
                        ]
                    }
                ]
            }

            try:
                # Headers
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {minvoice_api_token}'
                }
                
                response = requests.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                # Kiểm tra status code
                response.raise_for_status()

                # Parse JSON response
                result = response.json()

                if result.get('ok') and result.get('code') == '00':
                    # Lấy sobaomat từ data
                    data = result.get('data', {})
                    sobaomat = data.get('sobaomat')
                    order.write({
                        'trcf_reference_tax_code': sobaomat,
                        'trcf_is_vat_sent': True,
                    })

                # Parse response JSON
                try:
                    _logger.info(f"📥 Parsed JSON Response:")
                    _logger.info(json.dumps(result, indent=2, ensure_ascii=False))
                except:
                    _logger.warning("⚠️  Response không phải JSON")
                    result = None
                
            except requests.exceptions.HTTPError as e:
                _logger.error(f"❌ HTTP Error: {e}")
                _logger.error(f"Response: {response.text if 'response' in locals() else 'N/A'}")
                
            except requests.exceptions.ConnectionError as e:
                _logger.error(f"❌ Connection Error: {e}")
                
            except requests.exceptions.Timeout as e:
                _logger.error(f"❌ Timeout Error: {e}")
                
            except Exception as e:
                _logger.error(f"❌ Unexpected Error: {e}")
                _logger.exception("Chi tiết lỗi:")
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '✅ Thành công',
                'message': f'Đã gửi dữ liệu lên Minvoice!\nStatus: Check terminal log để xem chi tiết response.',
                'type': 'success',
                'sticky': False,
            }
        }